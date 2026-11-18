"""ThreatPredictor: TabDDPM Anomaly Detection + LightGBM Multiclass Classification.

Adheres to:
    - contracts/inference_schema.json (TabDDPM & LightGBM inference contract)
    - contracts/stage1_output.schema.json (QuantumShield Stage 1 contract)
    - models/quantumshield_model_registry.json
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import pathlib
from typing import Any, Iterable
import uuid

import numpy as np
import pandas as pd

from .classifier import FlowClassifier
from .config import (
    ARTIFACTS_DIR,
    BENIGN,
    CLASS_NAMES,
    CLASS_TO_ID,
    ID_TO_CLASS,
    LIGHTGBM_FEATURES,
    MODELS_DIR,
    PROJECT_ROOT,
    ROOT,
    TABDDPM_FEATURES,
    TABDDPM_THRESHOLD,
)
from .explain import format_explanation_phrases
from .tabddpm import TabDDPM, TabDDPMPreprocessor

CONTRACT_VERSION = "1.0"
SCHEMA_VERSION = "1.0"


class ThreatPredictor:
    """Fuses TabDDPM (benign anomaly detection) and LightGBM (attack classification)."""

    def __init__(
        self,
        classifier: FlowClassifier,
        tabddpm: TabDDPM,
        tabddpm_prep: TabDDPMPreprocessor,
        cfg: dict[str, Any] | None = None,
        device: str = "cpu",
    ):
        self.clf = classifier
        self.tabddpm = tabddpm
        self.tabddpm_prep = tabddpm_prep
        self.cfg = cfg or {}
        self.device = device
        self.buffer = pd.DataFrame()

    # ------------------------------------------------------------------ io
    @classmethod
    def load(
        cls,
        path: str | pathlib.Path | None = None,
        registry_path: str | pathlib.Path | None = None,
        device: str = "cpu",
    ) -> "ThreatPredictor":
        """Load trained models from directory or quantumshield_model_registry.json."""
        base_paths = []
        if path:
            base_paths.append(pathlib.Path(path))
        if registry_path:
            base_paths.append(pathlib.Path(registry_path).parent)
        base_paths.extend([MODELS_DIR, ROOT / "models", ARTIFACTS_DIR, PROJECT_ROOT / "models", PROJECT_ROOT])

        reg_file = None
        for b in base_paths:
            candidate = b / "quantumshield_model_registry.json"
            if candidate.exists():
                reg_file = candidate
                break

        # Discover TabDDPM artifact paths
        tabddpm_pt = None
        tabddpm_prep_file = None
        lgb_model = None
        lgb_bundle = None

        if reg_file and reg_file.exists():
            try:
                reg_data = json.loads(reg_file.read_text())
                models_info = reg_data.get("models", {})
                anom_info = models_info.get("anomaly_detector", {})
                att_info = models_info.get("attack_classifier", {})

                # Resolve relative to registry file location or repo root
                search_roots = [reg_file.parent, PROJECT_ROOT, ROOT]
                for sr in search_roots:
                    c_pt = sr / anom_info.get("model_artifact", "")
                    if c_pt.exists() and not tabddpm_pt:
                        tabddpm_pt = c_pt
                    c_txt = sr / att_info.get("model_artifact", "")
                    if c_txt.exists() and not lgb_model:
                        lgb_model = c_txt
            except Exception:
                pass

        # Fallback discovery
        for b in base_paths:
            for pt in [b / "tabddpm/improved/tabddpm_improved.pt", b / "tabddpm.pt", b / "tabddpm_improved.pt"]:
                if pt.exists() and not tabddpm_pt:
                    tabddpm_pt = pt
            for prep in [b / "tabddpm/improved/preprocessing_improved.joblib", b / "preprocessing_improved.joblib", b / "tabddpm_prep.joblib"]:
                if prep.exists() and not tabddpm_prep_file:
                    tabddpm_prep_file = prep
            for lgb_txt in [b / "cicids_classifier/lightgbm_multiclass.txt", b / "lightgbm_multiclass.txt", b / "classifier.txt"]:
                if lgb_txt.exists() and not lgb_model:
                    lgb_model = lgb_txt
            for bun in [b / "cicids_classifier/cicids_lightgbm_bundle.joblib", b / "cicids_lightgbm_bundle.joblib", b / "classifier_bundle.joblib"]:
                if bun.exists() and not lgb_bundle:
                    lgb_bundle = bun

        if not lgb_model and not lgb_bundle:
            raise FileNotFoundError(
                f"No LightGBM model found in {base_paths}. Train models using: python -m stage1.train"
            )
        if not tabddpm_pt:
            raise FileNotFoundError(
                f"No TabDDPM model found in {base_paths}. Train models using: python -m stage1.train"
            )

        clf = FlowClassifier.load(native_model_path=lgb_model, joblib_bundle_path=lgb_bundle)
        tabddpm = TabDDPM.load(tabddpm_pt, device=device)
        if tabddpm_prep_file and tabddpm_prep_file.exists():
            tabddpm_prep = TabDDPMPreprocessor.load(tabddpm_prep_file)
        else:
            tabddpm_prep = TabDDPMPreprocessor()

        cfg_file = None
        for b in base_paths:
            if (b / "config.json").exists():
                cfg_file = b / "config.json"
                break
        cfg = json.loads(cfg_file.read_text()) if cfg_file else {}
        return cls(classifier=clf, tabddpm=tabddpm, tabddpm_prep=tabddpm_prep, cfg=cfg, device=device)

    # ------------------------------------------------------------------ streaming window
    def ingest(self, flows: pd.DataFrame) -> None:
        """Add new flows. Old flows older than buffer_minutes fall out."""
        flows = flows.copy()
        if "Timestamp" in flows.columns:
            flows["Timestamp"] = pd.to_datetime(flows["Timestamp"])
        self.buffer = pd.concat([self.buffer, flows], ignore_index=True) if len(self.buffer) else flows
        if "Timestamp" in self.buffer.columns and len(self.buffer):
            horizon = pd.Timedelta(minutes=self.cfg.get("buffer_minutes", 15))
            max_t = self.buffer["Timestamp"].max()
            self.buffer = self.buffer[self.buffer["Timestamp"] >= max_t - horizon].reset_index(drop=True)

    # ------------------------------------------------------------------ prediction
    def predict(self, node_id: str) -> dict[str, Any]:
        """Perform inference on node_id satisfying both inference_schema and stage1_output."""
        rows = self.buffer[self.buffer["Source IP"] == node_id] if len(self.buffer) and "Source IP" in self.buffer.columns else self.buffer
        now_iso = datetime.now(timezone.utc).isoformat()
        evt_id = f"evt_{uuid.uuid4().hex[:12]}"

        if rows.empty:
            return self._build_response(
                event_id=evt_id,
                timestamp_utc=now_iso,
                node_id=node_id,
                threat_label=BENIGN,
                confidence=0.99,
                anomaly_score=0.01,
                threshold=self.tabddpm.threshold,
                is_anomaly=False,
                predicted_class="Normal Traffic",
                predicted_class_id=0,
                class_probabilities={c: (0.99 if c == "Normal Traffic" else 0.001) for c in CLASS_NAMES},
                top_contributing_features=[],
                explanation_reasons=["no recent traffic from this host"],
                risk_level="low",
                risk_score_node=0.01,
                recommended_action="none",
                execution_status="simulated",
            )

        recent = rows.tail(40)

        # 1. Multiclass Classification with LightGBM
        probs_all = self.clf.predict_proba(recent)
        mean_probs = probs_all.mean(axis=0)
        best_cid = int(mean_probs.argmax())
        lgb_class = CLASS_NAMES[best_cid]
        conf = float(mean_probs[best_cid])
        class_probs = {c: float(mean_probs[i]) for i, c in enumerate(CLASS_NAMES)}

        # 2. Benign-distribution Anomaly Detection with TabDDPM
        x_tab = self.tabddpm_prep.transform(recent) if self.tabddpm_prep.fitted else TabDDPMPreprocessor.extract_tabddpm_features(recent)
        anom_scores = self.tabddpm.score(x_tab)
        anom_score = float(anom_scores.mean()) if len(anom_scores) else 0.0
        threshold = float(self.tabddpm.threshold)
        is_anomaly = bool(anom_score >= threshold)

        # 3. Explainability with SHAP TreeExplainer
        explanations = self.clf.explain(recent.tail(5), k=3)
        top_features = explanations[-1]["top_contributing_features"] if explanations else []
        reasons = format_explanation_phrases(top_features)

        # 4. Risk Assessment & Operational Response
        is_attack = (lgb_class != "Normal Traffic")
        if is_attack and is_anomaly:
            threat_label = lgb_class
            risk_score_node = float(np.clip(0.55 * conf + 0.45 * (anom_score / max(threshold, 0.1)), 0.6, 0.99))
            risk_level = "critical" if risk_score_node >= 0.8 else "high"
            recommended_action = "isolate"
            status = "pending_approval"
        elif is_attack and not is_anomaly:
            threat_label = lgb_class
            risk_score_node = float(np.clip(0.65 * conf + 0.15, 0.4, 0.85))
            risk_level = "medium"
            recommended_action = "monitor"
            status = "simulated"
        elif not is_attack and is_anomaly:
            # Anomaly detected that doesn't match known attack classes (Zero-Day / Novel threat)
            threat_label = "ANOMALY_UNKNOWN"
            risk_score_node = float(np.clip(0.6 * (anom_score / max(threshold, 0.1)), 0.5, 0.9))
            risk_level = "high"
            recommended_action = "monitor"
            status = "pending_approval"
            if "behaviour deviates strongly from learned normal pattern" not in reasons:
                reasons.insert(0, "behaviour deviates strongly from learned normal pattern")
        else:
            threat_label = BENIGN
            risk_score_node = float(np.clip(0.05 * (1.0 - conf) + 0.05 * (anom_score / max(threshold, 0.1)), 0.0, 0.15))
            risk_level = "low"
            recommended_action = "none"
            status = "executed"

        return self._build_response(
            event_id=evt_id,
            timestamp_utc=now_iso,
            node_id=node_id,
            threat_label=threat_label,
            confidence=conf,
            anomaly_score=anom_score,
            threshold=threshold,
            is_anomaly=is_anomaly,
            predicted_class=lgb_class,
            predicted_class_id=best_cid,
            class_probabilities=class_probs,
            top_contributing_features=top_features,
            explanation_reasons=reasons,
            risk_level=risk_level,
            risk_score_node=risk_score_node,
            recommended_action=recommended_action,
            execution_status=status,
        )

    def predict_all(self, nodes: Iterable[str] | None = None) -> list[dict[str, Any]]:
        if nodes is not None:
            node_list = list(nodes)
        elif len(self.buffer) and "Source IP" in self.buffer.columns:
            node_list = list(self.buffer["Source IP"].unique())
        else:
            node_list = []
        return [self.predict(n) for n in node_list]

    @staticmethod
    def _build_response(
        event_id: str,
        timestamp_utc: str,
        node_id: str,
        threat_label: str,
        confidence: float,
        anomaly_score: float,
        threshold: float,
        is_anomaly: bool,
        predicted_class: str,
        predicted_class_id: int,
        class_probabilities: dict[str, float],
        top_contributing_features: list[dict[str, Any]],
        explanation_reasons: list[str],
        risk_level: str,
        risk_score_node: float,
        recommended_action: str,
        execution_status: str,
    ) -> dict[str, Any]:
        """Construct response satisfying both stage1_output and inference_schema."""
        r = lambda v: round(float(np.clip(v, 0.0, 1.0)), 4)
        return {
            # --- Stage 1 Contract Fields (contracts/stage1_output.schema.json) ---
            "contract_version": CONTRACT_VERSION,
            "node_id": node_id,
            "threat_label": threat_label,
            "confidence": r(confidence),
            "anomaly_score": r(anomaly_score),
            "risk_score_node": r(risk_score_node),
            "explanation": explanation_reasons[:4],

            # --- Common TabDDPM & LightGBM Inference Contract (contracts/inference_schema.json) ---
            "schema_version": SCHEMA_VERSION,
            "event_id": event_id,
            "timestamp_utc": timestamp_utc,
            "tabddpm": {
                "anomaly_score": round(float(anomaly_score), 5),
                "threshold": round(float(threshold), 5),
                "is_anomaly": bool(is_anomaly),
            },
            "lightgbm": {
                "predicted_class": predicted_class,
                "predicted_class_id": int(predicted_class_id),
                "class_probabilities": {k: round(float(v), 5) for k, v in class_probabilities.items()},
            },
            "explainability": {
                "method": "shap.TreeExplainer",
                "top_contributing_features": top_contributing_features,
                "explanation_reference": "results/cicids_classifier/shap/shap_experiment_metadata.json",
            },
            "risk_assessment": {
                "risk_level": risk_level,
                "policy_version": "1.0",
            },
            "response": {
                "recommended_action": recommended_action,
                "execution_status": execution_status,
            },
        }
