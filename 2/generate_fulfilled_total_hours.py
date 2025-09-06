#!/usr/bin/env python3

import pandas as pd
from typing import Dict, Tuple

EXCEL_PATH = "Y Volunteer Raw Data - Jan- August 2025.xlsx"
OUTPUT_CSV_PATH = "volunteer_fulfilled_total_hours.csv"


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def build_display_name(first_name: str, last_name: str, assignee: str) -> str:
    first_name = normalize_whitespace(first_name.strip()) if first_name else ""
    last_name = normalize_whitespace(last_name.strip()) if last_name else ""
    if first_name or last_name:
        return (first_name + " " + last_name).strip()

    assignee = normalize_whitespace(assignee.strip()) if assignee else ""
    if "," in assignee:
        parts = [p.strip() for p in assignee.split(",", 1)]
        if len(parts) == 2:
            return f"{parts[1]} {parts[0]}".strip()
    return assignee


def build_key(display_name: str) -> str:
    return normalize_whitespace(display_name).lower()


def generate_csv() -> None:
    df = pd.read_excel(EXCEL_PATH)

    fulfilled_series = pd.to_numeric(df.get("Fulfilled"), errors="coerce").fillna(0.0)
    first_names = df.get("First Name").fillna("").astype(str)
    last_names = df.get("Last Name").fillna("").astype(str)
    assignees = df.get("Assignee").fillna("").astype(str)

    totals_by_key: Dict[str, float] = {}
    display_name_by_key: Dict[str, str] = {}

    for first, last, assignee, fulfilled in zip(first_names, last_names, assignees, fulfilled_series):
        display_name = build_display_name(first, last, assignee)
        if not display_name:
            continue
        key = build_key(display_name)
        if key not in display_name_by_key:
            display_name_by_key[key] = display_name
        totals_by_key[key] = totals_by_key.get(key, 0.0) + float(fulfilled)

    out_df = pd.DataFrame(
        {
            "Full Name": [display_name_by_key[k] for k in totals_by_key.keys()],
            "Total Hours": [totals_by_key[k] for k in totals_by_key.keys()],
        }
    )

    out_df = out_df.sort_values(by=["Full Name"], kind="mergesort").reset_index(drop=True)
    out_df.to_csv(OUTPUT_CSV_PATH, index=False)


if __name__ == "__main__":
    generate_csv()
