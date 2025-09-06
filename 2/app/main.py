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

import uuid
from datetime import datetime, timezone
from enum import Enum


DATA_PATH = Path(__file__).resolve().parent.parent / "Y_Volunteer_Raw_Data_Jan_August_2025.csv"

# In-memory storage for gift card redemptions (in production, use a database)
gift_card_redemptions: Dict[str, GiftCardRedemption] = {}

# Available gift card options with points conversion (1 hour = 10 points)
GIFT_CARD_OPTIONS: List[GiftCardOption] = [
    GiftCardOption(
        provider=GiftCardProvider.AMAZON,
        denomination=25,
        points_required=250,
        name="Amazon Gift Card - $25",
        description="Shop millions of products on Amazon"
    ),
    GiftCardOption(
        provider=GiftCardProvider.AMAZON,
        denomination=50,
        points_required=500,
        name="Amazon Gift Card - $50",
        description="Shop millions of products on Amazon"
    ),
    GiftCardOption(
        provider=GiftCardProvider.STARBUCKS,
        denomination=10,
        points_required=100,
        name="Starbucks Gift Card - $10",
        description="Enjoy your favorite coffee and treats"
    ),
    GiftCardOption(
        provider=GiftCardProvider.STARBUCKS,
        denomination=25,
        points_required=250,
        name="Starbucks Gift Card - $25",
        description="Enjoy your favorite coffee and treats"
    ),
    GiftCardOption(
        provider=GiftCardProvider.TARGET,
        denomination=25,
        points_required=250,
        name="Target Gift Card - $25",
        description="Shop at Target stores nationwide"
    ),
    GiftCardOption(
        provider=GiftCardProvider.WALMART,
        denomination=25,
        points_required=250,
        name="Walmart Gift Card - $25",
        description="Shop at Walmart stores and online"
    ),
    GiftCardOption(
        provider=GiftCardProvider.VISA,
        denomination=50,
        points_required=500,
        name="Visa Gift Card - $50",
        description="Use anywhere Visa is accepted"
    ),
]


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
    points_total: Optional[int] = None
    points_available: Optional[int] = None




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

        # Calculate points for this volunteer
        points_total = calculate_volunteer_points(hours_total)
        contact_id_int = int(contact_id) if pd.notna(contact_id) else None
        
        # Calculate points used in redemptions if contact_id is available
        points_used = 0
        if contact_id_int:
            points_used = sum(
                redemption.points_used 
                for redemption in gift_card_redemptions.values() 
                if redemption.volunteer_contact_id == contact_id_int
            )
        
        points_available = points_total - points_used

        results.append(
            VolunteerAggregate(
                contact_id=contact_id_int,
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
                points_total=points_total,
                points_available=points_available,
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


class GiftCardProvider(str, Enum):
    AMAZON = "amazon"
    STARBUCKS = "starbucks"
    TARGET = "target"
    WALMART = "walmart"
    VISA = "visa"


class GiftCardOption(BaseModel):
    provider: GiftCardProvider
    denomination: int
    points_required: int
    name: str
    description: str
    image_url: Optional[str] = None


class GiftCardRedemption(BaseModel):
    id: str
    volunteer_contact_id: int
    provider: GiftCardProvider
    denomination: int
    points_used: int
    status: str
    redemption_code: Optional[str] = None
    created_at: str
    fulfilled_at: Optional[str] = None


class RedemptionRequest(BaseModel):
    volunteer_contact_id: int
    provider: GiftCardProvider
    denomination: int


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


def calculate_volunteer_points(hours: float) -> int:
    """Convert volunteer hours to points (1 hour = 10 points)"""
    return int(hours * 10)


def generate_gift_card_code(provider: GiftCardProvider, denomination: int) -> str:
    """Generate a mock gift card code for demonstration"""
    provider_prefix = {
        GiftCardProvider.AMAZON: "AMZ",
        GiftCardProvider.STARBUCKS: "SBX",
        GiftCardProvider.TARGET: "TGT",
        GiftCardProvider.WALMART: "WMT",
        GiftCardProvider.VISA: "VSA"
    }
    
    # Generate a mock code with provider prefix and random numbers
    import random
    code_suffix = ''.join([str(random.randint(0, 9)) for _ in range(12)])
    return f"{provider_prefix[provider]}-{code_suffix[:4]}-{code_suffix[4:8]}-{code_suffix[8:]}"


@app.get("/gift-cards/options", response_model=List[GiftCardOption])
def get_gift_card_options():
    """Get available gift card redemption options"""
    return GIFT_CARD_OPTIONS


@app.get("/volunteers/{contact_id}/points")
def get_volunteer_points(contact_id: int):
    """Get volunteer's available points balance"""
    try:
        df = load_dataframe(DATA_PATH)
        df = filter_date_range(df, "2024-01-01", None)
        agg = aggregate_by_volunteer(df)
        
        for volunteer in agg:
            if volunteer.contact_id == contact_id:
                points = calculate_volunteer_points(volunteer.hours_total)
                
                # Calculate points used in redemptions
                points_used = sum(
                    redemption.points_used 
                    for redemption in gift_card_redemptions.values() 
                    if redemption.volunteer_contact_id == contact_id
                )
                
                available_points = points - points_used
                
                return {
                    "contact_id": contact_id,
                    "total_hours": volunteer.hours_total,
                    "total_points": points,
                    "points_used": points_used,
                    "available_points": available_points
                }
        
        raise HTTPException(status_code=404, detail="Volunteer not found")
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/gift-cards/redeem", response_model=GiftCardRedemption)
def redeem_gift_card(request: RedemptionRequest):
    """Redeem points for a gift card"""
    try:
        # Get volunteer info
        df = load_dataframe(DATA_PATH)
        df = filter_date_range(df, "2024-01-01", None)
        agg = aggregate_by_volunteer(df)
        
        volunteer = None
        for v in agg:
            if v.contact_id == request.volunteer_contact_id:
                volunteer = v
                break
        
        if not volunteer:
            raise HTTPException(status_code=404, detail="Volunteer not found")
        
        # Find the requested gift card option
        gift_card_option = None
        for option in GIFT_CARD_OPTIONS:
            if (option.provider == request.provider and 
                option.denomination == request.denomination):
                gift_card_option = option
                break
        
        if not gift_card_option:
            raise HTTPException(status_code=404, detail="Gift card option not found")
        
        # Calculate available points
        total_points = calculate_volunteer_points(volunteer.hours_total)
        points_used = sum(
            redemption.points_used 
            for redemption in gift_card_redemptions.values() 
            if redemption.volunteer_contact_id == request.volunteer_contact_id
        )
        available_points = total_points - points_used
        
        # Check if volunteer has enough points
        if available_points < gift_card_option.points_required:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient points. Need {gift_card_option.points_required}, have {available_points}"
            )
        
        # Create redemption record
        redemption_id = str(uuid.uuid4())
        redemption = GiftCardRedemption(
            id=redemption_id,
            volunteer_contact_id=request.volunteer_contact_id,
            provider=request.provider,
            denomination=request.denomination,
            points_used=gift_card_option.points_required,
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        # Store the redemption
        gift_card_redemptions[redemption_id] = redemption
        
        # Simulate gift card code generation (in production, integrate with actual providers)
        redemption.redemption_code = generate_gift_card_code(request.provider, request.denomination)
        redemption.status = "fulfilled"
        redemption.fulfilled_at = datetime.now(timezone.utc).isoformat()
        
        return redemption
        
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/volunteers/{contact_id}/redemptions", response_model=List[GiftCardRedemption])
def get_volunteer_redemptions(contact_id: int):
    """Get all gift card redemptions for a volunteer"""
    redemptions = [
        redemption for redemption in gift_card_redemptions.values()
        if redemption.volunteer_contact_id == contact_id
    ]
    
    # Sort by creation date (newest first)
    redemptions.sort(key=lambda x: x.created_at, reverse=True)
    return redemptions


@app.get("/gift-cards/redemptions", response_model=List[GiftCardRedemption])
def get_all_redemptions():
    """Get all gift card redemptions (admin endpoint)"""
    redemptions = list(gift_card_redemptions.values())
    redemptions.sort(key=lambda x: x.created_at, reverse=True)
    return redemptions

