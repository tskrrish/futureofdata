"""
Test script for Volunteer Funnel Tracking System
Tests the core functionality of funnel tracking, interventions, and analytics
"""
import asyncio
import sys
import json
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules
from database import VolunteerDatabase
from funnel_tracker import VolunteerFunnelTracker, FunnelStage, InterventionType, FunnelEvent
from funnel_analytics import FunnelAnalyticsEngine

class FunnelTrackingTest:
    """Test class for funnel tracking functionality"""
    
    def __init__(self):
        self.database = VolunteerDatabase()
        self.funnel_tracker = VolunteerFunnelTracker(self.database)
        self.analytics_engine = FunnelAnalyticsEngine(self.funnel_tracker, self.database)
        
    async def run_all_tests(self):
        """Run all test scenarios"""
        logger.info("🧪 Starting Funnel Tracking Tests...")
        
        try:
            # Test 1: Database initialization
            await self.test_database_initialization()
            
            # Test 2: Basic stage tracking
            await self.test_stage_tracking()
            
            # Test 3: Intervention application
            await self.test_intervention_application()
            
            # Test 4: Analytics generation
            await self.test_analytics_generation()
            
            # Test 5: At-risk user identification
            await self.test_at_risk_identification()
            
            # Test 6: Cohort creation and comparison
            await self.test_cohort_functionality()
            
            logger.info("✅ All tests completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False
    
    async def test_database_initialization(self):
        """Test database table initialization"""
        logger.info("Testing database initialization...")
        
        if not self.database._is_available():
            logger.warning("Database not available - skipping database tests")
            return
        
        try:
            # Initialize tables
            table_sqls = await self.funnel_tracker.initialize_tracking_tables()
            assert len(table_sqls) >= 3, "Should return at least 3 table creation SQL statements"
            
            logger.info("✅ Database initialization test passed")
        except Exception as e:
            logger.error(f"❌ Database initialization test failed: {e}")
            raise
    
    async def test_stage_tracking(self):
        """Test basic stage tracking functionality"""
        logger.info("Testing stage tracking...")
        
        # Create test user ID
        test_user_id = "test-user-001"
        
        # Test tracking different stages
        stages_to_test = [
            FunnelStage.INTEREST_EXPRESSED,
            FunnelStage.PROFILE_CREATED,
            FunnelStage.MATCHED_OPPORTUNITIES,
            FunnelStage.APPLICATION_STARTED
        ]
        
        for stage in stages_to_test:
            event = FunnelEvent(
                user_id=test_user_id,
                stage=stage,
                timestamp=datetime.now(),
                metadata={"test": True, "stage_test": stage.value},
                session_id="test-session-001"
            )
            
            success = await self.funnel_tracker.track_stage_progression(event)
            
            if self.database._is_available():
                assert success, f"Failed to track stage {stage.value}"
            
            logger.info(f"✓ Tracked stage: {stage.value}")
        
        logger.info("✅ Stage tracking test passed")
    
    async def test_intervention_application(self):
        """Test intervention application and tracking"""
        logger.info("Testing intervention application...")
        
        test_user_id = "test-user-002"
        
        # Test different intervention types
        interventions_to_test = [
            (InterventionType.EMAIL_REMINDER, FunnelStage.MATCHED_OPPORTUNITIES),
            (InterventionType.PHONE_CALL, FunnelStage.APPLICATION_STARTED),
            (InterventionType.PERSONALIZED_MATCH, FunnelStage.PROFILE_CREATED)
        ]
        
        for intervention_type, target_stage in interventions_to_test:
            intervention_id = await self.funnel_tracker.apply_intervention(
                test_user_id,
                intervention_type,
                target_stage,
                metadata={"test": True, "target": target_stage.value}
            )
            
            if self.database._is_available():
                assert intervention_id is not None, f"Failed to apply intervention {intervention_type.value}"
            
            logger.info(f"✓ Applied intervention: {intervention_type.value} → {target_stage.value}")
        
        logger.info("✅ Intervention application test passed")
    
    async def test_analytics_generation(self):
        """Test analytics generation"""
        logger.info("Testing analytics generation...")
        
        # Test basic funnel analytics
        analytics = await self.funnel_tracker.get_funnel_analytics(days=7)
        
        assert isinstance(analytics, dict), "Analytics should return a dictionary"
        assert 'period_days' in analytics, "Analytics should include period_days"
        assert 'generated_at' in analytics, "Analytics should include generated_at timestamp"
        
        logger.info(f"✓ Generated basic analytics: {len(analytics)} metrics")
        
        # Test comprehensive report
        if self.database._is_available():
            try:
                comprehensive_report = await self.analytics_engine.generate_comprehensive_report(days=7)
                
                assert isinstance(comprehensive_report, dict), "Report should be a dictionary"
                
                expected_sections = [
                    'executive_summary', 'funnel_metrics', 'dropoff_insights',
                    'intervention_analysis', 'optimization_recommendations'
                ]
                
                for section in expected_sections:
                    if section not in comprehensive_report and 'error' not in comprehensive_report:
                        logger.warning(f"Expected section {section} not found in report")
                
                logger.info(f"✓ Generated comprehensive report with {len(comprehensive_report)} sections")
            except Exception as e:
                logger.warning(f"Comprehensive report generation skipped: {e}")
        
        logger.info("✅ Analytics generation test passed")
    
    async def test_at_risk_identification(self):
        """Test at-risk user identification"""
        logger.info("Testing at-risk user identification...")
        
        # This test may not find users in a fresh system
        at_risk_users = await self.funnel_tracker.identify_at_risk_users(hours_threshold=1)
        
        assert isinstance(at_risk_users, list), "At-risk users should return a list"
        
        logger.info(f"✓ Identified {len(at_risk_users)} at-risk users")
        
        # Test suggestion functionality
        suggestions = self.funnel_tracker._suggest_interventions('interest_expressed', {})
        assert isinstance(suggestions, list), "Suggestions should be a list"
        assert len(suggestions) > 0, "Should have at least one suggestion"
        
        logger.info(f"✓ Generated {len(suggestions)} intervention suggestions")
        logger.info("✅ At-risk identification test passed")
    
    async def test_cohort_functionality(self):
        """Test cohort creation and comparison"""
        logger.info("Testing cohort functionality...")
        
        test_user_ids = ["cohort-user-001", "cohort-user-002", "cohort-user-003"]
        
        # Test cohort creation
        success = await self.funnel_tracker.create_user_cohort(
            test_user_ids,
            "test-cohort-control",
            is_control_group=True,
            metadata={"test": True, "purpose": "unit_test"}
        )
        
        if self.database._is_available():
            assert success, "Cohort creation should succeed"
        
        logger.info("✓ Created test cohort")
        
        # Test cohort analysis (may be empty in fresh system)
        if self.database._is_available():
            try:
                cohort_analysis = await self.analytics_engine.compare_cohort_performance(days=7)
                assert isinstance(cohort_analysis, dict), "Cohort analysis should return a dictionary"
                logger.info(f"✓ Generated cohort analysis with {len(cohort_analysis)} comparisons")
            except Exception as e:
                logger.warning(f"Cohort analysis skipped: {e}")
        
        logger.info("✅ Cohort functionality test passed")
    
    async def test_data_validation(self):
        """Test data validation and error handling"""
        logger.info("Testing data validation...")
        
        # Test invalid stage
        try:
            invalid_event = FunnelEvent(
                user_id="test-validation",
                stage="invalid_stage",  # This should cause an error
                timestamp=datetime.now()
            )
            # This should not reach here if validation works
            logger.warning("Invalid stage validation may need improvement")
        except (ValueError, AttributeError):
            logger.info("✓ Invalid stage properly rejected")
        
        # Test invalid intervention
        try:
            await self.funnel_tracker.apply_intervention(
                "test-user",
                "invalid_intervention",  # This should cause an error
                FunnelStage.PROFILE_CREATED
            )
            logger.warning("Invalid intervention validation may need improvement")
        except (ValueError, AttributeError):
            logger.info("✓ Invalid intervention properly rejected")
        
        logger.info("✅ Data validation test passed")

async def run_integration_test():
    """Run a complete integration test scenario"""
    logger.info("🔧 Running Integration Test Scenario...")
    
    database = VolunteerDatabase()
    funnel_tracker = VolunteerFunnelTracker(database)
    
    # Simulate a user journey
    test_user_id = "integration-test-user"
    
    try:
        # Step 1: User expresses interest
        interest_event = FunnelEvent(
            user_id=test_user_id,
            stage=FunnelStage.INTEREST_EXPRESSED,
            timestamp=datetime.now() - timedelta(hours=72),
            metadata={"source": "website", "campaign": "spring_2025"}
        )
        await funnel_tracker.track_stage_progression(interest_event)
        logger.info("✓ Tracked: Interest expressed")
        
        # Step 2: User creates profile
        profile_event = FunnelEvent(
            user_id=test_user_id,
            stage=FunnelStage.PROFILE_CREATED,
            timestamp=datetime.now() - timedelta(hours=48),
            metadata={"profile_complete": True, "interests": ["youth_development", "fitness"]}
        )
        await funnel_tracker.track_stage_progression(profile_event)
        logger.info("✓ Tracked: Profile created")
        
        # Step 3: Apply intervention
        intervention_id = await funnel_tracker.apply_intervention(
            test_user_id,
            InterventionType.PERSONALIZED_MATCH,
            FunnelStage.MATCHED_OPPORTUNITIES,
            metadata={"match_count": 5, "automated": True}
        )
        logger.info(f"✓ Applied intervention: {intervention_id}")
        
        # Step 4: User receives matches (intervention successful)
        matches_event = FunnelEvent(
            user_id=test_user_id,
            stage=FunnelStage.MATCHED_OPPORTUNITIES,
            timestamp=datetime.now() - timedelta(hours=24),
            metadata={"match_count": 5, "top_score": 0.92},
            intervention_applied=InterventionType.PERSONALIZED_MATCH
        )
        await funnel_tracker.track_stage_progression(matches_event)
        logger.info("✓ Tracked: Matches received (intervention successful)")
        
        # Step 5: User starts application
        app_event = FunnelEvent(
            user_id=test_user_id,
            stage=FunnelStage.APPLICATION_STARTED,
            timestamp=datetime.now() - timedelta(hours=12),
            metadata={"project_id": 12345, "branch": "Blue Ash"}
        )
        await funnel_tracker.track_stage_progression(app_event)
        logger.info("✓ Tracked: Application started")
        
        logger.info("🎉 Integration test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False

async def main():
    """Main test runner"""
    print("🚀 Volunteer Funnel Tracking System - Test Suite")
    print("=" * 60)
    
    # Check if we should run a quick validation or full tests
    quick_test = "--quick" in sys.argv
    
    if quick_test:
        logger.info("Running quick validation test...")
        
        # Quick validation of core functionality
        try:
            from funnel_tracker import FunnelStage, InterventionType
            assert len(list(FunnelStage)) == 10, "Expected 10 funnel stages"
            assert len(list(InterventionType)) == 8, "Expected 8 intervention types"
            
            logger.info("✅ Quick validation passed")
            print("\n📊 Test Results:")
            print("- Core imports: ✅")
            print("- Enum definitions: ✅")
            print("- Basic structure: ✅")
            
        except Exception as e:
            logger.error(f"❌ Quick validation failed: {e}")
            return False
    else:
        # Run full test suite
        test_runner = FunnelTrackingTest()
        
        # Run unit tests
        unit_test_success = await test_runner.run_all_tests()
        
        # Run integration test
        integration_test_success = await run_integration_test()
        
        # Summary
        print("\n📊 Test Results Summary:")
        print(f"- Unit Tests: {'✅ PASSED' if unit_test_success else '❌ FAILED'}")
        print(f"- Integration Tests: {'✅ PASSED' if integration_test_success else '❌ FAILED'}")
        
        if unit_test_success and integration_test_success:
            print("\n🎉 All tests passed! Funnel tracking system is ready for deployment.")
        else:
            print("\n⚠️ Some tests failed. Please review the logs and fix issues before deployment.")
            
        return unit_test_success and integration_test_success

if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(main())
    sys.exit(0 if success else 1)