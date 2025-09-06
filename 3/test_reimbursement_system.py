"""
Test script for Volunteer Reimbursement & Stipend Tracking system
"""
import asyncio
import json
from datetime import datetime, date
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import VolunteerDatabase
from reimbursement_manager import ReimbursementManager, ExpenseItem, StipendItem

async def test_reimbursement_system():
    """Test the reimbursement system functionality"""
    
    print("🧪 Testing Volunteer Reimbursement & Stipend Tracking System")
    print("=" * 60)
    
    # Initialize components
    database = VolunteerDatabase()
    reimbursement_manager = ReimbursementManager(database)
    
    # Test 1: Create expense categories (would be done via SQL)
    print("1. Testing expense categories...")
    categories = await reimbursement_manager.get_expense_categories()
    print(f"   ✅ Found {len(categories)} expense categories")
    
    # Test 2: Submit test expense
    print("2. Testing expense submission...")
    test_expense = ExpenseItem(
        user_id="test-user-123",
        project_id=1,
        category_id="test-category-id",
        description="Test transportation expense for volunteer event",
        amount=25.50,
        expense_date=date.today().isoformat()
    )
    
    expense_id = await reimbursement_manager.submit_expense(test_expense)
    if expense_id:
        print(f"   ✅ Expense submitted successfully: {expense_id}")
    else:
        print("   ❌ Failed to submit expense")
    
    # Test 3: Submit test stipend
    print("3. Testing stipend submission...")
    test_stipend = StipendItem(
        user_id="test-user-123",
        project_id=1,
        stipend_type="hourly",
        amount=15.00,
        hours_worked=2.5,
        period_start=date.today().isoformat(),
        period_end=date.today().isoformat(),
        description="Volunteer coaching session"
    )
    
    stipend_id = await reimbursement_manager.submit_stipend(test_stipend)
    if stipend_id:
        print(f"   ✅ Stipend submitted successfully: {stipend_id}")
    else:
        print("   ❌ Failed to submit stipend")
    
    # Test 4: Get user expenses and stipends
    print("4. Testing retrieval of user data...")
    expenses = await reimbursement_manager.get_user_expenses("test-user-123")
    stipends = await reimbursement_manager.get_user_stipends("test-user-123")
    
    print(f"   ✅ Found {len(expenses)} expenses for user")
    print(f"   ✅ Found {len(stipends)} stipends for user")
    
    # Test 5: Test approval process (if data exists)
    if expense_id:
        print("5. Testing expense approval...")
        approved = await reimbursement_manager.approve_expense(
            expense_id=expense_id,
            approver_id="admin-user-123",
            notes="Approved for reimbursement"
        )
        if approved:
            print("   ✅ Expense approved successfully")
        else:
            print("   ❌ Failed to approve expense")
    
    # Test 6: Get pending approvals
    print("6. Testing pending approvals retrieval...")
    pending = await reimbursement_manager.get_pending_approvals()
    print(f"   ✅ Found {len(pending['expenses'])} pending expenses")
    print(f"   ✅ Found {len(pending['stipends'])} pending stipends")
    
    # Test 7: Get reimbursement summary
    print("7. Testing reimbursement summary...")
    summary = await reimbursement_manager.get_reimbursement_summary(days=30)
    if summary:
        print("   ✅ Generated reimbursement summary:")
        print(f"      - Total submitted expenses: ${summary.get('expenses', {}).get('total_submitted', 0)}")
        print(f"      - Total approved expenses: ${summary.get('expenses', {}).get('total_approved', 0)}")
        print(f"      - Total pending stipends: ${summary.get('stipends', {}).get('total_pending', 0)}")
    else:
        print("   ❌ Failed to generate summary")
    
    print("\n🎉 Test completed!")
    print("\nNext steps:")
    print("- Set up QuickBooks/Xero API credentials in config.py")
    print("- Run the database schema SQL in your Supabase instance")
    print("- Start the FastAPI server with: python main.py")
    print("- Access API documentation at: http://localhost:8000/docs")

def test_api_models():
    """Test the API data models"""
    print("\n📋 Testing API Models...")
    
    # Test expense submission model
    from reimbursement_api import ExpenseSubmission, StipendSubmission
    
    expense_data = {
        "category_id": "transportation",
        "description": "Gas for volunteer event",
        "amount": 15.75,
        "expense_date": "2025-01-15"
    }
    
    try:
        expense = ExpenseSubmission(**expense_data)
        print("   ✅ ExpenseSubmission model validated")
    except Exception as e:
        print(f"   ❌ ExpenseSubmission validation failed: {e}")
    
    # Test stipend submission model
    stipend_data = {
        "stipend_type": "hourly",
        "amount": 20.00,
        "hours_worked": 4.0,
        "period_start": "2025-01-15",
        "period_end": "2025-01-15"
    }
    
    try:
        stipend = StipendSubmission(**stipend_data)
        print("   ✅ StipendSubmission model validated")
    except Exception as e:
        print(f"   ❌ StipendSubmission validation failed: {e}")

def print_api_endpoints():
    """Print available API endpoints"""
    print("\n🔗 Available API Endpoints:")
    print("=" * 40)
    
    endpoints = [
        ("POST", "/api/expenses/submit", "Submit new expense"),
        ("POST", "/api/expenses/upload-receipt/{expense_id}", "Upload receipt"),
        ("GET", "/api/expenses/user/{user_id}", "Get user expenses"),
        ("POST", "/api/expenses/approve", "Approve/reject expense"),
        ("POST", "/api/stipends/submit", "Submit new stipend"),
        ("GET", "/api/stipends/user/{user_id}", "Get user stipends"),
        ("POST", "/api/stipends/approve", "Approve/reject stipend"),
        ("POST", "/api/reimbursements/create-batch", "Create reimbursement batch"),
        ("POST", "/api/reimbursements/process-batch/{batch_id}", "Process batch"),
        ("GET", "/api/admin/pending-approvals", "Get pending approvals"),
        ("GET", "/api/reports/reimbursement-summary", "Get summary report"),
        ("GET", "/api/expense-categories", "Get expense categories"),
        ("POST", "/api/integration/setup", "Setup accounting integration"),
        ("GET", "/api/integration/quickbooks/auth-url", "Get QB auth URL"),
        ("GET", "/api/integration/xero/auth-url", "Get Xero auth URL"),
    ]
    
    for method, endpoint, description in endpoints:
        print(f"   {method:4} {endpoint:<45} - {description}")

if __name__ == "__main__":
    # Test API models first (no async needed)
    test_api_models()
    
    # Print available endpoints
    print_api_endpoints()
    
    # Run async tests
    print("\n" + "="*60)
    print("Running async tests...")
    try:
        asyncio.run(test_reimbursement_system())
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        print("Note: This is expected if database is not configured yet.")
        print("Please set up Supabase credentials and run the SQL schema first.")