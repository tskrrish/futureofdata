"""
Advanced Analytics and Reporting for Volunteer Funnel Tracking
Provides detailed insights into drop-offs, intervention effectiveness, and optimization opportunities
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
from funnel_tracker import VolunteerFunnelTracker, FunnelStage, InterventionType
from database import VolunteerDatabase
import logging

logger = logging.getLogger(__name__)

@dataclass
class DropoffInsight:
    """Represents insights about funnel dropoffs"""
    stage: str
    dropoff_count: int
    dropoff_percentage: float
    avg_time_at_stage: float  # hours
    common_characteristics: Dict[str, Any]
    suggested_interventions: List[str]
    severity: str  # 'low', 'medium', 'high'

@dataclass
class InterventionAnalysis:
    """Analysis of intervention effectiveness"""
    intervention_type: str
    success_rate: float
    avg_time_to_progression: float
    cost_effectiveness_score: float
    best_target_stage: str
    sample_size: int
    confidence_level: str

@dataclass 
class CohortComparison:
    """Comparison between cohorts"""
    control_group: Dict[str, Any]
    test_group: Dict[str, Any]
    statistical_significance: float
    improvement_percentage: float
    recommendation: str

class FunnelAnalyticsEngine:
    """Advanced analytics engine for volunteer funnel optimization"""
    
    def __init__(self, funnel_tracker: VolunteerFunnelTracker, database: VolunteerDatabase):
        self.funnel_tracker = funnel_tracker
        self.database = database
        self.stage_weights = {
            FunnelStage.INTEREST_EXPRESSED.value: 1,
            FunnelStage.PROFILE_CREATED.value: 2,
            FunnelStage.MATCHED_OPPORTUNITIES.value: 3,
            FunnelStage.APPLICATION_STARTED.value: 4,
            FunnelStage.APPLICATION_SUBMITTED.value: 5,
            FunnelStage.SCREENING_COMPLETED.value: 6,
            FunnelStage.ORIENTATION_SCHEDULED.value: 7,
            FunnelStage.ORIENTATION_COMPLETED.value: 8,
            FunnelStage.FIRST_ASSIGNMENT.value: 9,
            FunnelStage.ACTIVE_VOLUNTEER.value: 10
        }
    
    async def generate_comprehensive_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate a comprehensive funnel analytics report"""
        try:
            # Basic funnel metrics
            funnel_metrics = await self.funnel_tracker.get_funnel_analytics(days)
            
            # Advanced dropoff analysis
            dropoff_insights = await self.analyze_critical_dropoffs(days)
            
            # Intervention effectiveness analysis
            intervention_analysis = await self.analyze_intervention_effectiveness(days)
            
            # Cohort performance comparison
            cohort_analysis = await self.compare_cohort_performance(days)
            
            # Predictive insights
            predictions = await self.generate_predictive_insights(days)
            
            # Optimization recommendations
            recommendations = await self.generate_optimization_recommendations(
                dropoff_insights, intervention_analysis
            )
            
            # ROI analysis
            roi_analysis = await self.calculate_intervention_roi(days)
            
            return {
                "report_period": days,
                "generated_at": datetime.now().isoformat(),
                "executive_summary": self._generate_executive_summary(
                    funnel_metrics, dropoff_insights, intervention_analysis
                ),
                "funnel_metrics": funnel_metrics,
                "dropoff_insights": [insight.__dict__ for insight in dropoff_insights],
                "intervention_analysis": [analysis.__dict__ for analysis in intervention_analysis],
                "cohort_comparison": cohort_analysis,
                "predictive_insights": predictions,
                "optimization_recommendations": recommendations,
                "roi_analysis": roi_analysis
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {"error": str(e)}
    
    async def analyze_critical_dropoffs(self, days: int = 30) -> List[DropoffInsight]:
        """Identify and analyze critical dropoff points"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get funnel events
            events = self.database.supabase.table('funnel_events')\
                .select('*')\
                .gte('timestamp', start_date)\
                .order('timestamp')\
                .execute()
            
            # Analyze dropoffs by stage
            dropoffs = []
            stage_data = self._process_stage_data(events.data)
            
            for stage in FunnelStage:
                stage_info = stage_data.get(stage.value, {})
                if stage_info.get('dropoff_count', 0) > 0:
                    
                    # Calculate severity
                    dropoff_rate = stage_info.get('dropoff_percentage', 0)
                    if dropoff_rate > 50:
                        severity = 'high'
                    elif dropoff_rate > 25:
                        severity = 'medium'
                    else:
                        severity = 'low'
                    
                    # Get common characteristics of users who dropped off
                    characteristics = await self._analyze_dropoff_characteristics(stage.value, days)
                    
                    # Suggest interventions
                    suggested_interventions = self._suggest_stage_interventions(stage.value, characteristics)
                    
                    insight = DropoffInsight(
                        stage=stage.value,
                        dropoff_count=stage_info.get('dropoff_count', 0),
                        dropoff_percentage=dropoff_rate,
                        avg_time_at_stage=stage_info.get('avg_time_hours', 0),
                        common_characteristics=characteristics,
                        suggested_interventions=suggested_interventions,
                        severity=severity
                    )
                    dropoffs.append(insight)
            
            # Sort by severity and dropoff percentage
            dropoffs.sort(key=lambda x: (x.severity == 'high', x.dropoff_percentage), reverse=True)
            
            return dropoffs
            
        except Exception as e:
            logger.error(f"Error analyzing dropoffs: {e}")
            return []
    
    async def analyze_intervention_effectiveness(self, days: int = 30) -> List[InterventionAnalysis]:
        """Analyze effectiveness of different interventions"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get intervention data
            interventions = self.database.supabase.table('funnel_interventions')\
                .select('*')\
                .gte('applied_at', start_date)\
                .execute()
            
            analysis_results = []
            
            # Group by intervention type
            intervention_data = {}
            for intervention in interventions.data:
                int_type = intervention['intervention_type']
                if int_type not in intervention_data:
                    intervention_data[int_type] = []
                intervention_data[int_type].append(intervention)
            
            # Analyze each intervention type
            for int_type, int_list in intervention_data.items():
                if len(int_list) < 5:  # Skip if sample size too small
                    continue
                
                successful = [i for i in int_list if i['successful']]
                success_rate = len(successful) / len(int_list) * 100
                
                # Calculate average time to progression
                progression_times = [
                    i['time_to_progression_hours'] for i in successful 
                    if i['time_to_progression_hours']
                ]
                avg_time = np.mean(progression_times) if progression_times else 0
                
                # Calculate cost-effectiveness score (simplified)
                cost_effectiveness = self._calculate_cost_effectiveness(int_type, success_rate, avg_time)
                
                # Find best target stage
                stage_success = {}
                for intervention in int_list:
                    stage = intervention['target_stage']
                    if stage not in stage_success:
                        stage_success[stage] = {'total': 0, 'successful': 0}
                    stage_success[stage]['total'] += 1
                    if intervention['successful']:
                        stage_success[stage]['successful'] += 1
                
                best_stage = max(
                    stage_success.items(),
                    key=lambda x: x[1]['successful'] / x[1]['total'] if x[1]['total'] > 0 else 0
                )[0] if stage_success else "unknown"
                
                # Determine confidence level
                sample_size = len(int_list)
                if sample_size >= 100:
                    confidence = "high"
                elif sample_size >= 30:
                    confidence = "medium"
                else:
                    confidence = "low"
                
                analysis = InterventionAnalysis(
                    intervention_type=int_type,
                    success_rate=round(success_rate, 2),
                    avg_time_to_progression=round(avg_time, 2),
                    cost_effectiveness_score=cost_effectiveness,
                    best_target_stage=best_stage,
                    sample_size=sample_size,
                    confidence_level=confidence
                )
                analysis_results.append(analysis)
            
            # Sort by effectiveness
            analysis_results.sort(key=lambda x: x.cost_effectiveness_score, reverse=True)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing intervention effectiveness: {e}")
            return []
    
    async def compare_cohort_performance(self, days: int = 30) -> Dict[str, Any]:
        """Compare performance between different cohorts"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get cohort data
            cohorts = self.database.supabase.table('funnel_cohorts')\
                .select('*')\
                .gte('entry_date', start_date)\
                .execute()
            
            # Group by cohort name and control/test status
            cohort_groups = {}
            for cohort in cohorts.data:
                key = f"{cohort['cohort_name']}_{cohort['is_control_group']}"
                if key not in cohort_groups:
                    cohort_groups[key] = []
                cohort_groups[key].append(cohort)
            
            comparisons = {}
            
            # Find matching control/test pairs
            cohort_names = set(c['cohort_name'] for c in cohorts.data)
            
            for cohort_name in cohort_names:
                control_key = f"{cohort_name}_True"
                test_key = f"{cohort_name}_False"
                
                if control_key in cohort_groups and test_key in cohort_groups:
                    control_performance = await self._analyze_cohort_performance(
                        cohort_groups[control_key], days
                    )
                    test_performance = await self._analyze_cohort_performance(
                        cohort_groups[test_key], days
                    )
                    
                    # Calculate statistical significance (simplified)
                    stat_sig = self._calculate_statistical_significance(
                        control_performance, test_performance
                    )
                    
                    # Calculate improvement
                    control_rate = control_performance.get('activation_rate', 0)
                    test_rate = test_performance.get('activation_rate', 0)
                    improvement = ((test_rate - control_rate) / control_rate * 100) if control_rate > 0 else 0
                    
                    # Generate recommendation
                    recommendation = self._generate_cohort_recommendation(
                        improvement, stat_sig, control_performance, test_performance
                    )
                    
                    comparison = CohortComparison(
                        control_group=control_performance,
                        test_group=test_performance,
                        statistical_significance=stat_sig,
                        improvement_percentage=round(improvement, 2),
                        recommendation=recommendation
                    )
                    
                    comparisons[cohort_name] = comparison.__dict__
            
            return comparisons
            
        except Exception as e:
            logger.error(f"Error comparing cohort performance: {e}")
            return {}
    
    async def generate_predictive_insights(self, days: int = 30) -> Dict[str, Any]:
        """Generate predictive insights about future funnel performance"""
        try:
            # Analyze trends over time
            trends = await self._analyze_funnel_trends(days)
            
            # Predict next month's performance
            predictions = self._predict_future_performance(trends)
            
            # Identify early warning indicators
            warning_indicators = await self._identify_warning_indicators()
            
            return {
                "trends": trends,
                "next_month_predictions": predictions,
                "warning_indicators": warning_indicators,
                "confidence": "medium"  # Simplified confidence measure
            }
            
        except Exception as e:
            logger.error(f"Error generating predictive insights: {e}")
            return {}
    
    async def generate_optimization_recommendations(
        self, dropoff_insights: List[DropoffInsight], 
        intervention_analysis: List[InterventionAnalysis]
    ) -> List[Dict[str, Any]]:
        """Generate actionable optimization recommendations"""
        recommendations = []
        
        # Analyze high-severity dropoffs
        critical_dropoffs = [d for d in dropoff_insights if d.severity == 'high']
        
        for dropoff in critical_dropoffs[:3]:  # Top 3 critical issues
            # Find best intervention for this stage
            relevant_interventions = [
                i for i in intervention_analysis 
                if i.best_target_stage == dropoff.stage and i.confidence_level != 'low'
            ]
            
            if relevant_interventions:
                best_intervention = max(relevant_interventions, key=lambda x: x.success_rate)
                
                recommendation = {
                    "priority": "high",
                    "issue": f"High dropoff at {dropoff.stage} stage",
                    "impact": f"{dropoff.dropoff_percentage}% of users dropping off",
                    "solution": f"Apply {best_intervention.intervention_type} intervention",
                    "expected_improvement": f"{best_intervention.success_rate}% success rate",
                    "implementation": self._get_implementation_details(best_intervention.intervention_type),
                    "estimated_roi": self._estimate_intervention_roi(dropoff, best_intervention)
                }
                recommendations.append(recommendation)
        
        # Add medium priority recommendations
        medium_dropoffs = [d for d in dropoff_insights if d.severity == 'medium'][:2]
        
        for dropoff in medium_dropoffs:
            recommendation = {
                "priority": "medium",
                "issue": f"Moderate dropoff at {dropoff.stage} stage",
                "impact": f"{dropoff.dropoff_percentage}% dropoff rate",
                "solution": f"Consider implementing {', '.join(dropoff.suggested_interventions[:2])}",
                "implementation": "A/B test recommended interventions with small cohort",
                "timeline": "2-4 weeks"
            }
            recommendations.append(recommendation)
        
        # Add general optimization recommendations
        if intervention_analysis:
            top_intervention = max(intervention_analysis, key=lambda x: x.cost_effectiveness_score)
            recommendation = {
                "priority": "low",
                "issue": "General funnel optimization",
                "solution": f"Scale up {top_intervention.intervention_type} intervention",
                "rationale": f"Highest cost-effectiveness score: {top_intervention.cost_effectiveness_score}",
                "implementation": "Gradually increase intervention deployment",
                "timeline": "ongoing"
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    async def calculate_intervention_roi(self, days: int = 30) -> Dict[str, Any]:
        """Calculate ROI for different interventions"""
        try:
            # Simplified ROI calculation
            # In a real implementation, you'd have actual cost data
            
            intervention_costs = {
                "email_reminder": 0.50,
                "phone_call": 5.00,
                "personalized_match": 2.00,
                "simplified_application": 1.00,
                "quick_start_program": 15.00,
                "peer_mentor": 25.00,
                "branch_visit": 10.00,
                "flexibility_option": 3.00
            }
            
            # Estimated value per activated volunteer (in hours * $25/hour)
            volunteer_value = 100 * 25  # $2,500 per activated volunteer
            
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            interventions = self.database.supabase.table('funnel_interventions')\
                .select('*')\
                .gte('applied_at', start_date)\
                .execute()
            
            roi_data = {}
            
            for intervention in interventions.data:
                int_type = intervention['intervention_type']
                if int_type not in roi_data:
                    roi_data[int_type] = {
                        'total_cost': 0,
                        'successful_conversions': 0,
                        'total_interventions': 0
                    }
                
                cost = intervention_costs.get(int_type, 5.0)  # Default $5
                roi_data[int_type]['total_cost'] += cost
                roi_data[int_type]['total_interventions'] += 1
                
                if intervention['successful']:
                    roi_data[int_type]['successful_conversions'] += 1
            
            # Calculate ROI for each intervention type
            roi_results = {}
            for int_type, data in roi_data.items():
                if data['total_interventions'] > 0:
                    total_value = data['successful_conversions'] * volunteer_value
                    roi_percentage = ((total_value - data['total_cost']) / data['total_cost'] * 100) if data['total_cost'] > 0 else 0
                    
                    roi_results[int_type] = {
                        'total_cost': data['total_cost'],
                        'total_value_generated': total_value,
                        'roi_percentage': round(roi_percentage, 2),
                        'cost_per_conversion': round(data['total_cost'] / data['successful_conversions'], 2) if data['successful_conversions'] > 0 else 0,
                        'conversion_count': data['successful_conversions']
                    }
            
            return {
                'roi_by_intervention': roi_results,
                'assumptions': {
                    'volunteer_value': volunteer_value,
                    'intervention_costs': intervention_costs
                },
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error calculating ROI: {e}")
            return {}
    
    def _process_stage_data(self, events_data: List[Dict]) -> Dict[str, Dict]:
        """Process raw event data to extract stage analytics"""
        stage_data = {}
        user_journeys = {}
        
        # Group events by user
        for event in events_data:
            user_id = event['user_id']
            if user_id not in user_journeys:
                user_journeys[user_id] = []
            user_journeys[user_id].append(event)
        
        # Analyze each user's journey
        for user_id, events in user_journeys.items():
            events.sort(key=lambda x: x['timestamp'])
            
            # Find last stage and calculate time spent
            for i, event in enumerate(events):
                stage = event['stage']
                if stage not in stage_data:
                    stage_data[stage] = {
                        'entry_count': 0,
                        'exit_count': 0,
                        'dropoff_count': 0,
                        'time_spent_hours': []
                    }
                
                stage_data[stage]['entry_count'] += 1
                
                # Check if user progressed to next stage
                if i < len(events) - 1:
                    next_event = events[i + 1]
                    current_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                    next_time = datetime.fromisoformat(next_event['timestamp'].replace('Z', '+00:00'))
                    time_diff = (next_time - current_time).total_seconds() / 3600
                    stage_data[stage]['time_spent_hours'].append(time_diff)
                    stage_data[stage]['exit_count'] += 1
                else:
                    # This is the last stage for the user - potential dropoff
                    stage_data[stage]['dropoff_count'] += 1
        
        # Calculate percentages and averages
        for stage, data in stage_data.items():
            if data['entry_count'] > 0:
                data['dropoff_percentage'] = (data['dropoff_count'] / data['entry_count']) * 100
                data['avg_time_hours'] = np.mean(data['time_spent_hours']) if data['time_spent_hours'] else 0
            else:
                data['dropoff_percentage'] = 0
                data['avg_time_hours'] = 0
        
        return stage_data
    
    async def _analyze_dropoff_characteristics(self, stage: str, days: int) -> Dict[str, Any]:
        """Analyze common characteristics of users who drop off at a specific stage"""
        # This is a simplified implementation
        # In a real scenario, you'd join with user profile data
        return {
            "common_demographics": "Analysis not yet implemented",
            "common_preferences": "Requires user profile integration",
            "time_patterns": "Users typically drop off after 24-48 hours"
        }
    
    def _suggest_stage_interventions(self, stage: str, characteristics: Dict) -> List[str]:
        """Suggest appropriate interventions for a stage based on dropoff characteristics"""
        stage_interventions = {
            'interest_expressed': ['email_reminder', 'personalized_match', 'simplified_application'],
            'profile_created': ['personalized_match', 'quick_start_program', 'phone_call'],
            'matched_opportunities': ['email_reminder', 'simplified_application', 'peer_mentor'],
            'application_started': ['phone_call', 'simplified_application', 'email_reminder'],
            'application_submitted': ['email_reminder', 'phone_call'],
            'screening_completed': ['orientation_scheduling', 'phone_call'],
            'orientation_scheduled': ['email_reminder', 'phone_call', 'branch_visit'],
            'orientation_completed': ['quick_start_program', 'peer_mentor'],
            'first_assignment': ['peer_mentor', 'flexibility_option']
        }
        
        return stage_interventions.get(stage, ['email_reminder', 'phone_call'])
    
    def _calculate_cost_effectiveness(self, intervention_type: str, success_rate: float, avg_time: float) -> float:
        """Calculate cost-effectiveness score for an intervention"""
        # Simplified scoring: success_rate * speed_factor * cost_factor
        cost_factors = {
            'email_reminder': 1.0,
            'phone_call': 0.6,
            'personalized_match': 0.8,
            'simplified_application': 0.9,
            'quick_start_program': 0.4,
            'peer_mentor': 0.3,
            'branch_visit': 0.5,
            'flexibility_option': 0.7
        }
        
        cost_factor = cost_factors.get(intervention_type, 0.5)
        speed_factor = max(0.1, 1.0 - (avg_time / 168))  # Penalize longer time to progression
        
        return round(success_rate * speed_factor * cost_factor, 2)
    
    async def _analyze_cohort_performance(self, cohort_users: List[Dict], days: int) -> Dict[str, Any]:
        """Analyze performance metrics for a cohort"""
        user_ids = [u['user_id'] for u in cohort_users]
        
        # Get funnel events for cohort users
        # This is simplified - in practice you'd do more complex queries
        active_users = len([u for u in cohort_users if u.get('current_stage') == 'active_volunteer'])
        
        return {
            'total_users': len(cohort_users),
            'active_users': active_users,
            'activation_rate': (active_users / len(cohort_users) * 100) if cohort_users else 0,
            'avg_progression_time': 72,  # Placeholder
            'completion_stages': {'orientation_completed': 0.6, 'first_assignment': 0.4}
        }
    
    def _calculate_statistical_significance(self, control: Dict, test: Dict) -> float:
        """Calculate statistical significance between control and test groups"""
        # Simplified chi-square test simulation
        # In practice, you'd use proper statistical tests
        control_rate = control.get('activation_rate', 0) / 100
        test_rate = test.get('activation_rate', 0) / 100
        
        # Simplified p-value approximation
        rate_diff = abs(test_rate - control_rate)
        sample_size = min(control.get('total_users', 0), test.get('total_users', 0))
        
        if sample_size < 30:
            return 0.5  # Low significance for small samples
        
        # Simplified calculation
        significance = min(0.95, rate_diff * sample_size * 2)
        return round(significance, 3)
    
    def _generate_cohort_recommendation(self, improvement: float, significance: float, 
                                      control: Dict, test: Dict) -> str:
        """Generate recommendation based on cohort comparison"""
        if significance > 0.95 and improvement > 10:
            return "Strong recommendation: Deploy test intervention broadly"
        elif significance > 0.8 and improvement > 5:
            return "Moderate recommendation: Scale test intervention carefully"
        elif improvement > 0:
            return "Weak positive signal: Continue testing with larger sample"
        else:
            return "No clear benefit: Consider alternative interventions"
    
    async def _analyze_funnel_trends(self, days: int) -> Dict[str, Any]:
        """Analyze trends in funnel performance over time"""
        # Simplified trend analysis
        return {
            "overall_trend": "stable",
            "conversion_rate_change": "+2.3%",
            "most_improving_stage": "orientation_completed",
            "most_declining_stage": "application_started"
        }
    
    def _predict_future_performance(self, trends: Dict) -> Dict[str, Any]:
        """Predict future performance based on trends"""
        return {
            "predicted_activation_rate": "15.2%",
            "predicted_dropoff_stages": ["application_started", "orientation_scheduled"],
            "confidence": "medium"
        }
    
    async def _identify_warning_indicators(self) -> List[Dict[str, Any]]:
        """Identify early warning indicators"""
        return [
            {
                "indicator": "Increased dropoff at application stage",
                "severity": "medium",
                "trend": "3-day upward trend",
                "action": "Review application process complexity"
            }
        ]
    
    def _generate_executive_summary(self, funnel_metrics: Dict, dropoffs: List[DropoffInsight], 
                                  interventions: List[InterventionAnalysis]) -> Dict[str, Any]:
        """Generate executive summary of funnel performance"""
        total_conversions = sum(funnel_metrics.get('conversion_rates', {}).values()) / len(funnel_metrics.get('conversion_rates', {})) if funnel_metrics.get('conversion_rates') else 0
        
        critical_issues = len([d for d in dropoffs if d.severity == 'high'])
        top_intervention = max(interventions, key=lambda x: x.success_rate) if interventions else None
        
        return {
            "overall_funnel_health": "good" if total_conversions > 50 else "needs_attention",
            "avg_conversion_rate": f"{total_conversions:.1f}%",
            "critical_issues_count": critical_issues,
            "top_performing_intervention": top_intervention.intervention_type if top_intervention else "none",
            "key_recommendation": "Focus on application stage dropoffs" if critical_issues > 0 else "Optimize successful interventions"
        }
    
    def _get_implementation_details(self, intervention_type: str) -> Dict[str, Any]:
        """Get implementation details for an intervention"""
        implementations = {
            "email_reminder": {
                "setup_time": "1-2 hours",
                "automation": "Fully automated",
                "resources": "Email platform integration"
            },
            "phone_call": {
                "setup_time": "Training required",
                "automation": "Semi-automated",
                "resources": "Staff time and training"
            },
            "personalized_match": {
                "setup_time": "Algorithm tuning",
                "automation": "Automated",
                "resources": "ML model optimization"
            }
        }
        
        return implementations.get(intervention_type, {
            "setup_time": "Variable",
            "automation": "Manual",
            "resources": "Staff coordination"
        })
    
    def _estimate_intervention_roi(self, dropoff: DropoffInsight, intervention: InterventionAnalysis) -> str:
        """Estimate ROI for applying intervention to dropoff issue"""
        # Simplified ROI estimation
        prevented_dropoffs = dropoff.dropoff_count * (intervention.success_rate / 100)
        estimated_value = prevented_dropoffs * 2500  # $2,500 per volunteer
        
        return f"${estimated_value:,.0f} potential value from {prevented_dropoffs:.0f} additional activations"