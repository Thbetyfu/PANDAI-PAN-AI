from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Menjalankan benchmark internal PANDAI-EVAL terhadap model atau adapter."
    )
    parser.add_argument("--config", required=True, help="Path ke config evaluasi YAML.")
    parser.add_argument("--model", required=True, help="Nama model atau path adapter.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config_path = Path(args.config)

    print(f"[run_eval] config: {config_path}")
    print(f"[run_eval] model:  {args.model}")
    print("[run_eval] TODO: implement evaluator untuk subset PANDAI-EVAL.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
