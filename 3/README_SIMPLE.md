# 🎯 VOLUNTEER PATHFINDER AI ASSISTANT

**AI-powered volunteer matching system for YMCA of Greater Cincinnati**

*"The Netflix of Volunteer Matching"* - Intelligent assistant that matches passion with purpose.

---

## 🚀 QUICK START

### 1. Launch the System
```bash
python start.py
```

### 2. Access the Web Interface
- **Main Interface**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## ✨ FEATURES

- **🤖 Smart Matching**: ML-powered volunteer-opportunity matching
- **💬 AI Chat**: Conversational guidance using Llama 3.2
- **📊 Predictions**: Success forecasting and analytics
- **🏢 Branch Recommendations**: Location-based suggestions
- **🌐 Modern UI**: Beautiful web interface

---

## 📊 BUILT WITH REAL DATA

- **3,079 Volunteers** 
- **72,526 Volunteer Hours**
- **437 Projects**
- **25 YMCA Branches**

---

## 🛠️ SYSTEM COMPONENTS

- `data_processor.py` - Analyzes Excel volunteer data
- `matching_engine.py` - ML matching algorithms  
- `ai_assistant.py` - Conversational AI using inference.net
- `database.py` - Supabase integration
- `main.py` - FastAPI web backend
- `start.py` - Easy startup script

---

## 🔌 KEY API ENDPOINTS

```http
POST /api/chat          # Chat with AI assistant
POST /api/match         # Get volunteer recommendations
GET /api/onboarding     # Step-by-step guidance
GET /api/resources      # YMCA information
```

---

## ⚙️ CONFIGURATION

Create `.env` file:
```env
# Optional - for AI features
INFERENCE_NET_API_KEY=your_key

# Optional - for data storage  
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
```

---

## 🧪 TEST THE SYSTEM

```bash
# Quick demo
python test_system.py

# Expected output:
✅ Data loaded: 3079 volunteers, 437 projects  
✅ ML models trained successfully
🎯 Sample Matches for fitness interests:
   • Highland County - Group Ex Volunteer (Score: 0.92)
   • R.C. Durr - Swim Lesson Volunteer (Score: 0.88)
```

---

## 🌟 SUCCESS METRICS

**Target Impact:**
- 50% faster volunteer onboarding
- 80% VolunteerMatters completion rate
- 30% increase in volunteer retention  
- 4.8+ star satisfaction rating

---

**🎉 Ready to revolutionize volunteer matching at the YMCA!**

*Built with ❤️ using Python, FastAPI, scikit-learn, and Llama 3.2*
