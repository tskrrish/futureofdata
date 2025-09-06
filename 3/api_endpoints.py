"""
API Endpoints for A/B Test Framework
Adds A/B testing endpoints to the existing FastAPI application
"""
from fastapi import HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging

from ab_test_framework import ABTestFramework, TestStatus, VariantType, MetricType
from campaign_manager import CampaignManager
from statistical_analysis import ABTestAnalyzer

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class CreateTestRequest(BaseModel):
    name: str
    description: str
    test_type: str  # 'message', 'schedule', 'hybrid'
    start_date: str
    end_date: str
    sample_size: int = 1000
    confidence_level: float = 0.95
    primary_metric: str = 'turnout_rate'
    secondary_metrics: List[str] = []
    message_variants: List[Dict[str, Any]] = []
    schedule_variants: List[Dict[str, Any]] = []
    target_audience_filters: Dict[str, Any] = {}
    created_by: str

class CreateCampaignRequest(BaseModel):
    name: str
    description: str
    channel: str = 'email'
    start_date: str
    end_date: str
    sample_size: int = 1000
    target_audience: Dict[str, Any] = {}
    message_variants: Optional[List[Dict[str, Any]]] = None
    created_by: str

class TrackEventRequest(BaseModel):
    test_id: str
    user_id: str
    event_type: str
    metadata: Dict[str, Any] = {}

class UserAssignmentRequest(BaseModel):
    test_id: str
    user_id: str
    user_profile: Dict[str, Any] = {}

def setup_ab_test_endpoints(app, database=None):
    """Add A/B test endpoints to existing FastAPI app"""
    
    # Initialize A/B test framework
    ab_framework = ABTestFramework(database)
    campaign_manager = CampaignManager(ab_framework, database)
    analyzer = ABTestAnalyzer()
    
    @app.post("/api/ab-tests")
    async def create_ab_test(request: CreateTestRequest) -> JSONResponse:
        """Create a new A/B test"""
        
        try:
            test_config = {
                'name': request.name,
                'description': request.description,
                'test_type': request.test_type,
                'start_date': request.start_date,
                'end_date': request.end_date,
                'sample_size': request.sample_size,
                'confidence_level': request.confidence_level,
                'primary_metric': request.primary_metric,
                'secondary_metrics': request.secondary_metrics,
                'message_variants': request.message_variants,
                'schedule_variants': request.schedule_variants,
                'target_audience_filters': request.target_audience_filters,
                'created_by': request.created_by
            }
            
            test_id = await ab_framework.create_test(test_config)
            
            return JSONResponse(content={
                'success': True,
                'test_id': test_id,
                'message': f'Created A/B test: {request.name}'
            })
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            raise HTTPException(status_code=500, detail="Failed to create A/B test")
    
    @app.post("/api/ab-tests/{test_id}/start")
    async def start_ab_test(test_id: str) -> JSONResponse:
        """Start an A/B test"""
        
        try:
            success = await ab_framework.start_test(test_id)
            
            if success:
                return JSONResponse(content={
                    'success': True,
                    'message': f'Started A/B test {test_id}'
                })
            else:
                raise HTTPException(status_code=400, detail="Failed to start test")
                
        except Exception as e:
            logger.error(f"Error starting test {test_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to start test")
    
    @app.post("/api/ab-tests/assign-user")
    async def assign_user_to_variant(request: UserAssignmentRequest) -> JSONResponse:
        """Assign a user to a test variant"""
        
        try:
            variant_id = ab_framework.assign_participant(
                request.test_id, 
                request.user_id, 
                request.user_profile
            )
            
            if variant_id:
                return JSONResponse(content={
                    'success': True,
                    'variant_id': variant_id,
                    'test_id': request.test_id
                })
            else:
                return JSONResponse(content={
                    'success': False,
                    'message': 'User not eligible for test or test not active'
                })
                
        except Exception as e:
            logger.error(f"Error assigning user to test: {e}")
            raise HTTPException(status_code=500, detail="Failed to assign user")
    
    @app.post("/api/ab-tests/track-event")
    async def track_test_event(request: TrackEventRequest) -> JSONResponse:
        """Track an event for A/B test analysis"""
        
        try:
            await ab_framework.track_event(
                request.test_id,
                request.user_id,
                request.event_type,
                request.metadata
            )
            
            return JSONResponse(content={
                'success': True,
                'message': 'Event tracked successfully'
            })
            
        except Exception as e:
            logger.error(f"Error tracking event: {e}")
            raise HTTPException(status_code=500, detail="Failed to track event")
    
    @app.get("/api/ab-tests/{test_id}/results")
    async def get_test_results(test_id: str) -> JSONResponse:
        """Get statistical results for an A/B test"""
        
        try:
            results = await ab_framework.calculate_results(test_id)
            
            # Convert results to dict format
            results_dict = []
            for result in results:
                result_dict = {
                    'test_id': result.test_id,
                    'variant_id': result.variant_id,
                    'variant_name': result.variant_name,
                    'sample_size': result.sample_size,
                    'primary_metric_value': result.primary_metric_value,
                    'secondary_metrics': result.secondary_metrics,
                    'confidence_interval': result.confidence_interval,
                    'p_value': result.p_value,
                    'is_statistically_significant': result.is_statistically_significant,
                    'lift_percentage': result.lift_percentage,
                    'calculated_at': result.calculated_at.isoformat()
                }
                results_dict.append(result_dict)
            
            return JSONResponse(content={
                'success': True,
                'test_id': test_id,
                'results': results_dict
            })
            
        except Exception as e:
            logger.error(f"Error getting test results: {e}")
            raise HTTPException(status_code=500, detail="Failed to get test results")
    
    @app.get("/api/ab-tests")
    async def list_ab_tests(status: Optional[str] = None) -> JSONResponse:
        """List all A/B tests with optional status filter"""
        
        try:
            tests = []
            for test_id, test_config in ab_framework.active_tests.items():
                if status and test_config.status.value != status:
                    continue
                
                test_dict = {
                    'test_id': test_id,
                    'name': test_config.name,
                    'description': test_config.description,
                    'status': test_config.status.value,
                    'test_type': test_config.test_type.value,
                    'start_date': test_config.start_date.isoformat(),
                    'end_date': test_config.end_date.isoformat(),
                    'sample_size': test_config.sample_size,
                    'primary_metric': test_config.primary_metric.value,
                    'created_by': test_config.created_by,
                    'created_at': test_config.created_at.isoformat()
                }
                tests.append(test_dict)
            
            return JSONResponse(content={
                'success': True,
                'tests': tests,
                'count': len(tests)
            })
            
        except Exception as e:
            logger.error(f"Error listing tests: {e}")
            raise HTTPException(status_code=500, detail="Failed to list tests")
    
    @app.post("/api/campaigns")
    async def create_campaign(request: CreateCampaignRequest) -> JSONResponse:
        """Create a new campaign with A/B testing"""
        
        try:
            campaign_data = {
                'name': request.name,
                'description': request.description,
                'channel': request.channel,
                'start_date': request.start_date,
                'end_date': request.end_date,
                'sample_size': request.sample_size,
                'target_audience': request.target_audience,
                'created_by': request.created_by
            }
            
            if request.message_variants:
                campaign_data['message_variants'] = request.message_variants
            
            campaign_id = await campaign_manager.create_volunteer_campaign(campaign_data)
            
            return JSONResponse(content={
                'success': True,
                'campaign_id': campaign_id,
                'message': f'Created campaign: {request.name}'
            })
            
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            raise HTTPException(status_code=500, detail="Failed to create campaign")
    
    @app.post("/api/campaigns/{campaign_id}/launch")
    async def launch_campaign(campaign_id: str) -> JSONResponse:
        """Launch a campaign"""
        
        try:
            success = await campaign_manager.launch_campaign(campaign_id)
            
            if success:
                return JSONResponse(content={
                    'success': True,
                    'message': f'Launched campaign {campaign_id}'
                })
            else:
                raise HTTPException(status_code=400, detail="Failed to launch campaign")
                
        except Exception as e:
            logger.error(f"Error launching campaign: {e}")
            raise HTTPException(status_code=500, detail="Failed to launch campaign")
    
    @app.post("/api/campaigns/{campaign_id}/send-message")
    async def send_campaign_message(
        campaign_id: str,
        user_id: str,
        user_profile: Dict[str, Any] = {}
    ) -> JSONResponse:
        """Send personalized campaign message to user"""
        
        try:
            success = await campaign_manager.send_personalized_message(
                campaign_id, user_id, user_profile
            )
            
            return JSONResponse(content={
                'success': success,
                'message': 'Message sent' if success else 'Failed to send message'
            })
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise HTTPException(status_code=500, detail="Failed to send message")
    
    @app.post("/api/campaigns/{campaign_id}/track-engagement")
    async def track_campaign_engagement(
        campaign_id: str,
        user_id: str,
        engagement_type: str,
        metadata: Dict[str, Any] = {}
    ) -> JSONResponse:
        """Track user engagement with campaign"""
        
        try:
            await campaign_manager.track_user_engagement(
                campaign_id, user_id, engagement_type, metadata
            )
            
            return JSONResponse(content={
                'success': True,
                'message': f'Tracked {engagement_type} engagement'
            })
            
        except Exception as e:
            logger.error(f"Error tracking engagement: {e}")
            raise HTTPException(status_code=500, detail="Failed to track engagement")
    
    @app.post("/api/campaigns/{campaign_id}/track-registration")
    async def track_volunteer_registration(
        campaign_id: str,
        user_id: str,
        event_details: Dict[str, Any]
    ) -> JSONResponse:
        """Track volunteer registration for event"""
        
        try:
            await campaign_manager.track_volunteer_registration(
                campaign_id, user_id, event_details
            )
            
            return JSONResponse(content={
                'success': True,
                'message': 'Registration tracked'
            })
            
        except Exception as e:
            logger.error(f"Error tracking registration: {e}")
            raise HTTPException(status_code=500, detail="Failed to track registration")
    
    @app.post("/api/campaigns/{campaign_id}/track-attendance")
    async def track_volunteer_attendance(
        campaign_id: str,
        user_id: str,
        attended: bool,
        event_details: Dict[str, Any]
    ) -> JSONResponse:
        """Track volunteer attendance at event"""
        
        try:
            await campaign_manager.track_volunteer_attendance(
                campaign_id, user_id, attended, event_details
            )
            
            return JSONResponse(content={
                'success': True,
                'message': f'Attendance tracked: {"attended" if attended else "no show"}'
            })
            
        except Exception as e:
            logger.error(f"Error tracking attendance: {e}")
            raise HTTPException(status_code=500, detail="Failed to track attendance")
    
    @app.get("/api/campaigns/{campaign_id}/performance")
    async def get_campaign_performance(campaign_id: str) -> JSONResponse:
        """Get campaign performance metrics"""
        
        try:
            performance = await campaign_manager.get_campaign_performance(campaign_id)
            
            return JSONResponse(content={
                'success': True,
                'performance': performance
            })
            
        except Exception as e:
            logger.error(f"Error getting campaign performance: {e}")
            raise HTTPException(status_code=500, detail="Failed to get performance data")
    
    @app.get("/api/campaigns")
    async def list_campaigns() -> JSONResponse:
        """List all campaigns"""
        
        try:
            campaigns = await campaign_manager.get_all_campaigns()
            
            return JSONResponse(content={
                'success': True,
                'campaigns': campaigns,
                'count': len(campaigns)
            })
            
        except Exception as e:
            logger.error(f"Error listing campaigns: {e}")
            raise HTTPException(status_code=500, detail="Failed to list campaigns")
    
    @app.post("/api/ab-tests/{test_id}/analyze")
    async def comprehensive_analysis(test_id: str) -> JSONResponse:
        """Run comprehensive statistical analysis on test data"""
        
        try:
            # Get test data from framework
            results = await ab_framework.calculate_results(test_id)
            
            if not results:
                raise HTTPException(status_code=404, detail="Test not found or no data")
            
            # Prepare data for comprehensive analysis
            control_result = results[0] if results else None
            variant_result = results[1] if len(results) > 1 else None
            
            if not control_result or not variant_result:
                raise HTTPException(status_code=400, detail="Insufficient data for analysis")
            
            # Run comprehensive analysis
            test_data = {
                'control_conversions': int(control_result.sample_size * control_result.primary_metric_value),
                'control_total': control_result.sample_size,
                'variant_conversions': int(variant_result.sample_size * variant_result.primary_metric_value),
                'variant_total': variant_result.sample_size
            }
            
            comprehensive_results = analyzer.comprehensive_analysis(test_data)
            
            return JSONResponse(content={
                'success': True,
                'test_id': test_id,
                'analysis': comprehensive_results
            })
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            raise HTTPException(status_code=500, detail="Analysis failed")
    
    @app.get("/api/ab-tests/dashboard-data")
    async def get_dashboard_data() -> JSONResponse:
        """Get aggregated data for A/B test dashboard"""
        
        try:
            dashboard_data = {
                'active_tests': len([t for t in ab_framework.active_tests.values() if t.status == TestStatus.ACTIVE]),
                'total_tests': len(ab_framework.active_tests),
                'total_participants': sum(len(ab_framework.participant_assignments.get(test_id, [])) 
                                        for test_id in ab_framework.active_tests.keys()),
                'recent_events': len([e for e in ab_framework.test_events 
                                    if (datetime.now() - e.timestamp).days <= 7])
            }
            
            # Get recent test results
            recent_results = []
            for test_id in list(ab_framework.active_tests.keys())[-5:]:  # Last 5 tests
                results = await ab_framework.calculate_results(test_id)
                if results:
                    recent_results.append({
                        'test_id': test_id,
                        'test_name': ab_framework.active_tests[test_id].name,
                        'results': [
                            {
                                'variant_id': r.variant_id,
                                'variant_name': r.variant_name,
                                'metric_value': r.primary_metric_value,
                                'is_significant': r.is_statistically_significant
                            }
                            for r in results
                        ]
                    })
            
            dashboard_data['recent_results'] = recent_results
            
            return JSONResponse(content={
                'success': True,
                'data': dashboard_data
            })
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            raise HTTPException(status_code=500, detail="Failed to get dashboard data")
    
    logger.info("A/B Test API endpoints registered successfully")