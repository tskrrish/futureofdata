-- Volunteer Reimbursement & Stipend Tracking Schema
-- Additional tables for QuickBooks/Xero integration

-- Volunteer expense categories table
CREATE TABLE IF NOT EXISTS public.expense_categories (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    quickbooks_account_id VARCHAR(50),
    xero_account_id VARCHAR(50),
    is_reimbursable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Volunteer expenses table
CREATE TABLE IF NOT EXISTS public.volunteer_expenses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    project_id INTEGER,
    category_id UUID REFERENCES public.expense_categories(id),
    description TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    expense_date DATE NOT NULL,
    receipt_url VARCHAR(500),
    receipt_filename VARCHAR(255),
    status VARCHAR(20) DEFAULT 'submitted' CHECK (status IN ('submitted', 'approved', 'rejected', 'reimbursed')),
    approved_by UUID REFERENCES public.users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    approval_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Volunteer stipends table
CREATE TABLE IF NOT EXISTS public.volunteer_stipends (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    project_id INTEGER,
    stipend_type VARCHAR(50) NOT NULL, -- 'hourly', 'fixed', 'event_based'
    amount DECIMAL(10,2) NOT NULL,
    hours_worked DECIMAL(5,2), -- for hourly stipends
    period_start DATE,
    period_end DATE,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'paid')),
    approved_by UUID REFERENCES public.users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    approval_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reimbursement batches table (for grouping multiple expenses)
CREATE TABLE IF NOT EXISTS public.reimbursement_batches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    batch_number VARCHAR(50) UNIQUE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'processed', 'paid')),
    created_by UUID REFERENCES public.users(id),
    approved_by UUID REFERENCES public.users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE,
    quickbooks_bill_id VARCHAR(100),
    xero_bill_id VARCHAR(100),
    payment_reference VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Link expenses to reimbursement batches
CREATE TABLE IF NOT EXISTS public.batch_expenses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    batch_id UUID REFERENCES public.reimbursement_batches(id) ON DELETE CASCADE,
    expense_id UUID REFERENCES public.volunteer_expenses(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- QuickBooks/Xero integration settings
CREATE TABLE IF NOT EXISTS public.accounting_integrations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    organization_id VARCHAR(100) NOT NULL,
    platform VARCHAR(20) NOT NULL CHECK (platform IN ('quickbooks', 'xero')),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    company_id VARCHAR(100),
    company_name VARCHAR(200),
    base_currency VARCHAR(3) DEFAULT 'USD',
    default_expense_account VARCHAR(50),
    default_liability_account VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sync log for tracking data synchronization
CREATE TABLE IF NOT EXISTS public.accounting_sync_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    integration_id UUID REFERENCES public.accounting_integrations(id),
    sync_type VARCHAR(50) NOT NULL, -- 'expense', 'stipend', 'reimbursement'
    entity_id UUID NOT NULL,
    external_id VARCHAR(100),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'success', 'failed', 'retry')),
    error_message TEXT,
    sync_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_volunteer_expenses_user_id ON public.volunteer_expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_volunteer_expenses_status ON public.volunteer_expenses(status);
CREATE INDEX IF NOT EXISTS idx_volunteer_expenses_date ON public.volunteer_expenses(expense_date);
CREATE INDEX IF NOT EXISTS idx_volunteer_stipends_user_id ON public.volunteer_stipends(user_id);
CREATE INDEX IF NOT EXISTS idx_volunteer_stipends_status ON public.volunteer_stipends(status);
CREATE INDEX IF NOT EXISTS idx_reimbursement_batches_user_id ON public.reimbursement_batches(user_id);
CREATE INDEX IF NOT EXISTS idx_reimbursement_batches_status ON public.reimbursement_batches(status);
CREATE INDEX IF NOT EXISTS idx_batch_expenses_batch_id ON public.batch_expenses(batch_id);
CREATE INDEX IF NOT EXISTS idx_accounting_sync_log_entity_id ON public.accounting_sync_log(entity_id);

-- Enable Row Level Security
ALTER TABLE public.expense_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_stipends ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reimbursement_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.batch_expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accounting_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accounting_sync_log ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Users can manage their own expenses
CREATE POLICY "Users can manage own expenses" ON public.volunteer_expenses
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Users can manage their own stipends
CREATE POLICY "Users can manage own stipends" ON public.volunteer_stipends
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Users can manage their own reimbursement batches
CREATE POLICY "Users can manage own reimbursement batches" ON public.reimbursement_batches
    FOR ALL USING (auth.uid()::text = user_id::text);

-- Everyone can read expense categories
CREATE POLICY "Anyone can view expense categories" ON public.expense_categories
    FOR SELECT USING (true);

-- Create triggers for updated_at columns
CREATE TRIGGER update_expense_categories_updated_at BEFORE UPDATE ON public.expense_categories
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_volunteer_expenses_updated_at BEFORE UPDATE ON public.volunteer_expenses
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_volunteer_stipends_updated_at BEFORE UPDATE ON public.volunteer_stipends
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_reimbursement_batches_updated_at BEFORE UPDATE ON public.reimbursement_batches
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_accounting_integrations_updated_at BEFORE UPDATE ON public.accounting_integrations
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Insert default expense categories
INSERT INTO public.expense_categories (name, description, is_reimbursable) VALUES
('Transportation', 'Travel expenses for volunteer activities', true),
('Supplies', 'Materials and supplies purchased for volunteer work', true),
('Meals', 'Meals during volunteer activities', true),
('Training', 'Training materials and courses', true),
('Communication', 'Phone, internet, printing costs', true),
('Equipment', 'Equipment purchased for volunteer work', true),
('Other', 'Miscellaneous volunteer-related expenses', true)
ON CONFLICT DO NOTHING;

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

SELECT 'Volunteer Reimbursement & Stipend Tracking schema created successfully!' AS result;