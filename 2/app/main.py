from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from shared_constants import (
    MILESTONES,
    MILESTONE_DETAILS,
    REQUIRED_CSV_COLUMNS,
    STORYWORLD_KEYWORDS,
    compute_milestones,
)
from streak_service import get_streak_summary


DATA_PATH = Path(__file__).resolve().parent.parent / "Y_Volunteer_Raw_Data_Jan_August_2025.csv"


class StreakInfo(BaseModel):
    current_streak: int
    longest_streak: int
    is_active: bool
    grace_days_remaining: int
    milestones: List[str]


class VolunteerStreaks(BaseModel):
    weekly: StreakInfo
    monthly: StreakInfo


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
    projects: List[str]
    storyworlds: List[str]
    branches: List[str]
    streaks: VolunteerStreaks




def load_dataframe(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found at {csv_path}")
    df = pd.read_csv(csv_path)
    # Normalize columns we rely on
    expected_columns = REQUIRED_CSV_COLUMNS
    missing = expected_columns - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {sorted(missing)}")
    # Types
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Pledged"] = pd.to_numeric(df["Pledged"], errors="coerce").fillna(0.0)
    df["Fulfilled"] = pd.to_numeric(df["Fulfilled"], errors="coerce").fillna(0)
    # Clean names and ids
    if "Contact ID" in df:
        df["Contact ID"] = pd.to_numeric(df["Contact ID"], errors="coerce").astype("Int64")
    # Strip whitespace in names
    df["First Name"] = df["First Name"].fillna("").astype(str).str.strip()
    df["Last Name"] = df["Last Name"].fillna("").astype(str).str.strip()
    if "Email" in df:
        df["Email"] = df["Email"].fillna("").astype(str).str.strip().str.lower()
    # Clean project and branch data
    df["Project"] = df["Project"].fillna("").astype(str).str.strip()
    df["Project Tags"] = df["Project Tags"].fillna("").astype(str).str.strip()
    df["Branch"] = df["Branch"].fillna("").astype(str).str.strip()
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




def aggregate_by_volunteer(df: pd.DataFrame) -> List[VolunteerAggregate]:
    # Filter to only fulfilled entries
    fulfilled_df = df[df["Fulfilled"] == 1].copy()
    
    def map_row_to_storyworlds(row: pd.Series) -> List[str]:
        tags = (row.get("Project Tags") or "").lower()
        project = (row.get("Project") or "").lower()
        candidates = f"{tags} {project}"
        storyworlds: List[str] = []
        
        for storyworld_name, keywords in STORYWORLD_KEYWORDS.items():
            if any(keyword in candidates for keyword in keywords):
                storyworlds.append(storyworld_name)
        
        # Fallbacks based on Branch Support if no match
        if not storyworlds and "branch support" in candidates:
            storyworlds.append("Neighbor Power")
        return list(dict.fromkeys(storyworlds))  # de-dup preserving order

    grouped = fulfilled_df.groupby(["Contact ID", "First Name", "Last Name", "Email"], dropna=False)
    results: List[VolunteerAggregate] = []
    for (contact_id, first_name, last_name, email), g in grouped:
        # Sum up pledged hours for this volunteer
        hours_total = float(g["Pledged"].sum())
        first_activity = None
        last_activity = None
        if not g["Date"].isna().all():
            first_dt = g["Date"].min()
            last_dt = g["Date"].max()
            first_activity = first_dt.strftime("%Y-%m-%d") if pd.notna(first_dt) else None
            last_activity = last_dt.strftime("%Y-%m-%d") if pd.notna(last_dt) else None

        # Collect projects, branches, and storyworlds
        projects = sorted(set([p for p in g.get("Project", []).astype(str).tolist() if p]))
        branches = sorted(set([b for b in g.get("Branch", []).astype(str).tolist() if b]))
        storyworlds_set: List[str] = []
        for _, row in g.iterrows():
            for sw in map_row_to_storyworlds(row):
                if sw not in storyworlds_set:
                    storyworlds_set.append(sw)

        # Calculate streak information
        streak_summary = get_streak_summary(g)
        volunteer_streaks = VolunteerStreaks(
            weekly=StreakInfo(
                current_streak=streak_summary['weekly']['current_streak'],
                longest_streak=streak_summary['weekly']['longest_streak'],
                is_active=streak_summary['weekly']['is_active'],
                grace_days_remaining=streak_summary['weekly']['grace_days_remaining'],
                milestones=streak_summary['weekly']['milestones']
            ),
            monthly=StreakInfo(
                current_streak=streak_summary['monthly']['current_streak'],
                longest_streak=streak_summary['monthly']['longest_streak'],
                is_active=streak_summary['monthly']['is_active'],
                grace_days_remaining=streak_summary['monthly']['grace_days_remaining'],
                milestones=streak_summary['monthly']['milestones']
            )
        )

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
                projects=projects[:6],
                storyworlds=storyworlds_set[:5],
                branches=branches[:5],
                streaks=volunteer_streaks,
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


class StreakLeaderboard(BaseModel):
    volunteer_name: str
    contact_id: Optional[int]
    current_streak: int
    longest_streak: int
    is_active: bool
    grace_days_remaining: int


@app.get("/streak_leaderboard")
def streak_leaderboard(
    streak_type: str = Query("weekly", description="Streak type: 'weekly' or 'monthly'"),
    sort_by: str = Query("current", description="Sort by 'current' or 'longest' streak"),
    limit: int = Query(50, description="Maximum number of results")
) -> Dict[str, List[StreakLeaderboard]]:
    """Get streak leaderboard for weekly or monthly streaks."""
    try:
        if streak_type not in ["weekly", "monthly"]:
            raise HTTPException(status_code=400, detail="streak_type must be 'weekly' or 'monthly'")
        
        if sort_by not in ["current", "longest"]:
            raise HTTPException(status_code=400, detail="sort_by must be 'current' or 'longest'")
        
        df = load_dataframe(DATA_PATH)
        df = filter_date_range(df, "2024-01-01", None)
        agg = aggregate_by_volunteer(df)
        
        # Extract streak data for leaderboard
        leaderboard_data = []
        for volunteer in agg:
            streak_info = volunteer.streaks.weekly if streak_type == "weekly" else volunteer.streaks.monthly
            
            leaderboard_data.append(StreakLeaderboard(
                volunteer_name=f"{volunteer.first_name} {volunteer.last_name}",
                contact_id=volunteer.contact_id,
                current_streak=streak_info.current_streak,
                longest_streak=streak_info.longest_streak,
                is_active=streak_info.is_active,
                grace_days_remaining=streak_info.grace_days_remaining
            ))
        
        # Sort by requested criteria
        if sort_by == "current":
            leaderboard_data.sort(key=lambda x: x.current_streak, reverse=True)
        else:  # sort_by == "longest"
            leaderboard_data.sort(key=lambda x: x.longest_streak, reverse=True)
        
        return {"leaderboard": leaderboard_data[:limit]}
        
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

