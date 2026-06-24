from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_FIELDS: dict[str, type] = {
    "id": str,
    "task_type": str,
    "language": str,
    "student_level": str,
    "persona": str,
    "difficulty": str,
    "curriculum_tag": str,
    "safety_label": str,
    "response_style": str,
    "system": str,
    "user": str,
    "assistant": str,
}

OPTIONAL_FIELDS: dict[str, type] = {
    "source_type": str,
    "source_name": str,
    "review_status": str,
    "reviewer_notes": str,
    "split_hint": str,
    "locale": str,
    "metadata": dict,
}

ALLOWED_VALUES: dict[str, set[str]] = {
    "task_type": {
        "instruction_tutor_bilingual",
        "grammar_correction",
        "teaching_explanation",
        "quiz_generation_structured",
        "student_feedback",
        "safe_refusal",
        "translation_reformulation",
    },
    "language": {"id", "en", "mixed"},
    "student_level": {"beginner", "elementary", "intermediate", "upper_intermediate"},
    "persona": {"strict_warm", "gentle_supportive", "concise_coach"},
    "difficulty": {"easy", "medium", "hard"},
    "safety_label": {"safe", "sensitive_but_allowed", "refusal_required"},
    "response_style": {"concise", "explanatory", "step_by_step", "structured_json", "encouraging"},
    "source_type": {"synthetic", "human_authored", "public_dataset"},
    "review_status": {"draft", "validated_schema", "reviewed_human", "approved", "rejected"},
    "split_hint": {"train", "validation", "test"},
}

SNAKE_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Memvalidasi dataset JSONL PANDAI Tutor sebelum training."
    )
    parser.add_argument("--dataset", required=True, help="Path ke file JSONL dataset.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Anggap field tak dikenal sebagai error, bukan warning.",
    )
    return parser


def is_control_string(value: str) -> bool:
    return any(ord(char) < 32 and char not in ("\n", "\r", "\t") for char in value)


def check_type(field_name: str, value: Any, expected_type: type) -> str | None:
    if not isinstance(value, expected_type):
        return (
            f"field '{field_name}' harus bertipe {expected_type.__name__}, "
            f"tetapi mendapat {type(value).__name__}"
        )
    return None


def check_string_field(field_name: str, value: str) -> list[str]:
    issues: list[str] = []
    if value.strip() == "":
        issues.append(f"field '{field_name}' tidak boleh string kosong")
    if is_control_string(value):
        issues.append(f"field '{field_name}' mengandung karakter kontrol yang tidak valid")
    return issues


def validate_allowed_values(field_name: str, value: str) -> str | None:
    allowed = ALLOWED_VALUES.get(field_name)
    if allowed and value not in allowed:
        return f"field '{field_name}' memiliki nilai tidak valid: {value!r}"
    return None


def validate_structured_json(record: dict[str, Any]) -> str | None:
    if record.get("response_style") != "structured_json":
        return None

    assistant_value = record.get("assistant")
    if not isinstance(assistant_value, str):
        return "field 'assistant' harus bertipe string untuk structured_json"

    try:
        json.loads(assistant_value)
    except json.JSONDecodeError as exc:
        return f"field 'assistant' harus valid JSON untuk structured_json: {exc.msg}"

    stripped = assistant_value.strip()
    if stripped.startswith("```") or stripped.endswith("```"):
        return "field 'assistant' untuk structured_json tidak boleh memakai markdown fence"

    return None


def validate_record(
    record: dict[str, Any],
    line_number: int,
    seen_ids: set[str],
    strict: bool,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(record, dict):
        return [f"baris {line_number}: objek root harus berupa JSON object"], warnings

    for key in record:
        if not SNAKE_CASE_PATTERN.match(key):
            errors.append(f"baris {line_number}: key '{key}' harus memakai snake_case")

    for field_name, expected_type in REQUIRED_FIELDS.items():
        if field_name not in record:
            errors.append(f"baris {line_number}: field wajib '{field_name}' tidak ditemukan")
            continue

        value = record[field_name]
        type_error = check_type(field_name, value, expected_type)
        if type_error:
            errors.append(f"baris {line_number}: {type_error}")
            continue

        if isinstance(value, str):
            for issue in check_string_field(field_name, value):
                errors.append(f"baris {line_number}: {issue}")

        allowed_error = validate_allowed_values(field_name, value) if isinstance(value, str) else None
        if allowed_error:
            errors.append(f"baris {line_number}: {allowed_error}")

    for field_name, expected_type in OPTIONAL_FIELDS.items():
        if field_name not in record:
            continue

        value = record[field_name]
        type_error = check_type(field_name, value, expected_type)
        if type_error:
            errors.append(f"baris {line_number}: {type_error}")
            continue

        if isinstance(value, str):
            for issue in check_string_field(field_name, value):
                warnings.append(f"baris {line_number}: {issue}")
            allowed_error = validate_allowed_values(field_name, value)
            if allowed_error:
                errors.append(f"baris {line_number}: {allowed_error}")

    known_fields = set(REQUIRED_FIELDS) | set(OPTIONAL_FIELDS)
    for key in record:
        if key in known_fields:
            continue
        message = f"baris {line_number}: field tak dikenal '{key}' ditemukan"
        if strict:
            errors.append(message)
        else:
            warnings.append(message)

    record_id = record.get("id")
    if isinstance(record_id, str) and record_id.strip():
        if record_id in seen_ids:
            errors.append(f"baris {line_number}: id duplikat '{record_id}' ditemukan")
        else:
            seen_ids.add(record_id)

    structured_json_error = validate_structured_json(record)
    if structured_json_error:
        errors.append(f"baris {line_number}: {structured_json_error}")

    return errors, warnings


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"[validate_data] dataset tidak ditemukan: {dataset_path}")
        return 2
    if dataset_path.suffix.lower() != ".jsonl":
        print(f"[validate_data] file harus berekstensi .jsonl: {dataset_path}")
        return 2

    print(f"[validate_data] dataset: {dataset_path}")
    seen_ids: set[str] = set()
    total_rows = 0
    all_errors: list[str] = []
    all_warnings: list[str] = []

    with dataset_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if raw_line.strip() == "":
                all_warnings.append(f"baris {line_number}: baris kosong dilewati")
                continue

            total_rows += 1

            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                all_errors.append(
                    f"baris {line_number}: JSON tidak valid ({exc.msg} pada kolom {exc.colno})"
                )
                continue

            record_errors, record_warnings = validate_record(
                record=record,
                line_number=line_number,
                seen_ids=seen_ids,
                strict=args.strict,
            )
            all_errors.extend(record_errors)
            all_warnings.extend(record_warnings)

    print(f"[validate_data] total baris diproses: {total_rows}")
    print(f"[validate_data] total error: {len(all_errors)}")
    print(f"[validate_data] total warning: {len(all_warnings)}")

    if all_errors:
        print("[validate_data] daftar error:")
        for error in all_errors:
            print(f"  - {error}")

    if all_warnings:
        print("[validate_data] daftar warning:")
        for warning in all_warnings:
            print(f"  - {warning}")

    if all_errors:
        return 1

    print("[validate_data] dataset valid terhadap spesifikasi dasar PANDAI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
