from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mengekspor adapter/checkpoint agar siap untuk pipeline deployment."
    )
    parser.add_argument("--input", required=True, help="Folder checkpoint atau adapter.")
    parser.add_argument("--output", required=True, help="Folder output artefak export.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    print(f"[export_adapter] input:  {input_path}")
    print(f"[export_adapter] output: {output_path}")
    print("[export_adapter] TODO: implement export ke format deployment target.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
