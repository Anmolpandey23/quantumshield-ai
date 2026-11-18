"""Shared constants for Stage 1: feature lists, model registry definitions, label groups, human phrases."""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent
ARTIFACTS_DIR = ROOT / "artifacts"
MODELS_DIR = PROJECT_ROOT / "models" if (PROJECT_ROOT / "models").exists() else ROOT / "models"

# 52 flow features for LightGBM multiclass attack classification (CIC-IDS2017 schema)
LIGHTGBM_FEATURES = [
    "Destination Port",
    "Flow Duration",
    "Total Fwd Packets",
    "Total Length of Fwd Packets",
    "Fwd Packet Length Max",
    "Fwd Packet Length Min",
    "Fwd Packet Length Mean",
    "Fwd Packet Length Std",
    "Bwd Packet Length Max",
    "Bwd Packet Length Min",
    "Bwd Packet Length Mean",
    "Bwd Packet Length Std",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Flow IAT Min",
    "Fwd IAT Total",
    "Fwd IAT Mean",
    "Fwd IAT Std",
    "Fwd IAT Max",
    "Fwd IAT Min",
    "Bwd IAT Total",
    "Bwd IAT Mean",
    "Bwd IAT Std",
    "Bwd IAT Max",
    "Bwd IAT Min",
    "Fwd Header Length",
    "Bwd Header Length",
    "Fwd Packets/s",
    "Bwd Packets/s",
    "Min Packet Length",
    "Max Packet Length",
    "Packet Length Mean",
    "Packet Length Std",
    "Packet Length Variance",
    "FIN Flag Count",
    "PSH Flag Count",
    "ACK Flag Count",
    "Average Packet Size",
    "Subflow Fwd Bytes",
    "Init_Win_bytes_forward",
    "Init_Win_bytes_backward",
    "act_data_pkt_fwd",
    "min_seg_size_forward",
    "Active Mean",
    "Active Max",
    "Active Min",
    "Idle Mean",
    "Idle Max",
    "Idle Min",
]

# Backward compatibility alias
FEATURES = LIGHTGBM_FEATURES
N_FEATURES = len(FEATURES)

# 11 telemetry features for TabDDPM benign-distribution anomaly detection
TABDDPM_FEATURES = [
    "e2c_total_bytes",
    "e4_entropy_h",
    "e5_entropy_c",
    "e6_time_char",
    "e6b_flow_duration_ms",
    "e2_client_size",
    "e2_client_record_len",
    "e2_server_record_len",
    "e1_alg_suite_mlkem1024",
    "e1_alg_suite_mlkem768",
    "e1_alg_suite_x25519",
]
N_TABDDPM_FEATURES = len(TABDDPM_FEATURES)

# 7 multiclass attack categories
CLASS_NAMES = [
    "Normal Traffic",
    "DoS",
    "DDoS",
    "Port Scanning",
    "Brute Force",
    "Web Attacks",
    "Bots",
]
CLASS_TO_ID = {name: i for i, name in enumerate(CLASS_NAMES)}
ID_TO_CLASS = {i: name for i, name in enumerate(CLASS_NAMES)}

# TabDDPM configuration & threshold from manifest
TABDDPM_THRESHOLD = 0.56279456615448
TABDDPM_STEPS = 100
TABDDPM_HIDDEN = 128
TABDDPM_SCORE_TIMESTEPS = 8
TABDDPM_SCORE_SEED = 142

META_COLS = ["Source IP", "Destination IP", "Timestamp"]
BENIGN = "Normal Traffic"
BENIGN_ALIASES = {"BENIGN", "Normal Traffic", "Normal", "benign"}
MIN_CLASS_ROWS = 30

# What a person reads on the dashboard (phrase when feature is HIGH, phrase when LOW)
PHRASES: dict[str, tuple[str, str]] = {
    "Destination Port": ("traffic to unusual destination ports", "traffic to low/privileged ports"),
    "Flow Duration": ("unusually long connections", "unusually short connections"),
    "Total Fwd Packets": ("burst of outgoing packets", "very few outgoing packets"),
    "Total Length of Fwd Packets": ("large outgoing data volume", "tiny outgoing data volume"),
    "Fwd Packet Length Max": ("oversized outgoing packets", "tiny maximum packet size"),
    "Fwd Packet Length Min": ("unusually large minimum packet", "zero/tiny minimum packet"),
    "Fwd Packet Length Mean": ("large outgoing packet size", "tiny outgoing packet size"),
    "Fwd Packet Length Std": ("variable outgoing packet sizes", "uniform outgoing packet sizes"),
    "Bwd Packet Length Max": ("oversized reply packets", "tiny maximum reply packet"),
    "Bwd Packet Length Min": ("unusually large reply minimum", "zero/tiny minimum reply"),
    "Bwd Packet Length Mean": ("large incoming reply data", "tiny reply payload"),
    "Bwd Packet Length Std": ("variable reply packet sizes", "uniform reply packet sizes"),
    "Flow Bytes/s": ("unusual byte rate", "unusually low byte rate"),
    "Flow Packets/s": ("unusual packet rate", "unusually low packet rate"),
    "Flow IAT Mean": ("long gaps between packets", "packets arriving too fast (tiny gaps)"),
    "Flow IAT Std": ("irregular packet timing", "robot-like regular packet timing"),
    "Flow IAT Max": ("long connection idle pause", "no pauses in transmission"),
    "Flow IAT Min": ("continuous packet stream", "spaced packet timing"),
    "Fwd IAT Total": ("extended forward transmission time", "quick forward burst"),
    "Fwd IAT Mean": ("long gaps between outgoing packets", "outgoing packets transmitted too fast"),
    "Fwd IAT Std": ("irregular forward timing", "robotic forward pacing"),
    "Fwd IAT Max": ("long forward delay", "rapid consecutive forward packets"),
    "Fwd IAT Min": ("consecutive forward packets burst", "spaced forward delivery"),
    "Bwd IAT Total": ("extended reply stream time", "instantaneous replies"),
    "Bwd IAT Mean": ("long gaps between replies", "replies arriving too fast"),
    "Bwd IAT Std": ("irregular reply timing", "robotic reply pacing"),
    "Bwd IAT Max": ("long reply delay", "rapid consecutive replies"),
    "Bwd IAT Min": ("consecutive reply burst", "spaced reply delivery"),
    "Fwd Header Length": ("large outgoing headers", "tiny outgoing headers"),
    "Bwd Header Length": ("large reply headers", "tiny reply headers"),
    "Fwd Packets/s": ("unusual outgoing packet rate", "unusually low outgoing packet rate"),
    "Bwd Packets/s": ("unusual reply packet rate", "unusually low reply packet rate"),
    "Min Packet Length": ("unusually large smallest packet", "unusually tiny packets"),
    "Max Packet Length": ("unusually large biggest packet", "unusually small biggest packet"),
    "Packet Length Mean": ("unusual average packet size", "unusually small average packet size"),
    "Packet Length Std": ("irregular packet sizes", "identical packet sizes (scripted traffic)"),
    "Packet Length Variance": ("high packet length variance", "fixed packet sizes"),
    "FIN Flag Count": ("many connection closures (FIN)", "no FIN flags"),
    "PSH Flag Count": ("spike in PSH flag count", "no PSH flags"),
    "ACK Flag Count": ("unusual ACK count", "missing ACK flags (half-open connections)"),
    "Average Packet Size": ("unusual average packet size", "unusually small average packet size"),
    "Subflow Fwd Bytes": ("high forward subflow volume", "low forward subflow volume"),
    "Init_Win_bytes_forward": ("unusual TCP window (outgoing)", "unusual TCP window (outgoing)"),
    "Init_Win_bytes_backward": ("unusual TCP window (replies)", "unusual TCP window (replies)"),
    "act_data_pkt_fwd": ("many payload-bearing forward packets", "zero data packets in forward flow"),
    "min_seg_size_forward": ("unusual minimum segment size", "standard minimum segment size"),
    "Active Mean": ("long active periods", "very short active periods"),
    "Active Max": ("extended burst duration", "brief burst duration"),
    "Active Min": ("sustained active transmission", "intermittent active transmission"),
    "Idle Mean": ("long idle periods", "no idle time between bursts"),
    "Idle Max": ("extended inactivity period", "negligible inactivity"),
    "Idle Min": ("constant pause intervals", "uninterrupted flow"),
    # Telemetry phrases
    "e2c_total_bytes": ("unusual encrypted handshake byte volume", "minimal encrypted handshake bytes"),
    "e4_entropy_h": ("high handshake entropy", "low handshake entropy"),
    "e5_entropy_c": ("unusual ciphertext entropy", "standard ciphertext entropy"),
    "e6_time_char": ("unusual PQC timing characteristics", "typical PQC timing characteristics"),
    "e6b_flow_duration_ms": ("unusual PQC flow duration", "typical PQC flow duration"),
    "e2_client_size": ("abnormal client hello payload size", "standard client hello payload size"),
    "e2_client_record_len": ("abnormal client record length", "standard client record length"),
    "e2_server_record_len": ("abnormal server record length", "standard server record length"),
    "e1_alg_suite_mlkem1024": ("ML-KEM-1024 suite active", "non-ML-KEM-1024 negotiation"),
    "e1_alg_suite_mlkem768": ("ML-KEM-768 suite active", "non-ML-KEM-768 negotiation"),
    "e1_alg_suite_x25519": ("classical X25519 active", "post-quantum suite negotiation"),
}
