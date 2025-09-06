# 🗄️ SUPABASE SETUP INSTRUCTIONS

## Step 1: Set Up Database Schema

1. **Go to your Supabase Dashboard**: https://app.supabase.com/project/ydbjceycutivkipxtaam

2. **Open SQL Editor**: Click on "SQL Editor" in the left sidebar

3. **Run the Setup Script**: Copy and paste the entire contents of `setup_supabase.sql` into the SQL editor and click "Run"

## Step 2: Verify Tables Created

After running the SQL, you should see these tables in your Database > Tables view:
- ✅ users
- ✅ user_preferences  
- ✅ conversations
- ✅ messages
- ✅ volunteer_matches
- ✅ volunteer_feedback
- ✅ analytics_events

## Step 3: Test the Connection

Run this command to test your Supabase integration:
```bash
python test_integrations.py
```

## Quick Setup (Alternative)

If you want to set up the database quickly, run these SQL commands in your Supabase SQL Editor:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
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

-- Other tables... (see setup_supabase.sql for complete schema)
```

## Configuration Status
✅ **Supabase URL**: https://ydbjceycutivkipxtaam.supabase.co  
✅ **API Key**: eyJhbGciOiJIUzI1NiIs... (configured)  
✅ **inference.net**: AI model ready and working!  

Once you've run the SQL setup, the system will be fully operational! 🚀
