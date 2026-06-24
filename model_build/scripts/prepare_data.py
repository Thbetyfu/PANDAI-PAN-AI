from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Menyiapkan dataset PANDAI Tutor dari sumber mentah ke format JSONL terstandar."
    )
    parser.add_argument("--input", required=True, help="Folder atau file sumber data mentah.")
    parser.add_argument("--output", required=True, help="File output JSONL hasil normalisasi.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    print(f"[prepare_data] input:  {input_path}")
    print(f"[prepare_data] output: {output_path}")
    print("[prepare_data] TODO: implement normalisasi data bilingual PANDAI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
