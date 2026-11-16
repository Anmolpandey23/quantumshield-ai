"""Command-line demo:  python -m stage2.demo"""
from .commands import CommandSigner, CommandVerifier
from .pipeline import secure_channel


def show(title: str, r: dict) -> None:
    print(f"\n=== {title} ===")
    for k in ("node_id", "status", "qber", "eavesdrop_detected", "key_generation_method",
              "key_gen_time_ms", "timings_ms", "sizes_bytes"):
        if k in r:
            print(f"  {k:24}: {r[k]}")


if __name__ == "__main__":
    show("Clean channel", secure_channel("192.168.1.14", seed=1))
    show("Eavesdropper on the line", secure_channel("192.168.1.14", eve_fraction=1.0, seed=2))
    print("\n=== Signed commands (for Stage 3) ===")
    signer = CommandSigner()
    verifier = CommandVerifier(signer.public_key)
    cmd = signer.sign("192.168.1.14", "isolate")
    print("  genuine command   :", verifier.verify(cmd))
    print("  replayed command  :", verifier.verify(cmd))
    forged = signer.sign("192.168.1.14", "isolate")
    forged["payload"]["action"] = "reconnect"
    print("  forged (edited)   :", verifier.verify(forged))
