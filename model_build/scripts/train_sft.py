from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Menjalankan SFT/LoRA untuk eksperimen awal PANDAI-Tutor-7B."
    )
    parser.add_argument("--config", required=True, help="Path ke config YAML LoRA.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config_path = Path(args.config)

    print(f"[train_sft] config: {config_path}")
    print("[train_sft] TODO: implement trainer bootstrap untuk LoRA/QLoRA.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
