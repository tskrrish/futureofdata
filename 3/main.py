"""
Main FastAPI application for Volunteer PathFinder AI Assistant
Brings together AI, matching engine, and database
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import asyncio
from datetime import datetime
import os
import pandas as pd

# Import our modules
from config import settings
from ai_assistant import VolunteerAIAssistant
from matching_engine import VolunteerMatchingEngine
from data_processor import VolunteerDataProcessor
from database import VolunteerDatabase
from bi_connectors import (
    BIConnectorManager, 
    ConnectorConfig, 
    ConnectorType, 
    ExportFormat, 
    RefreshSchedule, 
    bi_connector_manager
)
from scheduler import start_scheduler, stop_scheduler

# Initialize FastAPI app
app = FastAPI(
    title="YMCA Volunteer PathFinder AI Assistant",
    description="AI-powered volunteer matching system for YMCA of Greater Cincinnati",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://yourapp.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
ai_assistant = VolunteerAIAssistant()
database = VolunteerDatabase()
volunteer_data = None
matching_engine = None

# Pydantic models
class UserProfile(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    is_ymca_member: bool = False
    member_branch: Optional[str] = None

class UserPreferences(BaseModel):
    interests: str = ""
    skills: str = ""
    availability: Dict[str, Any] = {}
    time_commitment: int = 2  # 1=low, 2=medium, 3=high
    location_preference: str = ""
    experience_level: int = 1  # 1=beginner, 2=some, 3=experienced
    volunteer_type: str = ""

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None

class FeedbackData(BaseModel):
    match_id: Optional[str] = None
    rating: Optional[int] = None
    feedback_text: str = ""
    feedback_type: str = "general"

class BIConnectorConfigRequest(BaseModel):
    name: str
    connector_type: ConnectorType
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    workspace_id: Optional[str] = None
    dataset_id: Optional[str] = None
    table_id: Optional[str] = None
    refresh_token: Optional[str] = None
    service_account_key: Optional[Dict] = None
    base_url: Optional[str] = None
    custom_config: Optional[Dict] = None

class DataExportRequest(BaseModel):
    connector_name: str
    table_name: str
    export_format: ExportFormat = ExportFormat.JSON
    data_query: Optional[str] = None  # Optional SQL-like query to filter data

class RefreshScheduleRequest(BaseModel):
    connector_name: str
    cron_expression: str = "0 */6 * * *"  # Every 6 hours by default
    enabled: bool = True

# Initialize data on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application data and models"""
    global volunteer_data, matching_engine
    
    print("🚀 Starting Volunteer PathFinder AI Assistant...")
    
    # Initialize database tables
    try:
        await database.initialize_tables()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database initialization note: {e}")
    
    # Load and process volunteer data
    try:
        if os.path.exists(settings.VOLUNTEER_DATA_PATH):
            print("📊 Loading volunteer data...")
            processor = VolunteerDataProcessor(settings.VOLUNTEER_DATA_PATH)
            volunteer_data = processor.get_volunteer_recommendations_data()
            
            # Initialize matching engine
            matching_engine = VolunteerMatchingEngine(volunteer_data)
            matching_engine.train_models()
            
            print(f"✅ Loaded {len(volunteer_data['volunteers'])} volunteer profiles")
            print(f"✅ Loaded {len(volunteer_data['projects'])} projects")
        else:
            print(f"⚠️  Volunteer data file not found: {settings.VOLUNTEER_DATA_PATH}")
    except Exception as e:
        print(f"❌ Error loading volunteer data: {e}")
    
    print("🎉 Volunteer PathFinder AI Assistant is ready!")
    
    # Start BI connector scheduler
    try:
        await start_scheduler()
        print("✅ BI Connector scheduler started")
    except Exception as e:
        print(f"⚠️  BI Connector scheduler initialization note: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down Volunteer PathFinder AI Assistant...")
    
    try:
        await stop_scheduler()
        print("✅ BI Connector scheduler stopped")
    except Exception as e:
        print(f"⚠️  BI Connector scheduler shutdown note: {e}")
    
    print("👋 Volunteer PathFinder AI Assistant shutdown complete")

@app.post("/api/reset")
async def reset_context() -> JSONResponse:
    """Reset assistant context and conversation cache."""
    try:
        ai_assistant.clear_conversation()
        return JSONResponse(content={"reset": True})
    except Exception as e:
        return JSONResponse(content={"reset": False, "error": str(e)}, status_code=500)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_loaded": volunteer_data is not None,
        "models_ready": matching_engine is not None and matching_engine.models_trained
    }

# Serve static files (for web interface)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve chat UI directly
@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    file_path = os.path.join(os.path.dirname(__file__), "static", "chat.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTMLResponse("<h3>Chat UI not found. Create static/chat.html</h3>", status_code=404)

class ProfileRequest(BaseModel):
    name: str

def _split_name(full_name: str) -> tuple[str, str]:
    name = full_name.strip()
    if "," in name:
        last, first = [p.strip() for p in name.split(",", 1)]
        return first, last
    parts = name.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])

def _derive_preferences_from_history(history_df: pd.DataFrame) -> dict:
    preferences: dict = {
        "interests": "",
        "skills": "",
        "availability": {},
        "time_commitment": 2,
        "location_preference": "",
        "experience_level": 2,
        "volunteer_type": "",
        "affinity": {"branches": {}, "categories": {}}
    }
    if history_df.empty:
        return preferences
    # Interests from top categories
    top_categories = (
        history_df["project_category"].dropna().astype(str).str.strip().value_counts().head(2).index.tolist()
    )
    preferences["interests"] = ", ".join(top_categories)
    # Location preference from top branch
    if "branch_short" in history_df.columns and history_df["branch_short"].notna().any():
        preferences["location_preference"] = (
            history_df["branch_short"].dropna().astype(str).str.strip().value_counts().idxmax()
        )
        # Branch affinity histogram
        preferences["affinity"]["branches"] = history_df["branch_short"].dropna().astype(str).value_counts().to_dict()
    # Category affinity histogram
    if "project_category" in history_df.columns and history_df["project_category"].notna().any():
        preferences["affinity"]["categories"] = history_df["project_category"].dropna().astype(str).value_counts().to_dict()
    # Experience level heuristic by sessions
    sessions = history_df["date"].nunique()
    preferences["experience_level"] = 3 if sessions >= 10 else (2 if sessions >= 3 else 1)
    return preferences

@app.post("/api/profile")
async def get_profile_analysis(req: ProfileRequest) -> JSONResponse:
    """Analyze a volunteer's profile by their name from the Excel dataset and suggest matches."""
    if volunteer_data is None:
        raise HTTPException(status_code=503, detail="Volunteer data not loaded")

    interactions: pd.DataFrame = volunteer_data.get("interactions")
    profiles: pd.DataFrame = volunteer_data.get("volunteers")
    projects: pd.DataFrame = volunteer_data.get("projects")
    if interactions is None or profiles is None:
        raise HTTPException(status_code=500, detail="Volunteer dataset incomplete")

    first_name, last_name = _split_name(req.name)
    df = interactions.copy()
    # Normalize name columns
    for col in ("first_name", "last_name"):
        if col in df.columns:
            df[col] = df[col].astype(str)
    # Filter by case-insensitive name match
    mask = df["first_name"].str.lower().str.strip().eq(first_name.lower().strip())
    if last_name:
        mask &= df["last_name"].str.lower().str.strip().eq(last_name.lower().strip())
    candidate_rows = df[mask]

    if candidate_rows.empty:
        # Try partial match on last name if provided
        if last_name:
            mask2 = df["last_name"].str.lower().str.contains(last_name.lower().strip(), na=False)
            candidate_rows = df[mask2]
        if candidate_rows.empty:
            return JSONResponse(content={
                "found": False,
                "message": f"No volunteer found for '{req.name}'. Try exact First Last name as in the records.",
            })

    # Choose the most active contact if multiple
    by_contact = candidate_rows.groupby("contact_id")["hours"].sum().sort_values(ascending=False)
    contact_id = by_contact.index[0]
    person_rows = df[df["contact_id"] == contact_id]

    # Aggregate stats
    # Use pledged total instead of hours to avoid undercounting duplicates
    total_hours = float(person_rows.get("pledged", pd.Series([0]*len(person_rows))).fillna(0).sum())
    sessions = int(person_rows["date"].nunique()) if "date" in person_rows.columns else int(len(person_rows))
    unique_projects = int(person_rows["project_id"].nunique()) if "project_id" in person_rows.columns else 0
    first_date = str(person_rows["date"].min()) if "date" in person_rows.columns else None
    last_date = str(person_rows["date"].max()) if "date" in person_rows.columns else None
    top_branches = person_rows["branch_short"].dropna().astype(str).value_counts().to_dict() if "branch_short" in person_rows.columns else {}
    top_categories = person_rows["project_category"].dropna().astype(str).value_counts().to_dict()

    # Top projects with total hours
    # Top projects by pledged total
    pledged_series = person_rows.get("pledged") if "pledged" in person_rows.columns else person_rows.get("hours")
    agg_df = (
        person_rows.assign(_pledged=pledged_series.fillna(0))
        .groupby(["project_id", "project_clean", "branch_short"], dropna=False)["_pledged"].sum().reset_index()
        .rename(columns={"_pledged": "pledged_total"})
    )
    top_projects_df = agg_df.sort_values("pledged_total", ascending=False).head(5)
    top_projects_list = []
    for _, r in top_projects_df.iterrows():
        top_projects_list.append({
            "project_id": int(r["project_id"]) if pd.notna(r["project_id"]) else None,
            "project_name": str(r["project_clean"]) if pd.notna(r["project_clean"]) else "",
            "branch": str(r["branch_short"]) if pd.notna(r["branch_short"]) else "",
            "pledged": float(r["pledged_total"]) if pd.notna(r["pledged_total"]) else 0.0
        })

    # Pull profile info (age, member, gender, volunteer_type) from aggregated profiles if available
    persona = None
    age = None
    is_member = None
    gender = None
    if "contact_id" in profiles.columns and (profiles["contact_id"] == contact_id).any():
        rowp = profiles[profiles["contact_id"] == contact_id].iloc[0].to_dict()
        persona = rowp.get("volunteer_type")
        age = rowp.get("age")
        is_member = rowp.get("is_ymca_member")
        gender = rowp.get("gender")

    # Derive preferences and recommendations
    preferences = _derive_preferences_from_history(person_rows)
    if persona:
        preferences["volunteer_type"] = str(persona)

    recs = []
    if matching_engine is not None and matching_engine.models_trained:
        try:
            recs = matching_engine.find_matches(preferences, top_k=8)
            # Re-rank using branch/category affinity and engagement heuristics
            branch_aff = (preferences.get("affinity", {}) or {}).get("branches", {})
            cat_aff = (preferences.get("affinity", {}) or {}).get("categories", {})
            sessions_score = min(1.0, (sessions / 10.0))  # more sessions => small boost
            def boosted_score(rec):
                score = rec.get("score", 0) or 0
                b = rec.get("branch", "")
                c = rec.get("category", "")
                boost = 1.0
                if b in branch_aff:
                    boost += 0.08
                if c in cat_aff:
                    boost += 0.08
                boost += 0.04 * sessions_score
                return score * boost
            for rec in recs:
                rec["score"] = float(max(0.0, min(1.0, boosted_score(rec))))
            recs = sorted(recs, key=lambda r: r.get("score", 0), reverse=True)[:5]
        except Exception:
            recs = []

    # Build human-readable summary
    name_display = f"{first_name} {last_name}".strip()
    summary_lines = [
        f"Profile for {name_display}:",
        f"- Total hours: {total_hours:.2f} across {sessions} sessions and {unique_projects} projects",
    ]
    if top_branches:
        top_branch_name = max(top_branches, key=top_branches.get)
        summary_lines.append(f"- Primary branch: {top_branch_name}")
    if top_categories:
        cats = ", ".join(list(top_categories.keys())[:3])
        summary_lines.append(f"- Focus areas: {cats}")
    if persona:
        summary_lines.append(f"- Volunteer type: {persona}")
    if age:
        summary_lines.append(f"- Age: {int(age)}")
    if is_member is not None:
        summary_lines.append(f"- YMCA Member: {'Yes' if is_member else 'No'}")

    profile_payload = {
        "found": True,
        "contact_id": contact_id,
        "name": name_display,
        "stats": {
            "total_hours": total_hours,
            "sessions": sessions,
            "unique_projects": unique_projects,
            "first_date": first_date,
            "last_date": last_date,
        },
        "top_branches": top_branches,
        "top_categories": top_categories,
        "top_projects": top_projects_list,
        "persona": persona,
        "age": age,
        "is_member": is_member,
        "gender": gender,
        "preferences": preferences,
        "recommendations": recs,
        "summary": "\n".join(summary_lines)
    }
    # Save context for subsequent AI chats
    try:
        ai_assistant.add_context("profile", profile_payload)
    except Exception:
        pass
    return JSONResponse(content=profile_payload)

# Main chat interface
@app.post("/api/chat")
async def chat_with_assistant(
    chat_data: ChatMessage,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """Main chat endpoint for the AI assistant"""
    
    try:
        # Get AI response
        response = await ai_assistant.chat(
            user_message=chat_data.message,
            conversation_id=chat_data.conversation_id
        )
        
        # Save to database in background
        if chat_data.conversation_id:
            background_tasks.add_task(
                save_conversation_message,
                chat_data.conversation_id,
                chat_data.message,
                response.get('response', ''),
                chat_data.user_id
            )
        
        # Track analytics
        background_tasks.add_task(
            database.track_event,
            "chat_message",
            {
                "message_length": len(chat_data.message),
                "response_success": response.get('success', False)
            },
            chat_data.user_id,
            chat_data.conversation_id
        )
        
        return JSONResponse(content=response)
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail="Chat service temporarily unavailable")

# Volunteer matching
@app.post("/api/match")
async def get_volunteer_matches(
    preferences: UserPreferences,
    user_id: Optional[str] = None,
    background_tasks: BackgroundTasks = None
) -> JSONResponse:
    """Get personalized volunteer recommendations"""
    
    if not matching_engine:
        raise HTTPException(status_code=503, detail="Matching service not available")
    
    try:
        # Convert preferences to dict
        preferences_dict = preferences.dict()
        
        # Get AI-powered recommendations
        ai_recommendations = await ai_assistant.get_volunteer_recommendations(
            preferences_dict, 
            volunteer_data
        )
        
        # Get ML-based matches
        ml_matches = matching_engine.find_matches(preferences_dict, top_k=5)
        
        # Get success prediction
        success_prediction = matching_engine.predict_volunteer_success(preferences_dict)
        
        # Get branch recommendations
        branch_recommendations = matching_engine.get_branch_recommendations(preferences_dict)
        
        # Combine results
        result = {
            "ai_recommendations": ai_recommendations.get('recommendations', ''),
            "ml_matches": ml_matches,
            "success_prediction": success_prediction,
            "branch_recommendations": branch_recommendations,
            "insights": volunteer_data.get('insights', {}),
            "generated_at": datetime.now().isoformat()
        }
        
        # Save matches to database
        if user_id:
            background_tasks.add_task(
                database.save_volunteer_matches,
                user_id,
                ml_matches
            )
            
            # Save preferences
            background_tasks.add_task(
                database.save_user_preferences,
                user_id,
                preferences_dict
            )
        
        # Track analytics
        background_tasks.add_task(
            database.track_event,
            "volunteer_matching",
            {
                "preferences": preferences_dict,
                "matches_count": len(ml_matches),
                "top_match_score": ml_matches[0]['score'] if ml_matches else 0
            },
            user_id
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        print(f"❌ Matching error: {e}")
        raise HTTPException(status_code=500, detail="Matching service temporarily unavailable")

# User management
@app.post("/api/users")
async def create_user(user_data: UserProfile) -> JSONResponse:
    """Create a new user profile"""
    
    try:
        user = await database.create_user(user_data.dict(exclude_unset=True))
        
        if user:
            # Track user creation
            await database.track_event(
                "user_created",
                {"source": "api"},
                user['id']
            )
            
            return JSONResponse(content={"user": user, "success": True})
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
            
    except Exception as e:
        print(f"❌ User creation error: {e}")
        raise HTTPException(status_code=500, detail="User creation failed")

@app.get("/api/users/{user_id}")
async def get_user(user_id: str) -> JSONResponse:
    """Get user profile"""
    
    try:
        user = await database.get_user(user_id=user_id)
        
        if user:
            # Get user preferences
            preferences = await database.get_user_preferences(user_id)
            
            # Get user matches
            matches = await database.get_user_matches(user_id)
            
            return JSONResponse(content={
                "user": user,
                "preferences": preferences,
                "matches": matches,
                "success": True
            })
        else:
            raise HTTPException(status_code=404, detail="User not found")
            
    except Exception as e:
        print(f"❌ Get user error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user")

# Conversations
@app.post("/api/conversations")
async def start_conversation(user_id: Optional[str] = None) -> JSONResponse:
    """Start a new conversation"""
    
    try:
        conversation_id = await database.create_conversation(user_id=user_id)
        
        # Track conversation start
        await database.track_event(
            "conversation_started",
            {},
            user_id,
            conversation_id
        )
        
        return JSONResponse(content={
            "conversation_id": conversation_id,
            "success": True
        })
        
    except Exception as e:
        print(f"❌ Conversation creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start conversation")

@app.get("/api/conversations/{conversation_id}/history")
async def get_conversation_history(conversation_id: str) -> JSONResponse:
    """Get conversation history"""
    
    try:
        messages = await database.get_conversation_history(conversation_id)
        
        return JSONResponse(content={
            "messages": messages,
            "conversation_id": conversation_id,
            "success": True
        })
        
    except Exception as e:
        print(f"❌ Get conversation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation")

# Onboarding guidance
@app.get("/api/onboarding/{step}")
async def get_onboarding_guidance(step: str) -> JSONResponse:
    """Get step-by-step onboarding guidance"""
    
    try:
        guidance = await ai_assistant.get_onboarding_guidance(step)
        
        return JSONResponse(content=guidance)
        
    except Exception as e:
        print(f"❌ Onboarding guidance error: {e}")
        raise HTTPException(status_code=500, detail="Onboarding guidance not available")

# Feedback
@app.post("/api/feedback")
async def submit_feedback(
    feedback_data: FeedbackData,
    user_id: Optional[str] = None
) -> JSONResponse:
    """Submit user feedback"""
    
    try:
        success = await database.save_feedback(user_id, feedback_data.dict())
        
        if success:
            # Track feedback submission
            await database.track_event(
                "feedback_submitted",
                {
                    "feedback_type": feedback_data.feedback_type,
                    "rating": feedback_data.rating
                },
                user_id
            )
            
            return JSONResponse(content={"success": True})
        else:
            raise HTTPException(status_code=400, detail="Failed to save feedback")
            
    except Exception as e:
        print(f"❌ Feedback error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit feedback")

# Analytics
@app.get("/api/analytics")
async def get_analytics(days: int = 30) -> JSONResponse:
    """Get system analytics"""
    
    try:
        analytics = await database.get_user_analytics(days)
        popular_matches = await database.get_popular_matches()
        
        # Add volunteer data insights
        insights = volunteer_data.get('insights', {}) if volunteer_data else {}
        
        result = {
            "usage_analytics": analytics,
            "popular_matches": popular_matches,
            "volunteer_insights": insights,
            "system_status": {
                "data_loaded": volunteer_data is not None,
                "models_trained": matching_engine is not None and matching_engine.models_trained,
                "total_volunteers": len(volunteer_data['volunteers']) if volunteer_data else 0,
                "total_projects": len(volunteer_data['projects']) if volunteer_data else 0
            }
        }
        
        return JSONResponse(content=result)
        
    except Exception as e:
        print(f"❌ Analytics error: {e}")
        raise HTTPException(status_code=500, detail="Analytics not available")

# Resources and information
@app.get("/api/resources")
async def get_resources() -> JSONResponse:
    """Get YMCA volunteer resources and links"""
    
    resources = {
        "official_links": {
            "volunteer_page": settings.YMCA_VOLUNTEER_PAGE,
            "project_catalog": settings.VOLUNTEER_MATTERS_CATALOG,
            "interest_form": settings.VOLUNTEER_INTEREST_FORM,
            "registration": "https://cincinnatiymca.volunteermatters.org/volunteer/register"
        },
        "branches": {
            "Blue Ash YMCA": {
                "address": "4449 Cooper Rd, Blue Ash, OH 45242",
                "phone": "(513) 745-9622",
                "specialties": ["Fitness", "Youth Programs", "Competitive Swimming"]
            },
            "M.E. Lyons YMCA": {
                "address": "3447 Madison Rd, Cincinnati, OH 45209", 
                "phone": "(513) 871-4900",
                "specialties": ["Group Exercise", "Community Events", "Senior Programs"]
            },
            "Campbell County YMCA": {
                "address": "2.05 Dave Cowens Dr, Newport, KY 41071",
                "phone": "(859) 431-5000",
                "specialties": ["Youth Development", "Childcare", "Family Programs"]
            },
            "Clippard YMCA": {
                "address": "2143 Ferguson Rd, Cincinnati, OH 45238",
                "phone": "(513) 681-0003",
                "specialties": ["Youth Sports", "Leadership Development", "Community Outreach"]
            }
        },
        "volunteer_types": {
            "Youth Development": "Mentoring, after-school programs, summer camps",
            "Fitness & Wellness": "Group exercise, swimming instruction, sports coaching",
            "Special Events": "Fundraisers, community celebrations, holiday programs",
            "Facility Support": "Maintenance, organization, member services",
            "Administrative": "Office support, data entry, communications"
        }
    }
    
    return JSONResponse(content=resources)

# Main web interface
@app.get("/", response_class=HTMLResponse)
async def main_interface():
    """Minimal home that routes to the Chat UI."""
    return HTMLResponse("""
    <!doctype html>
    <html lang=\"en\">
    <head>
      <meta charset=\"utf-8\" />
      <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
      <title>YMCA Volunteer PathFinder</title>
      <style>
        :root {
          --bg: #ffffff; --fg: #111111; --muted: #6b7280; --border: #e5e7eb; --accent: #111111;
        }
        *{box-sizing:border-box}
        body{margin:0;font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto;background:var(--bg);color:var(--fg)}
        .wrap{max-width:1000px;margin:0 auto;padding:32px}
        .hero{padding:40px 0;border-bottom:1px solid var(--border)}
        h1{font-size:32px;margin:0 0 6px 0}
        p.lead{color:var(--muted);font-size:16px;margin:0}
        .cta{display:inline-block;margin-top:16px;padding:12px 18px;border:1px solid var(--fg);border-radius:999px;text-decoration:none;color:var(--bg);background:var(--fg);font-weight:700}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-top:24px}
        .card{border:1px solid var(--border);border-radius:12px;padding:16px;background:#fff}
        h2{font-size:20px;margin:0 0 10px 0}
        ul{margin:8px 0 0 18px;padding:0}
        li{margin:6px 0;color:#222}
        a{color:#111;text-underline-offset:3px}
        .section{padding:28px 0;border-top:1px solid var(--border)}
        .muted{color:var(--muted)}
      </style>
    </head>
    <body>
      <div class=\"wrap\">
        <section class=\"hero\">
          <h1>YMCA Volunteer PathFinder</h1>
          <p class=\"lead\">An AI assistant that helps you explore, understand, and navigate YMCA volunteer opportunities.</p>
          <a class=\"cta\" href=\"/chat\">Start Chat</a>
        </section>

        <section class=\"section\">
          <div class=\"grid\">
            <div class=\"card\">
              <h2>What it can do</h2>
              <ul>
                <li>Answer questions about volunteering (requirements, process, types)</li>
                <li>Guide you step-by-step through VolunteerMatters onboarding</li>
                <li>Recommend roles based on interests, age, and schedule</li>
                <li>Point you to the right resources and next steps</li>
              </ul>
            </div>
            <div class=\"card\">
              <h2>How it works</h2>
              <ul>
                <li><strong>Tell your name</strong> – we analyze your past activity (if any) from YMCA records</li>
                <li><strong>Share preferences</strong> – interests, availability, location</li>
                <li><strong>Get matches</strong> – personalized, with reasons and time commitments</li>
                <li><strong>Onboard</strong> – step-by-step help to register and complete credentials</li>
              </ul>
            </div>
            <div class=\"card\">
              <h2>Resources</h2>
              <ul>
                <li><a href=\"https://www.myy.org/volunteering\" target=\"_blank\">YMCA of Greater Cincinnati – Volunteering</a></li>
                <li><a href=\"https://cincinnatiymca.volunteermatters.org/project-catalog\" target=\"_blank\">VolunteerMatters Project Catalog</a></li>
                <li><a href=\"https://ymcacincinnati.qualtrics.com/jfe/form/SV_0JklTjQEJTQmS2i\" target=\"_blank\">Volunteer Interest Form</a></li>
                <li><a href=\"https://cincinnatiymca.volunteermatters.org/volunteer/register\" target=\"_blank\">VolunteerMatters – Register</a></li>
              </ul>
            </div>
          </div>
        </section>

        <section class=\"section\">
          <div class=\"grid\">
            <div class=\"card\">
              <h2>Optional add‑ons</h2>
              <ul>
                <li>Chat-style experience (this site)</li>
                <li>Sample Q&A for FAQs (credentials, background checks, training)</li>
                <li>Visual guides and links for next steps</li>
              </ul>
            </div>
            <div class=\"card\">
              <h2>Success by end of day</h2>
              <ul>
                <li>A functioning assistant that supports new volunteers</li>
                <li>Friendly, accurate, YMCA-aligned guidance</li>
                <li>Clear docs on how staff/branches can use it</li>
              </ul>
            </div>
            <div class=\"card\">
              <h2>Purpose & Impact</h2>
              <p class=\"muted\">Help individuals explore volunteering with confidence and clarity — making it easier to take the first step and contribute in ways aligned with YMCA needs.</p>
            </div>
          </div>
        </section>

        <section class=\"section\">
          <p class=\"muted\">Need help now? <a href=\"/chat\">Open the assistant</a> and say 
            <em>“My name is First Last”</em> to get personalized recommendations.</p>
        </section>
      </div>
    </body>
    </html>
    """)

# BI Connector Management Endpoints
@app.post("/api/bi-connectors/register")
async def register_bi_connector(config_request: BIConnectorConfigRequest) -> JSONResponse:
    """Register a new BI connector"""
    try:
        config = ConnectorConfig(
            name=config_request.name,
            connector_type=config_request.connector_type,
            api_key=config_request.api_key,
            client_id=config_request.client_id,
            client_secret=config_request.client_secret,
            workspace_id=config_request.workspace_id,
            dataset_id=config_request.dataset_id,
            table_id=config_request.table_id,
            refresh_token=config_request.refresh_token,
            service_account_key=config_request.service_account_key,
            base_url=config_request.base_url,
            custom_config=config_request.custom_config
        )
        
        success = bi_connector_manager.register_connector(config)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": f"BI connector '{config_request.name}' registered successfully",
                "connector_type": config_request.connector_type
            })
        else:
            raise HTTPException(status_code=400, detail="Failed to register BI connector")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BI connector registration failed: {str(e)}")

@app.get("/api/bi-connectors")
async def list_bi_connectors() -> JSONResponse:
    """List all registered BI connectors"""
    try:
        connectors = bi_connector_manager.list_connectors()
        return JSONResponse(content={
            "success": True,
            "connectors": connectors,
            "count": len(connectors)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list connectors: {str(e)}")

@app.post("/api/bi-connectors/{connector_name}/test")
async def test_bi_connector(connector_name: str) -> JSONResponse:
    """Test connection to a specific BI connector"""
    try:
        connector = bi_connector_manager.get_connector(connector_name)
        if not connector:
            raise HTTPException(status_code=404, detail=f"Connector '{connector_name}' not found")
        
        result = await connector.test_connection()
        return JSONResponse(content={
            "connector_name": connector_name,
            **result
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@app.post("/api/bi-connectors/test-all")
async def test_all_bi_connectors() -> JSONResponse:
    """Test connections to all registered BI connectors"""
    try:
        results = await bi_connector_manager.test_all_connectors()
        return JSONResponse(content={
            "success": True,
            "test_results": results
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection tests failed: {str(e)}")

@app.post("/api/bi-connectors/export")
async def export_data_to_bi(
    export_request: DataExportRequest,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """Export volunteer data to BI connector"""
    try:
        # Get volunteer data for export
        if volunteer_data is None:
            raise HTTPException(status_code=503, detail="Volunteer data not loaded")
        
        # Prepare data based on request
        if export_request.data_query:
            # In a real implementation, you'd parse and execute the query
            # For now, we'll export all volunteer data
            data_df = pd.DataFrame(volunteer_data.get('volunteers', []))
        else:
            # Export all volunteer data
            data_df = pd.DataFrame(volunteer_data.get('volunteers', []))
        
        if data_df.empty:
            raise HTTPException(status_code=400, detail="No data available for export")
        
        # Start export job in background
        job = await bi_connector_manager.export_data_to_connector(
            export_request.connector_name,
            data_df,
            export_request.table_name,
            export_request.export_format
        )
        
        return JSONResponse(content={
            "success": True,
            "job_id": job.id,
            "message": f"Export job started for connector '{export_request.connector_name}'",
            "status": job.status,
            "record_count": job.record_count
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data export failed: {str(e)}")

@app.get("/api/bi-connectors/export-jobs/{job_id}")
async def get_export_job_status(job_id: str) -> JSONResponse:
    """Get status of export job"""
    try:
        job = bi_connector_manager.get_export_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Export job '{job_id}' not found")
        
        return JSONResponse(content={
            "success": True,
            "job": {
                "id": job.id,
                "connector_name": job.connector_name,
                "connector_type": job.connector_type,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message,
                "record_count": job.record_count,
                "export_format": job.export_format
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@app.post("/api/bi-connectors/{connector_name}/refresh")
async def refresh_bi_connector_dataset(
    connector_name: str,
    dataset_id: Optional[str] = None
) -> JSONResponse:
    """Refresh dataset in BI connector"""
    try:
        result = await bi_connector_manager.refresh_connector_dataset(connector_name, dataset_id)
        
        return JSONResponse(content={
            "connector_name": connector_name,
            "dataset_id": dataset_id,
            **result
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dataset refresh failed: {str(e)}")

@app.post("/api/bi-connectors/schedules")
async def create_refresh_schedule(schedule_request: RefreshScheduleRequest) -> JSONResponse:
    """Create a refresh schedule for BI connector"""
    try:
        # Verify connector exists
        connector = bi_connector_manager.get_connector(schedule_request.connector_name)
        if not connector:
            raise HTTPException(status_code=404, detail=f"Connector '{schedule_request.connector_name}' not found")
        
        schedule = RefreshSchedule(
            connector_name=schedule_request.connector_name,
            cron_expression=schedule_request.cron_expression,
            enabled=schedule_request.enabled,
            next_run=datetime.now() + pd.Timedelta(hours=1)  # Schedule first run in 1 hour
        )
        
        bi_connector_manager.add_refresh_schedule(schedule)
        
        return JSONResponse(content={
            "success": True,
            "schedule_id": schedule.id,
            "message": f"Refresh schedule created for connector '{schedule_request.connector_name}'",
            "cron_expression": schedule_request.cron_expression,
            "next_run": schedule.next_run.isoformat() if schedule.next_run else None
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create refresh schedule: {str(e)}")

@app.get("/api/bi-connectors/schedules")
async def list_refresh_schedules() -> JSONResponse:
    """List all refresh schedules"""
    try:
        schedules = bi_connector_manager.get_refresh_schedules()
        
        return JSONResponse(content={
            "success": True,
            "schedules": [
                {
                    "id": s.id,
                    "connector_name": s.connector_name,
                    "cron_expression": s.cron_expression,
                    "enabled": s.enabled,
                    "last_run": s.last_run.isoformat() if s.last_run else None,
                    "next_run": s.next_run.isoformat() if s.next_run else None,
                    "created_at": s.created_at.isoformat()
                }
                for s in schedules
            ],
            "count": len(schedules)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list schedules: {str(e)}")

@app.delete("/api/bi-connectors/{connector_name}")
async def remove_bi_connector(connector_name: str) -> JSONResponse:
    """Remove a BI connector"""
    try:
        if connector_name in bi_connector_manager.connectors:
            del bi_connector_manager.connectors[connector_name]
            return JSONResponse(content={
                "success": True,
                "message": f"BI connector '{connector_name}' removed successfully"
            })
        else:
            raise HTTPException(status_code=404, detail=f"Connector '{connector_name}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove connector: {str(e)}")

# Background task helpers
async def save_conversation_message(conversation_id: str, user_message: str, 
                                  ai_response: str, user_id: str = None):
    """Save conversation messages to database"""
    try:
        await database.save_message(conversation_id, 'user', user_message, user_id)
        await database.save_message(conversation_id, 'assistant', ai_response, user_id)
    except Exception as e:
        print(f"❌ Error saving conversation: {e}")

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
