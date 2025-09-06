from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


DATA_PATH = Path(__file__).resolve().parent.parent / "Y_Volunteer_Raw_Data_Jan_August_2025.csv"


class VolunteerAggregate(BaseModel):
    contact_id: Optional[int]
    first_name: str
    last_name: str
    email: Optional[str]
    hours_total: float
    assignments_count: int
    first_activity: Optional[str]
    last_activity: Optional[str]
    milestones: List[str]


MILESTONES = [
    (10, "First Impact"),
    (25, "Service Star"),
    (50, "Commitment Champion"),
    (100, "Passion In Action Award"),
    (500, "Guiding Light Award"),
]


def load_dataframe(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found at {csv_path}")
    df = pd.read_csv(csv_path)
    # Normalize columns we rely on
    expected_columns = {
        "Date",
        "First Name",
        "Last Name",
        "Email",
        "Contact ID",
        "Hours",
    }
    missing = expected_columns - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")
    # Types
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Hours"] = pd.to_numeric(df["Hours"], errors="coerce").fillna(0.0)
    # Clean names and ids
    if "Contact ID" in df:
        df["Contact ID"] = pd.to_numeric(df["Contact ID"], errors="coerce").astype("Int64")
    # Strip whitespace in names
    df["First Name"] = df["First Name"].fillna("").astype(str).str.strip()
    df["Last Name"] = df["Last Name"].fillna("").astype(str).str.strip()
    if "Email" in df:
        df["Email"] = df["Email"].fillna("").astype(str).str.strip().str.lower()
    return df


def filter_date_range(df: pd.DataFrame, start: Optional[str], end: Optional[str]) -> pd.DataFrame:
    if start:
        start_dt = pd.to_datetime(start, errors="coerce")
        if pd.isna(start_dt):
            raise ValueError("Invalid start date")
        df = df[df["Date"] >= start_dt]
    if end:
        end_dt = pd.to_datetime(end, errors="coerce")
        if pd.isna(end_dt):
            raise ValueError("Invalid end date")
        df = df[df["Date"] <= end_dt]
    return df


def compute_milestones(total_hours: float) -> List[str]:
    unlocked: List[str] = []
    for threshold, label in MILESTONES:
        if total_hours >= threshold:
            unlocked.append(label)
    return unlocked


def aggregate_by_volunteer(df: pd.DataFrame) -> List[VolunteerAggregate]:
    grouped = df.groupby(["Contact ID", "First Name", "Last Name", "Email"], dropna=False)
    results: List[VolunteerAggregate] = []
    for (contact_id, first_name, last_name, email), g in grouped:
        hours_total = float(g["Hours"].sum())
        first_activity = None
        last_activity = None
        if not g["Date"].isna().all():
            first_dt = g["Date"].min()
            last_dt = g["Date"].max()
            first_activity = first_dt.strftime("%Y-%m-%d") if pd.notna(first_dt) else None
            last_activity = last_dt.strftime("%Y-%m-%d") if pd.notna(last_dt) else None

        results.append(
            VolunteerAggregate(
                contact_id=int(contact_id) if pd.notna(contact_id) else None,
                first_name=first_name or "",
                last_name=last_name or "",
                email=email or None,
                hours_total=round(hours_total, 2),
                assignments_count=int(len(g)),
                first_activity=first_activity,
                last_activity=last_activity,
                milestones=compute_milestones(hours_total),
            )
        )
    # Sort by total hours desc
    results.sort(key=lambda r: r.hours_total, reverse=True)
    return results


app = FastAPI(title="Volunteer Hours Milestone Tracker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/volunteers", response_model=List[VolunteerAggregate])
def list_volunteers(
    start: Optional[str] = Query(None, description="Start date YYYY-MM-DD (>=)"),
    end: Optional[str] = Query(None, description="End date YYYY-MM-DD (<=)"),
):
    try:
        df = load_dataframe(DATA_PATH)
        df = filter_date_range(df, start, end)
        # default filter: data from 2024-01-01 onward if no dates provided
        if not start and not end:
            df = filter_date_range(df, "2024-01-01", None)
        agg = aggregate_by_volunteer(df)
        return agg
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


class AchievementSummary(BaseModel):
    label: str
    threshold: int
    count_volunteers: int


@app.get("/achievements")
def achievements(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
) -> Dict[str, List[AchievementSummary]]:
    try:
        df = load_dataframe(DATA_PATH)
        df = filter_date_range(df, start, end)
        if not start and not end:
            df = filter_date_range(df, "2024-01-01", None)
        agg = aggregate_by_volunteer(df)
        counts: Dict[str, int] = {label: 0 for _, label in MILESTONES}
        for v in agg:
            for label in v.milestones:
                counts[label] += 1
        summary = [
            AchievementSummary(label=label, threshold=threshold, count_volunteers=counts[label])
            for threshold, label in MILESTONES
        ]
        return {"achievements": summary}
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/volunteers/{contact_id}", response_model=VolunteerAggregate)
def volunteer_detail(contact_id: int):
    try:
        df = load_dataframe(DATA_PATH)
        df = filter_date_range(df, "2024-01-01", None)
        agg = aggregate_by_volunteer(df)
        for v in agg:
            if v.contact_id == contact_id:
                return v
        raise HTTPException(status_code=404, detail="Volunteer not found")
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/volunteer_by_email", response_model=VolunteerAggregate)
def volunteer_by_email(email: str = Query(..., description="Volunteer email (case-insensitive)")):
    try:
        df = load_dataframe(DATA_PATH)
        df = filter_date_range(df, "2024-01-01", None)
        agg = aggregate_by_volunteer(df)
        needle = (email or "").strip().lower()
        for v in agg:
            if v.email == needle:
                return v
        raise HTTPException(status_code=404, detail="Volunteer not found")
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

