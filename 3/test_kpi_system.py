#!/usr/bin/env python3
"""
Test script for KPI Email Reporting System
Tests the core functionality without requiring full application startup
"""
import asyncio
import os
import sys
from datetime import datetime
import logging

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kpi_email_service import KPIEmailService, StakeholderConfig
from kpi_scheduler import KPIScheduler
from database import VolunteerDatabase
from data_processor import VolunteerDataProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_kpi_snapshot_generation():
    """Test KPI snapshot generation"""
    logger.info("=== Testing KPI Snapshot Generation ===")
    
    try:
        # Initialize database and data processor
        database = VolunteerDatabase()
        
        # Use a test data path or create mock data
        test_data_path = "volunteer_test_data.csv"  # This would need to exist
        
        # For testing, we'll use the email service with minimal setup
        kpi_service = KPIEmailService(database)
        
        # Generate a test snapshot with empty data
        snapshot = await kpi_service.generate_kpi_snapshot("current_month", "All")
        
        logger.info(f"Generated KPI snapshot for period: {snapshot.period}")
        logger.info(f"Total hours: {snapshot.total_hours}")
        logger.info(f"Active volunteers: {snapshot.active_volunteers}")
        logger.info(f"Member volunteers: {snapshot.member_volunteers}")
        logger.info(f"Total projects: {snapshot.total_projects}")
        logger.info(f"Generated at: {snapshot.generated_at}")
        
        return True
        
    except Exception as e:
        logger.error(f"KPI snapshot generation test failed: {e}")
        return False

async def test_stakeholder_management():
    """Test stakeholder management functionality"""
    logger.info("=== Testing Stakeholder Management ===")
    
    try:
        database = VolunteerDatabase()
        kpi_service = KPIEmailService(database)
        
        # Test getting initial stakeholders
        initial_stakeholders = kpi_service.get_stakeholders()
        logger.info(f"Initial stakeholders count: {len(initial_stakeholders)}")
        
        # Test adding a new stakeholder
        test_stakeholder = {
            "email": "test.manager@ymca.org",
            "name": "Test Manager",
            "role": "Test Role",
            "report_frequency": "weekly",
            "branches": ["Test Branch"],
            "active": True
        }
        
        success = await kpi_service.add_stakeholder(test_stakeholder)
        if success:
            logger.info("Successfully added test stakeholder")
        else:
            logger.error("Failed to add test stakeholder")
            return False
        
        # Test getting stakeholders after addition
        updated_stakeholders = kpi_service.get_stakeholders()
        logger.info(f"Updated stakeholders count: {len(updated_stakeholders)}")
        
        # Test updating stakeholder
        update_success = await kpi_service.update_stakeholder(
            "test.manager@ymca.org", 
            {"active": False}
        )
        if update_success:
            logger.info("Successfully updated test stakeholder")
        else:
            logger.error("Failed to update test stakeholder")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Stakeholder management test failed: {e}")
        return False

async def test_email_template_rendering():
    """Test email template rendering"""
    logger.info("=== Testing Email Template Rendering ===")
    
    try:
        database = VolunteerDatabase()
        kpi_service = KPIEmailService(database)
        
        # Generate test snapshot
        snapshot = await kpi_service.generate_kpi_snapshot("current_month", "All")
        
        # Test template rendering
        if kpi_service.email_template:
            html_content = kpi_service.email_template.render(kpi=snapshot)
            
            # Basic validation that HTML was generated
            if "<html" in html_content and "KPI Report" in html_content:
                logger.info("Email template rendered successfully")
                logger.info(f"Generated HTML length: {len(html_content)} characters")
                
                # Save test output for inspection
                with open("test_kpi_email_output.html", "w") as f:
                    f.write(html_content)
                logger.info("Test email HTML saved to test_kpi_email_output.html")
                
                return True
            else:
                logger.error("Email template rendering produced invalid HTML")
                return False
        else:
            logger.error("Email template not loaded")
            return False
            
    except Exception as e:
        logger.error(f"Email template rendering test failed: {e}")
        return False

async def test_scheduler_functionality():
    """Test scheduler functionality"""
    logger.info("=== Testing Scheduler Functionality ===")
    
    try:
        # Create test email service
        database = VolunteerDatabase()
        kpi_service = KPIEmailService(database)
        
        # Initialize scheduler
        scheduler = KPIScheduler(kpi_service)
        
        # Test job status
        job_status = scheduler.get_job_status()
        logger.info(f"Default jobs loaded: {len(job_status)}")
        
        for job in job_status:
            logger.info(f"Job: {job['job_id']} - {job['frequency']} at {job['time']}")
        
        # Test adding a custom job
        test_job = {
            "job_id": "test_job",
            "frequency": "daily",
            "time": "12:00",
            "timezone": "US/Eastern",
            "active": False  # Don't activate for test
        }
        
        add_success = scheduler.add_job(test_job)
        if add_success:
            logger.info("Successfully added test job")
        else:
            logger.error("Failed to add test job")
            return False
        
        # Test updating job
        update_success = scheduler.update_job("test_job", {"time": "13:00"})
        if update_success:
            logger.info("Successfully updated test job")
        else:
            logger.error("Failed to update test job")
            return False
        
        # Test deleting job
        delete_success = scheduler.delete_job("test_job")
        if delete_success:
            logger.info("Successfully deleted test job")
        else:
            logger.error("Failed to delete test job")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Scheduler functionality test failed: {e}")
        return False

async def test_api_integration():
    """Test API integration without actually starting server"""
    logger.info("=== Testing API Integration ===")
    
    try:
        # Test that all required components can be imported and initialized
        from kpi_email_service import KPIEmailService, StakeholderConfig, KPISnapshot
        from kpi_scheduler import KPIScheduler
        
        logger.info("All KPI system imports successful")
        
        # Test data classes
        test_stakeholder_config = StakeholderConfig(
            email="test@example.com",
            name="Test User", 
            role="Test",
            report_frequency="daily",
            branches=["all"],
            active=True
        )
        
        logger.info(f"StakeholderConfig created: {test_stakeholder_config.email}")
        
        return True
        
    except Exception as e:
        logger.error(f"API integration test failed: {e}")
        return False

async def run_all_tests():
    """Run all test suites"""
    logger.info("🚀 Starting KPI Email Reporting System Tests")
    
    test_results = {
        "kpi_snapshot_generation": await test_kpi_snapshot_generation(),
        "stakeholder_management": await test_stakeholder_management(),
        "email_template_rendering": await test_email_template_rendering(),
        "scheduler_functionality": await test_scheduler_functionality(),
        "api_integration": await test_api_integration()
    }
    
    logger.info("=== Test Results ===")
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! KPI Email Reporting System is ready.")
    else:
        logger.warning(f"⚠️  {total - passed} test(s) failed. Review the errors above.")
    
    return passed == total

if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n" + "="*60)
        print("KPI EMAIL REPORTING SYSTEM TESTING COMPLETE")
        print("="*60)
        print("✅ All tests passed!")
        print("\nThe system includes:")
        print("- KPI data collection and aggregation")  
        print("- HTML email template generation")
        print("- Stakeholder management")
        print("- Automated scheduling")
        print("- FastAPI endpoints for management")
        print("\nNext steps:")
        print("1. Configure SMTP settings in config/environment")
        print("2. Add real stakeholder email addresses")
        print("3. Test with actual volunteer data")
        print("4. Schedule automated reports")
        exit(0)
    else:
        print("\n❌ Some tests failed. Review the logs above.")
        exit(1)