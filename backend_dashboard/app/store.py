"""Tiny SQLite event log. Every pipeline event is stored once; the dashboard reads it back."""
from __future__ import annotations

import json
import os
import sqlite3
import threading


class Store:
    def __init__(self, path: str):
        if path != ":memory:":
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        with self.lock:
            self.db.execute("""CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, node_id TEXT, decision TEXT, label TEXT, risk REAL,
                s2_status TEXT, qber REAL, keygen_ms REAL, action TEXT, verified INTEGER, body TEXT)""")
            self.db.execute("CREATE INDEX IF NOT EXISTS ix_events_node ON events(node_id)")
            self.db.commit()

    def add(self, e: dict) -> int:
        s2, cmd = e.get("stage2") or {}, e.get("stage3_command")
        with self.lock:
            cur = self.db.execute(
                "INSERT INTO events (ts,node_id,decision,label,risk,s2_status,qber,keygen_ms,action,verified,body) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (e["timestamp"], e["node_id"], e["decision"], e["stage1"]["threat_label"], e["stage1"]["risk_score_node"],
                 s2.get("status"), s2.get("qber"), s2.get("key_gen_time_ms"),
                 cmd["payload"]["action"] if cmd else None,
                 None if e["command_verified"] is None else int(e["command_verified"]), json.dumps(e)))
            self.db.commit()
            return int(cur.lastrowid)

    def recent(self, limit: int = 50, node_id: str | None = None, decision: str | None = None) -> list[dict]:
        q, args = "SELECT id, body FROM events WHERE 1=1", []
        if node_id:
            q += " AND node_id=?"; args.append(node_id)
        if decision:
            q += " AND decision=?"; args.append(decision)
        q += " ORDER BY id DESC LIMIT ?"; args.append(min(max(limit, 1), 1000))
        with self.lock:
            rows = self.db.execute(q, args).fetchall()
        return [{**json.loads(r["body"]), "id": r["id"]} for r in rows]

    def keys(self, limit: int = 50) -> list[dict]:
        with self.lock:
            rows = self.db.execute("SELECT id, ts, node_id, s2_status, qber, keygen_ms, body FROM events WHERE s2_status IS NOT NULL "
                                   "ORDER BY id DESC LIMIT ?", (min(max(limit, 1), 1000),)).fetchall()
        out = []
        for r in rows:
            s2 = json.loads(r["body"])["stage2"]
            out.append({"id": r["id"], "timestamp": r["ts"], "node_id": r["node_id"], "status": r["s2_status"], "qber": r["qber"],
                        "key_gen_time_ms": r["keygen_ms"], "eavesdrop_detected": s2["eavesdrop_detected"],
                        "shared_key_id": s2.get("shared_key_id"), "method": s2.get("key_generation_method"),
                        "timings_ms": s2.get("timings_ms")})
        return out

    def stats(self) -> dict:
        with self.lock:
            q = lambda sql, *a: self.db.execute(sql, a).fetchone()[0]
            return {
                "events_total": q("SELECT COUNT(*) FROM events"),
                "threats_flagged": q("SELECT COUNT(*) FROM events WHERE s2_status IS NOT NULL"),
                "key_exchanges_ok": q("SELECT COUNT(*) FROM events WHERE s2_status='secure_channel_established'"),
                "eavesdrop_aborts": q("SELECT COUNT(*) FROM events WHERE s2_status='aborted_eavesdrop_detected'"),
                "isolations": q("SELECT COUNT(*) FROM events WHERE action='isolate' AND verified=1"),
                "reconnections": q("SELECT COUNT(*) FROM events WHERE action='reconnect' AND verified=1"),
                "commands_rejected": q("SELECT COUNT(*) FROM events WHERE decision='command_rejected'"),
                "avg_key_gen_ms": round(q("SELECT COALESCE(AVG(keygen_ms),0) FROM events WHERE s2_status='secure_channel_established'"), 1),
                "avg_qber_clean": round(q("SELECT COALESCE(AVG(qber),0) FROM events WHERE s2_status='secure_channel_established'"), 4),
                "avg_qber_eve": round(q("SELECT COALESCE(AVG(qber),0) FROM events WHERE s2_status='aborted_eavesdrop_detected'"), 4),
            }

    def threat_breakdown(self) -> dict[str, int]:
        with self.lock:
            rows = self.db.execute("SELECT label, COUNT(*) c FROM events WHERE label!='BENIGN' GROUP BY label").fetchall()
        return {r["label"]: r["c"] for r in rows}

    def clear(self) -> None:
        with self.lock:
            self.db.execute("DELETE FROM events"); self.db.commit()
