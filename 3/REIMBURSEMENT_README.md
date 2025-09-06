# YMCA Volunteer Reimbursement & Stipend Tracking System

A comprehensive solution for tracking volunteer expenses, reimbursements, and stipends with seamless QuickBooks and Xero integration.

## 🚀 Features

### Expense Tracking
- **Expense Submission**: Volunteers can submit expenses with receipts
- **Categorization**: Pre-defined expense categories (Transportation, Supplies, Meals, etc.)
- **Receipt Management**: File upload and storage for expense receipts
- **Approval Workflow**: Multi-stage approval process with notes and comments

### Stipend Management
- **Multiple Stipend Types**: Hourly, fixed amount, and event-based stipends
- **Time Tracking**: Hours worked tracking for hourly stipends
- **Period Management**: Start and end dates for stipend periods
- **Approval Process**: Dedicated approval workflow for stipends

### Batch Processing
- **Reimbursement Batches**: Group multiple approved expenses for processing
- **Batch Status Tracking**: Track batches through approval, processing, and payment stages
- **Accounting Integration**: Automatic sync with QuickBooks or Xero

### Accounting Integration
- **QuickBooks Online**: Full integration with QB Online API
- **Xero**: Complete Xero API integration
- **Automatic Vendor Creation**: Create volunteer vendors automatically
- **Bill Generation**: Generate bills/expense claims in accounting software
- **Sync Logging**: Track all synchronization attempts and errors

### Reporting & Analytics
- **Summary Reports**: Expense and stipend summaries by period
- **Pending Approvals**: Dashboard for items requiring approval
- **User History**: Complete expense/stipend history per volunteer
- **Analytics Tracking**: Built-in analytics for usage patterns

## 📊 Database Schema

The system adds the following tables to the existing YMCA Volunteer PathFinder database:

- `expense_categories` - Predefined expense categories
- `volunteer_expenses` - Individual expense records
- `volunteer_stipends` - Stipend records
- `reimbursement_batches` - Grouped expenses for processing
- `batch_expenses` - Links expenses to batches
- `accounting_integrations` - QB/Xero integration settings
- `accounting_sync_log` - Synchronization audit trail

## 🔧 Installation & Setup

### 1. Database Setup
Run the SQL schema in your Supabase instance:
```bash
# Execute the schema file in Supabase SQL Editor
cat volunteer_reimbursement_schema.sql
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configuration
Copy and configure the settings:
```bash
cp config.example.py config.py
# Edit config.py with your API keys
```

Required configuration:
- Supabase credentials
- QuickBooks OAuth credentials (optional)
- Xero OAuth credentials (optional)

### 4. QuickBooks Setup (Optional)
1. Create a QuickBooks Developer account
2. Register your application
3. Set the redirect URI to: `http://localhost:8000/api/integration/quickbooks/callback`
4. Add credentials to config.py

### 5. Xero Setup (Optional)
1. Create a Xero Developer account
2. Register your application
3. Set the redirect URI to: `http://localhost:8000/api/integration/xero/callback`
4. Add credentials to config.py

## 🌐 API Endpoints

### Expense Management
- `POST /api/expenses/submit` - Submit new expense
- `POST /api/expenses/upload-receipt/{expense_id}` - Upload receipt
- `GET /api/expenses/user/{user_id}` - Get user expenses
- `POST /api/expenses/approve` - Approve/reject expense

### Stipend Management
- `POST /api/stipends/submit` - Submit new stipend
- `GET /api/stipends/user/{user_id}` - Get user stipends
- `POST /api/stipends/approve` - Approve/reject stipend

### Batch Processing
- `POST /api/reimbursements/create-batch` - Create batch from approved expenses
- `POST /api/reimbursements/process-batch/{batch_id}` - Process batch through accounting

### Admin & Reporting
- `GET /api/admin/pending-approvals` - Get pending approvals
- `GET /api/reports/reimbursement-summary` - Get summary statistics
- `GET /api/expense-categories` - Get available categories

### Accounting Integration
- `POST /api/integration/setup` - Setup QB/Xero integration
- `GET /api/integration/quickbooks/auth-url` - Get QB OAuth URL
- `GET /api/integration/xero/auth-url` - Get Xero OAuth URL
- `POST /api/integration/quickbooks/callback` - QB OAuth callback
- `POST /api/integration/xero/callback` - Xero OAuth callback

## 📝 Usage Examples

### Submit an Expense
```python
import requests

expense_data = {
    "category_id": "transportation",
    "description": "Gas for volunteer event",
    "amount": 25.50,
    "expense_date": "2025-01-15"
}

response = requests.post(
    "http://localhost:8000/api/expenses/submit",
    json=expense_data,
    params={"user_id": "volunteer-123"}
)
```

### Submit a Stipend
```python
stipend_data = {
    "stipend_type": "hourly",
    "amount": 15.00,
    "hours_worked": 2.5,
    "period_start": "2025-01-15",
    "period_end": "2025-01-15",
    "description": "Coaching session"
}

response = requests.post(
    "http://localhost:8000/api/stipends/submit",
    json=stipend_data,
    params={"user_id": "volunteer-123"}
)
```

### Approve an Expense
```python
approval_data = {
    "expense_id": "expense-uuid-here",
    "approved": True,
    "notes": "Approved for reimbursement"
}

response = requests.post(
    "http://localhost:8000/api/expenses/approve",
    json=approval_data,
    params={"approver_id": "admin-123"}
)
```

## 🔄 Workflow

### Expense Reimbursement Process
1. **Volunteer submits expense** with receipt
2. **Admin reviews** and approves/rejects
3. **Approved expenses** grouped into batches
4. **Batch processed** through QuickBooks/Xero
5. **Bills/expense claims created** in accounting software
6. **Status updated** to "reimbursed"

### Stipend Process
1. **Volunteer submits stipend** request
2. **Admin reviews** hours and amount
3. **Approved stipends** marked for payment
4. **Payment processed** through normal payroll

## 🔐 Security Features

- **Row Level Security (RLS)**: Users can only access their own data
- **OAuth Integration**: Secure authentication with accounting software
- **Receipt Storage**: Secure file upload and storage
- **Audit Trail**: Complete logging of all actions
- **Token Management**: Automatic token refresh for integrations

## 📊 Analytics & Reporting

The system tracks:
- Expense submission patterns
- Approval times and rates
- Reimbursement volumes
- Integration success rates
- User engagement metrics

## 🧪 Testing

Run the test suite:
```bash
python test_reimbursement_system.py
```

This validates:
- Database connectivity
- API model validation
- Core functionality
- Integration readiness

## 🔧 Development

### File Structure
```
├── volunteer_reimbursement_schema.sql  # Database schema
├── reimbursement_manager.py           # Core business logic
├── quickbooks_integration.py          # QuickBooks API client
├── xero_integration.py               # Xero API client
├── reimbursement_api.py              # FastAPI endpoints
├── test_reimbursement_system.py      # Test suite
└── REIMBURSEMENT_README.md           # This file
```

### Adding New Features
1. Update database schema if needed
2. Extend ReimbursementManager class
3. Add new API endpoints in reimbursement_api.py
4. Update tests and documentation

## 📞 Support

For questions about this implementation:
1. Check the API documentation at `/docs`
2. Review the test suite for usage examples
3. Examine the existing YMCA codebase for patterns
4. Consult QuickBooks/Xero API documentation for integration details

## 🎯 Future Enhancements

Potential improvements:
- Mobile app integration
- Advanced reporting dashboard
- Automated approval rules
- Integration with additional accounting systems
- Receipt OCR for automatic data extraction
- Mileage tracking with GPS
- Multi-currency support
- Budget tracking and alerts

---

This system seamlessly integrates with the existing YMCA Volunteer PathFinder to provide comprehensive expense and stipend management with professional accounting software integration.