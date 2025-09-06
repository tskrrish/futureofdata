# 🚀 QUICK SETUP - 2 MINUTES TO LAUNCH!

## Step 1: Create Database Tables (30 seconds)

**Go to**: https://app.supabase.com/project/ydbjceycutivkipxtaam/sql

**Paste this SQL and click "Run":**

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS public.users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    age INTEGER,
    gender VARCHAR(20),
    city VARCHAR(100),
    state VARCHAR(10),
    zip_code VARCHAR(10),
    is_ymca_member BOOLEAN DEFAULT FALSE,
    member_branch VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.user_preferences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    interests TEXT,
    skills TEXT,
    availability JSONB DEFAULT '{}',
    time_commitment INTEGER DEFAULT 2,
    location_preference VARCHAR(100),
    experience_level INTEGER DEFAULT 1,
    volunteer_type VARCHAR(50),
    preferences_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    session_id VARCHAR(100),
    conversation_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id UUID,
    role VARCHAR(20) CHECK (role IN ('user', 'assistant')),
    content TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.volunteer_matches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    project_id INTEGER,
    project_name VARCHAR(200),
    branch VARCHAR(100),
    category VARCHAR(100),
    match_score DECIMAL(3,2),
    reasons JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'suggested',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.analytics_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID,
    session_id VARCHAR(100),
    event_type VARCHAR(50),
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

SELECT 'Database ready!' as result;
```

## Step 2: Launch System (30 seconds)

```bash
python start.py
```

## That's it! System will be running at:
- **Web Interface**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## ✅ What's Working:
- 🤖 **AI Assistant**: Fully operational with Llama 3.2
- 🎯 **Smart Matching**: ML-powered recommendations
- 🌐 **Web Interface**: Beautiful modern UI
- 📊 **Real Data**: 3,079+ volunteers, 437+ projects
- 💬 **Conversations**: Intelligent chat guidance

**Total setup time: 2 minutes!** 🎉
