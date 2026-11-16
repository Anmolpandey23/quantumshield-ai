"""Shared constants for Stage 1: feature list, label groups, human-readable phrases."""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT / "artifacts"          # trained models land here (git-ignored)

# 34 CICFlowMeter features used by all three models (names exactly as in CIC-IDS2017 after .strip()).
FEATURES = [
    "Destination Port", "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
    "Total Length of Fwd Packets", "Total Length of Bwd Packets", "Fwd Packet Length Mean",
    "Bwd Packet Length Mean", "Flow Bytes/s", "Flow Packets/s", "Flow IAT Mean", "Flow IAT Std",
    "Fwd IAT Mean", "Bwd IAT Mean", "Fwd PSH Flags", "SYN Flag Count", "RST Flag Count",
    "ACK Flag Count", "PSH Flag Count", "URG Flag Count", "Fwd Header Length", "Bwd Header Length",
    "Fwd Packets/s", "Bwd Packets/s", "Min Packet Length", "Max Packet Length", "Packet Length Mean",
    "Packet Length Std", "Down/Up Ratio", "Average Packet Size", "Init_Win_bytes_forward",
    "Init_Win_bytes_backward", "Active Mean", "Idle Mean",
]
N_FEATURES = len(FEATURES)

META_COLS = ["Source IP", "Destination IP", "Timestamp"]   # needed for the graph and the sequences
BENIGN = "BENIGN"
MIN_CLASS_ROWS = 30            # classes with fewer rows are dropped (e.g. Heartbleed has 11 rows)

# What a person reads on the dashboard. (phrase when the feature is HIGH, phrase when LOW)
PHRASES: dict[str, tuple[str, str]] = {
    "Destination Port": ("traffic to unusual destination ports", "traffic to unusual destination ports"),
    "Flow Duration": ("unusually long connections", "unusually short connections"),
    "Total Fwd Packets": ("burst of outgoing packets", "very few outgoing packets"),
    "Total Backward Packets": ("many reply packets", "almost no reply packets"),
    "Total Length of Fwd Packets": ("large outgoing data volume", "tiny outgoing data volume"),
    "Total Length of Bwd Packets": ("large incoming data volume", "tiny incoming data volume"),
    "Fwd Packet Length Mean": ("large outgoing packets", "tiny outgoing packets"),
    "Bwd Packet Length Mean": ("large reply packets", "tiny reply packets"),
    "Flow Bytes/s": ("unusual byte rate", "unusually low byte rate"),
    "Flow Packets/s": ("unusual packet rate", "unusually low packet rate"),
    "Flow IAT Mean": ("long gaps between packets", "packets arriving too fast (tiny gaps)"),
    "Flow IAT Std": ("irregular packet timing", "robot-like regular packet timing"),
    "Fwd IAT Mean": ("long gaps between outgoing packets", "outgoing packets too fast"),
    "Bwd IAT Mean": ("long gaps between replies", "replies arriving too fast"),
    "Fwd PSH Flags": ("spike in PSH flag usage", "no PSH flags"),
    "SYN Flag Count": ("spike in SYN flag ratio", "no SYN flags"),
    "RST Flag Count": ("many connection resets (RST)", "no connection resets"),
    "ACK Flag Count": ("unusual ACK count", "missing ACK flags (half-open connections)"),
    "PSH Flag Count": ("spike in PSH flag count", "no PSH flags"),
    "URG Flag Count": ("urgent-flag usage", "no urgent flags"),
    "Fwd Header Length": ("large outgoing headers", "tiny outgoing headers"),
    "Bwd Header Length": ("large reply headers", "tiny reply headers"),
    "Fwd Packets/s": ("unusual outgoing packet rate", "unusually low outgoing packet rate"),
    "Bwd Packets/s": ("unusual reply packet rate", "unusually low reply packet rate"),
    "Min Packet Length": ("unusually large smallest packet", "unusually tiny packets"),
    "Max Packet Length": ("unusually large biggest packet", "unusually small biggest packet"),
    "Packet Length Mean": ("unusual average packet size", "unusually small average packet size"),
    "Packet Length Std": ("irregular packet sizes", "identical packet sizes (scripted traffic)"),
    "Down/Up Ratio": ("download-heavy flow", "upload-heavy flow"),
    "Average Packet Size": ("unusual average packet size", "unusually small average packet size"),
    "Init_Win_bytes_forward": ("unusual TCP window (outgoing)", "unusual TCP window (outgoing)"),
    "Init_Win_bytes_backward": ("unusual TCP window (replies)", "unusual TCP window (replies)"),
    "Active Mean": ("long active periods", "very short active periods"),
    "Idle Mean": ("long idle periods", "no idle time between bursts"),
}
