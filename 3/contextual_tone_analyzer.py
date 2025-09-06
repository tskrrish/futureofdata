"""
Contextual Tone Analysis Module
Analyzes user context, interaction history, and volunteer data to determine 
optimal tone and messaging approach for personalized outreach
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from email_sms_drafting import MessageTone, PersonalizationContext, MessageContext, OutreachPurpose


class EngagementPattern(Enum):
    HIGHLY_ENGAGED = "highly_engaged"
    CONSISTENTLY_ACTIVE = "consistently_active"
    SPORADIC = "sporadic"
    DECLINING = "declining"
    DORMANT = "dormant"
    NEW_UNKNOWN = "new_unknown"


class CommunicationStyle(Enum):
    FORMAL = "formal"
    CASUAL = "casual"
    ENTHUSIASTIC = "enthusiastic"
    SUPPORTIVE = "supportive"
    DIRECT = "direct"
    NURTURING = "nurturing"


class ResponsivenessLevel(Enum):
    HIGHLY_RESPONSIVE = "highly_responsive"
    MODERATELY_RESPONSIVE = "moderately_responsive"
    SLOW_RESPONDER = "slow_responder"
    RARELY_RESPONDS = "rarely_responds"
    UNKNOWN = "unknown"


@dataclass
class ToneAnalysis:
    """Results of contextual tone analysis"""
    recommended_tone: MessageTone
    communication_style: CommunicationStyle
    engagement_pattern: EngagementPattern
    responsiveness_level: ResponsivenessLevel
    confidence_score: float  # 0-1, how confident we are in the recommendation
    reasoning: List[str]  # Explanations for the recommendation
    alternative_tones: List[MessageTone]  # Other viable options
    personalization_opportunities: List[str]
    risk_factors: List[str]  # Things to avoid or be careful about
    optimal_message_length: str  # "short", "medium", "long"
    emoji_recommendation: str  # "none", "minimal", "moderate", "frequent"


class ContextualToneAnalyzer:
    """Analyzes user context to determine optimal tone and messaging approach"""
    
    def __init__(self):
        self.engagement_weights = {
            'recent_activity': 0.3,
            'frequency_pattern': 0.25,
            'response_history': 0.2,
            'volunteer_duration': 0.15,
            'interaction_quality': 0.1
        }
        
    def analyze_tone(
        self,
        person_context: PersonalizationContext,
        message_purpose: OutreachPurpose,
        interaction_history: Optional[List[Dict]] = None,
        volunteer_data: Optional[Dict[str, Any]] = None
    ) -> ToneAnalysis:
        """Perform comprehensive tone analysis based on available context"""
        
        # Analyze engagement pattern
        engagement_pattern = self._analyze_engagement_pattern(
            person_context, interaction_history, volunteer_data
        )
        
        # Analyze responsiveness
        responsiveness_level = self._analyze_responsiveness(
            person_context, interaction_history
        )
        
        # Determine communication style preferences
        communication_style = self._determine_communication_style(
            person_context, engagement_pattern, responsiveness_level
        )
        
        # Recommend primary tone
        recommended_tone = self._recommend_primary_tone(
            person_context, message_purpose, engagement_pattern, 
            communication_style, responsiveness_level
        )
        
        # Calculate confidence
        confidence_score = self._calculate_confidence_score(
            person_context, interaction_history
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            person_context, engagement_pattern, communication_style,
            recommended_tone, message_purpose
        )
        
        # Get alternative options
        alternative_tones = self._get_alternative_tones(
            recommended_tone, engagement_pattern, communication_style
        )
        
        # Identify personalization opportunities
        personalization_opportunities = self._identify_personalization_opportunities(
            person_context, volunteer_data
        )
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(
            person_context, engagement_pattern, responsiveness_level
        )
        
        # Determine optimal message characteristics
        message_length = self._recommend_message_length(
            engagement_pattern, communication_style, message_purpose
        )
        
        emoji_recommendation = self._recommend_emoji_usage(
            person_context, engagement_pattern, communication_style
        )
        
        return ToneAnalysis(
            recommended_tone=recommended_tone,
            communication_style=communication_style,
            engagement_pattern=engagement_pattern,
            responsiveness_level=responsiveness_level,
            confidence_score=confidence_score,
            reasoning=reasoning,
            alternative_tones=alternative_tones,
            personalization_opportunities=personalization_opportunities,
            risk_factors=risk_factors,
            optimal_message_length=message_length,
            emoji_recommendation=emoji_recommendation
        )
    
    def _analyze_engagement_pattern(
        self,
        person_context: PersonalizationContext,
        interaction_history: Optional[List[Dict]],
        volunteer_data: Optional[Dict[str, Any]]
    ) -> EngagementPattern:
        """Analyze the person's engagement pattern with YMCA"""
        
        # If no data available, assume new/unknown
        if not person_context.volunteer_history and not interaction_history:
            return EngagementPattern.NEW_UNKNOWN
        
        engagement_score = 0
        factors = 0
        
        # Analyze volunteer history
        if person_context.volunteer_history:
            history = person_context.volunteer_history
            
            # Recent activity (last 3 months)
            total_hours = history.get('total_hours', 0)
            sessions = history.get('sessions', 0)
            
            if total_hours > 50:
                engagement_score += 3
            elif total_hours > 20:
                engagement_score += 2
            elif total_hours > 5:
                engagement_score += 1
            factors += 1
            
            # Session frequency
            if sessions > 20:
                engagement_score += 3
            elif sessions > 10:
                engagement_score += 2
            elif sessions > 3:
                engagement_score += 1
            factors += 1
            
            # Project diversity
            unique_projects = history.get('unique_projects', 0)
            if unique_projects > 5:
                engagement_score += 2
            elif unique_projects > 2:
                engagement_score += 1
            factors += 1
        
        # Analyze interaction history
        if interaction_history:
            recent_interactions = [
                i for i in interaction_history 
                if self._is_recent(i.get('date'), days=90)
            ]
            
            if len(recent_interactions) > 10:
                engagement_score += 2
            elif len(recent_interactions) > 3:
                engagement_score += 1
            factors += 1
        
        # Calculate average engagement
        if factors == 0:
            return EngagementPattern.NEW_UNKNOWN
            
        avg_engagement = engagement_score / factors
        
        if avg_engagement >= 2.5:
            return EngagementPattern.HIGHLY_ENGAGED
        elif avg_engagement >= 2.0:
            return EngagementPattern.CONSISTENTLY_ACTIVE
        elif avg_engagement >= 1.0:
            return EngagementPattern.SPORADIC
        else:
            # Check if this is declining vs dormant
            if person_context.volunteer_history:
                last_date = person_context.volunteer_history.get('last_date')
                if last_date and self._is_recent(last_date, days=180):
                    return EngagementPattern.DECLINING
                else:
                    return EngagementPattern.DORMANT
            return EngagementPattern.NEW_UNKNOWN
    
    def _analyze_responsiveness(
        self,
        person_context: PersonalizationContext,
        interaction_history: Optional[List[Dict]]
    ) -> ResponsivenessLevel:
        """Analyze how responsive the person typically is to communications"""
        
        if not interaction_history:
            return ResponsivenessLevel.UNKNOWN
        
        response_interactions = [
            i for i in interaction_history 
            if i.get('type') in ['email_response', 'form_submission', 'phone_call_returned', 'event_rsvp']
        ]
        
        total_outreach = len([
            i for i in interaction_history 
            if i.get('type') in ['email_sent', 'sms_sent', 'phone_call_made', 'event_invited']
        ])
        
        if total_outreach == 0:
            return ResponsivenessLevel.UNKNOWN
        
        response_rate = len(response_interactions) / total_outreach
        
        # Also consider response timing if available
        quick_responses = len([
            i for i in response_interactions 
            if i.get('response_time_hours', 999) <= 24
        ])
        
        quick_response_rate = quick_responses / len(response_interactions) if response_interactions else 0
        
        # Calculate overall responsiveness
        if response_rate >= 0.7 and quick_response_rate >= 0.5:
            return ResponsivenessLevel.HIGHLY_RESPONSIVE
        elif response_rate >= 0.4:
            return ResponsivenessLevel.MODERATELY_RESPONSIVE
        elif response_rate >= 0.2:
            return ResponsivenessLevel.SLOW_RESPONDER
        else:
            return ResponsivenessLevel.RARELY_RESPONDS
    
    def _determine_communication_style(
        self,
        person_context: PersonalizationContext,
        engagement_pattern: EngagementPattern,
        responsiveness_level: ResponsivenessLevel
    ) -> CommunicationStyle:
        """Determine preferred communication style based on context"""
        
        # Age-based preferences
        if person_context.age:
            if person_context.age >= 65:
                return CommunicationStyle.FORMAL
            elif person_context.age <= 30:
                return CommunicationStyle.CASUAL
        
        # Engagement-based preferences
        if engagement_pattern == EngagementPattern.HIGHLY_ENGAGED:
            return CommunicationStyle.ENTHUSIASTIC
        elif engagement_pattern in [EngagementPattern.DECLINING, EngagementPattern.DORMANT]:
            return CommunicationStyle.SUPPORTIVE
        elif engagement_pattern == EngagementPattern.NEW_UNKNOWN:
            return CommunicationStyle.NURTURING
        
        # Responsiveness-based preferences
        if responsiveness_level == ResponsivenessLevel.HIGHLY_RESPONSIVE:
            return CommunicationStyle.DIRECT
        elif responsiveness_level == ResponsivenessLevel.RARELY_RESPONDS:
            return CommunicationStyle.ENTHUSIASTIC
        
        # Default
        return CommunicationStyle.SUPPORTIVE
    
    def _recommend_primary_tone(
        self,
        person_context: PersonalizationContext,
        message_purpose: OutreachPurpose,
        engagement_pattern: EngagementPattern,
        communication_style: CommunicationStyle,
        responsiveness_level: ResponsivenessLevel
    ) -> MessageTone:
        """Recommend the primary tone for the message"""
        
        # Purpose-driven tone selection
        purpose_tone_map = {
            OutreachPurpose.WELCOME_NEW: MessageTone.WELCOMING,
            OutreachPurpose.APPRECIATION: MessageTone.APPRECIATION,
            OutreachPurpose.RE_ENGAGEMENT: MessageTone.ENCOURAGING,
            OutreachPurpose.REMINDER: MessageTone.FOLLOW_UP,
            OutreachPurpose.UPDATE: MessageTone.INFORMATIVE,
        }
        
        base_tone = purpose_tone_map.get(message_purpose, MessageTone.WELCOMING)
        
        # Adjust based on engagement pattern
        if engagement_pattern == EngagementPattern.HIGHLY_ENGAGED:
            if base_tone in [MessageTone.WELCOMING, MessageTone.INFORMATIVE]:
                return MessageTone.PERSONALIZED
        elif engagement_pattern in [EngagementPattern.DECLINING, EngagementPattern.DORMANT]:
            if base_tone != MessageTone.APPRECIATION:
                return MessageTone.ENCOURAGING
        elif engagement_pattern == EngagementPattern.NEW_UNKNOWN:
            if base_tone not in [MessageTone.WELCOMING, MessageTone.APPRECIATION]:
                return MessageTone.WELCOMING
        
        # Adjust based on communication style
        if communication_style == CommunicationStyle.ENTHUSIASTIC:
            if base_tone in [MessageTone.INFORMATIVE, MessageTone.FOLLOW_UP]:
                return MessageTone.ENCOURAGING
        elif communication_style == CommunicationStyle.FORMAL:
            if base_tone in [MessageTone.ENCOURAGING, MessageTone.WELCOMING]:
                return MessageTone.INFORMATIVE
        
        return base_tone
    
    def _calculate_confidence_score(
        self,
        person_context: PersonalizationContext,
        interaction_history: Optional[List[Dict]]
    ) -> float:
        """Calculate confidence in tone recommendation (0-1)"""
        
        confidence = 0.0
        factors = 0
        
        # Data completeness factors
        if person_context.name:
            confidence += 0.1
            factors += 1
        
        if person_context.age:
            confidence += 0.1
            factors += 1
        
        if person_context.volunteer_history:
            # More complete history = higher confidence
            history = person_context.volunteer_history
            if history.get('total_hours', 0) > 10:
                confidence += 0.2
            else:
                confidence += 0.1
            factors += 1
        
        if person_context.preferences:
            confidence += 0.15
            factors += 1
        
        if interaction_history and len(interaction_history) >= 3:
            confidence += 0.2
            factors += 1
        elif interaction_history:
            confidence += 0.1
            factors += 1
        
        if person_context.engagement_level in ['active', 'champion']:
            confidence += 0.15
            factors += 1
        
        # Calculate average and normalize
        if factors == 0:
            return 0.3  # Low confidence with no data
        
        avg_confidence = confidence / factors
        return min(avg_confidence * factors / 6, 1.0)  # Normalize to reasonable scale
    
    def _generate_reasoning(
        self,
        person_context: PersonalizationContext,
        engagement_pattern: EngagementPattern,
        communication_style: CommunicationStyle,
        recommended_tone: MessageTone,
        message_purpose: OutreachPurpose
    ) -> List[str]:
        """Generate human-readable reasoning for tone recommendation"""
        
        reasoning = []
        
        # Engagement-based reasoning
        engagement_reasons = {
            EngagementPattern.HIGHLY_ENGAGED: "User shows high engagement with consistent volunteer activity",
            EngagementPattern.CONSISTENTLY_ACTIVE: "User maintains regular volunteer participation",
            EngagementPattern.SPORADIC: "User has intermittent volunteer activity",
            EngagementPattern.DECLINING: "User's volunteer activity has decreased recently",
            EngagementPattern.DORMANT: "User hasn't been active recently but has volunteer history",
            EngagementPattern.NEW_UNKNOWN: "New user with limited volunteer history available"
        }
        
        reasoning.append(engagement_reasons[engagement_pattern])
        
        # Age-based reasoning
        if person_context.age:
            if person_context.age >= 65:
                reasoning.append("Older demographic typically prefers formal, respectful communication")
            elif person_context.age <= 30:
                reasoning.append("Younger demographic typically responds well to casual, enthusiastic tone")
            else:
                reasoning.append("Mid-range age suggests balanced communication approach")
        
        # History-based reasoning
        if person_context.volunteer_history:
            history = person_context.volunteer_history
            hours = history.get('total_hours', 0)
            if hours > 50:
                reasoning.append("Extensive volunteer history indicates strong commitment to organization")
            elif hours > 10:
                reasoning.append("Moderate volunteer experience suggests familiarity with organization")
        
        # Membership-based reasoning
        if person_context.is_ymca_member:
            reasoning.append("YMCA membership indicates existing relationship and trust")
        
        # Purpose-based reasoning
        purpose_reasons = {
            OutreachPurpose.WELCOME_NEW: "New user welcome requires warm, inclusive tone",
            OutreachPurpose.VOLUNTEER_MATCH: "Opportunity matching benefits from personalized approach",
            OutreachPurpose.APPRECIATION: "Recognition requires heartfelt, appreciative tone",
            OutreachPurpose.RE_ENGAGEMENT: "Re-engagement needs encouraging, motivational approach",
            OutreachPurpose.REMINDER: "Reminders work best with supportive, helpful tone"
        }
        
        if message_purpose in purpose_reasons:
            reasoning.append(purpose_reasons[message_purpose])
        
        return reasoning
    
    def _get_alternative_tones(
        self,
        primary_tone: MessageTone,
        engagement_pattern: EngagementPattern,
        communication_style: CommunicationStyle
    ) -> List[MessageTone]:
        """Get alternative viable tone options"""
        
        alternatives = []
        
        # Get complementary tones based on primary
        tone_alternatives = {
            MessageTone.WELCOMING: [MessageTone.ENCOURAGING, MessageTone.PERSONALIZED],
            MessageTone.ENCOURAGING: [MessageTone.WELCOMING, MessageTone.APPRECIATION],
            MessageTone.INFORMATIVE: [MessageTone.FOLLOW_UP, MessageTone.WELCOMING],
            MessageTone.URGENT: [MessageTone.ENCOURAGING, MessageTone.INFORMATIVE],
            MessageTone.APPRECIATION: [MessageTone.ENCOURAGING, MessageTone.PERSONALIZED],
            MessageTone.FOLLOW_UP: [MessageTone.INFORMATIVE, MessageTone.ENCOURAGING],
            MessageTone.PERSONALIZED: [MessageTone.WELCOMING, MessageTone.APPRECIATION]
        }
        
        alternatives.extend(tone_alternatives.get(primary_tone, []))
        
        # Add engagement-specific alternatives
        if engagement_pattern == EngagementPattern.HIGHLY_ENGAGED:
            if MessageTone.PERSONALIZED not in alternatives:
                alternatives.append(MessageTone.PERSONALIZED)
        
        # Remove duplicates and primary tone
        alternatives = [t for t in alternatives if t != primary_tone]
        return alternatives[:2]  # Return top 2 alternatives
    
    def _identify_personalization_opportunities(
        self,
        person_context: PersonalizationContext,
        volunteer_data: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Identify specific personalization opportunities"""
        
        opportunities = []
        
        if person_context.name:
            opportunities.append("Use person's name in greeting and throughout message")
        
        if person_context.volunteer_history:
            history = person_context.volunteer_history
            if history.get('total_hours', 0) > 0:
                opportunities.append(f"Reference their {history['total_hours']} volunteer hours")
            
            if history.get('top_categories'):
                categories = list(history['top_categories'].keys())[:2]
                opportunities.append(f"Reference their interest in {', '.join(categories)}")
        
        if person_context.member_branch:
            opportunities.append(f"Reference their connection to {person_context.member_branch} branch")
        
        if person_context.preferences:
            prefs = person_context.preferences
            if prefs.get('interests'):
                opportunities.append("Align message with their stated interests")
            if prefs.get('location_preference'):
                opportunities.append("Reference their preferred volunteer location")
        
        if person_context.age:
            if person_context.age <= 30:
                opportunities.append("Use age-appropriate language and references")
            elif person_context.age >= 65:
                opportunities.append("Acknowledge their experience and wisdom")
        
        return opportunities
    
    def _identify_risk_factors(
        self,
        person_context: PersonalizationContext,
        engagement_pattern: EngagementPattern,
        responsiveness_level: ResponsivenessLevel
    ) -> List[str]:
        """Identify potential risks or things to avoid"""
        
        risks = []
        
        if engagement_pattern == EngagementPattern.DECLINING:
            risks.append("Avoid overwhelming with too many requests")
            risks.append("Don't be too pushy about immediate commitment")
        
        if engagement_pattern == EngagementPattern.DORMANT:
            risks.append("Don't assume they remember recent YMCA changes")
            risks.append("Avoid referencing outdated volunteer programs")
        
        if responsiveness_level == ResponsivenessLevel.RARELY_RESPONDS:
            risks.append("Keep message concise and action-focused")
            risks.append("Avoid lengthy explanations or complex requests")
        
        if person_context.age and person_context.age >= 70:
            risks.append("Avoid excessive informal language or slang")
            risks.append("Don't use too many emojis or modern communication styles")
        
        if not person_context.volunteer_history:
            risks.append("Don't assume familiarity with YMCA volunteer processes")
            risks.append("Avoid volunteer-specific jargon or acronyms")
        
        return risks
    
    def _recommend_message_length(
        self,
        engagement_pattern: EngagementPattern,
        communication_style: CommunicationStyle,
        message_purpose: OutreachPurpose
    ) -> str:
        """Recommend optimal message length"""
        
        # Engagement-based recommendations
        if engagement_pattern == EngagementPattern.HIGHLY_ENGAGED:
            return "medium"  # Can handle more detailed messages
        elif engagement_pattern in [EngagementPattern.DECLINING, EngagementPattern.DORMANT]:
            return "short"  # Keep it brief to re-engage
        elif engagement_pattern == EngagementPattern.NEW_UNKNOWN:
            return "medium"  # Need enough info to orient them
        
        # Style-based recommendations
        if communication_style == CommunicationStyle.DIRECT:
            return "short"
        elif communication_style == CommunicationStyle.FORMAL:
            return "long"
        
        # Purpose-based recommendations
        if message_purpose in [OutreachPurpose.REMINDER, OutreachPurpose.URGENT]:
            return "short"
        elif message_purpose in [OutreachPurpose.WELCOME_NEW, OutreachPurpose.UPDATE]:
            return "long"
        
        return "medium"
    
    def _recommend_emoji_usage(
        self,
        person_context: PersonalizationContext,
        engagement_pattern: EngagementPattern,
        communication_style: CommunicationStyle
    ) -> str:
        """Recommend emoji usage level"""
        
        # Age-based recommendations
        if person_context.age:
            if person_context.age >= 65:
                return "none"
            elif person_context.age <= 30:
                return "moderate"
        
        # Style-based recommendations
        if communication_style == CommunicationStyle.FORMAL:
            return "none"
        elif communication_style == CommunicationStyle.ENTHUSIASTIC:
            return "moderate"
        elif communication_style == CommunicationStyle.CASUAL:
            return "frequent"
        
        # Engagement-based recommendations
        if engagement_pattern == EngagementPattern.HIGHLY_ENGAGED:
            return "moderate"
        elif engagement_pattern in [EngagementPattern.DECLINING, EngagementPattern.DORMANT]:
            return "minimal"
        
        return "minimal"
    
    def _is_recent(self, date_str: str, days: int = 90) -> bool:
        """Check if a date string represents a recent date"""
        try:
            if isinstance(date_str, str):
                # Simple date parsing (assumes YYYY-MM-DD format)
                from datetime import datetime
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date_obj = date_str
            
            return (datetime.now() - date_obj).days <= days
        except:
            return False

    def get_tone_adjustment_recommendations(
        self,
        analysis: ToneAnalysis,
        message_performance: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Get recommendations for adjusting tone based on performance data"""
        
        recommendations = {
            "adjustments": [],
            "keep_same": [],
            "test_alternatives": []
        }
        
        if message_performance:
            open_rate = message_performance.get('open_rate', 0)
            response_rate = message_performance.get('response_rate', 0)
            
            # Low performance suggestions
            if open_rate < 0.2:
                recommendations["adjustments"].append("Subject line may be too formal - try more engaging tone")
            if response_rate < 0.05:
                recommendations["adjustments"].append("Message may need stronger call-to-action")
            
            # Good performance confirmations
            if open_rate > 0.3:
                recommendations["keep_same"].append("Current subject line approach is effective")
            if response_rate > 0.1:
                recommendations["keep_same"].append("Current message tone is generating responses")
        
        # General recommendations based on analysis
        if analysis.confidence_score < 0.6:
            recommendations["test_alternatives"].extend(analysis.alternative_tones)
        
        return recommendations