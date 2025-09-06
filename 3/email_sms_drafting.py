"""
Email/SMS Auto-Drafting Module for Volunteer PathFinder
Generates personalized outreach messages with contextual tone
"""
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from ai_assistant import VolunteerAIAssistant


class MessageType(Enum):
    EMAIL = "email"
    SMS = "sms"


class MessageTone(Enum):
    WELCOMING = "welcoming"
    ENCOURAGING = "encouraging"  
    INFORMATIVE = "informative"
    URGENT = "urgent"
    APPRECIATION = "appreciation"
    FOLLOW_UP = "follow_up"
    PERSONALIZED = "personalized"


class OutreachPurpose(Enum):
    WELCOME_NEW = "welcome_new"
    VOLUNTEER_MATCH = "volunteer_match"
    EVENT_INVITATION = "event_invitation"
    FOLLOW_UP_INQUIRY = "follow_up_inquiry"
    APPRECIATION = "appreciation"
    RE_ENGAGEMENT = "re_engagement"
    REMINDER = "reminder"
    UPDATE = "update"


@dataclass
class PersonalizationContext:
    """Context information for personalizing messages"""
    contact_id: Optional[str] = None
    name: str = ""
    age: Optional[int] = None
    gender: Optional[str] = None
    is_ymca_member: bool = False
    member_branch: Optional[str] = None
    volunteer_history: Dict[str, Any] = None
    preferences: Dict[str, Any] = None
    past_interactions: List[Dict] = None
    engagement_level: str = "new"  # new, active, returning, champion
    preferred_communication: str = "email"


@dataclass
class MessageContext:
    """Context for the message being drafted"""
    purpose: OutreachPurpose
    tone: MessageTone
    message_type: MessageType
    urgency_level: int = 1  # 1=low, 2=medium, 3=high
    event_details: Optional[Dict] = None
    volunteer_opportunity: Optional[Dict] = None
    branch_info: Optional[Dict] = None
    follow_up_context: Optional[str] = None


@dataclass
class DraftedMessage:
    """A drafted message with metadata"""
    subject: Optional[str]  # For emails only
    content: str
    message_type: MessageType
    tone: MessageTone
    purpose: OutreachPurpose
    personalization_score: float  # 0-1, how personalized
    estimated_engagement: float  # 0-1, predicted engagement
    character_count: int
    metadata: Dict[str, Any]
    created_at: datetime


class EmailSMSDraftingEngine:
    """Main engine for auto-drafting personalized emails and SMS messages"""
    
    def __init__(self, ai_assistant: VolunteerAIAssistant):
        self.ai_assistant = ai_assistant
        self.tone_templates = self._initialize_tone_templates()
        self.purpose_frameworks = self._initialize_purpose_frameworks()
        
    def _initialize_tone_templates(self) -> Dict[MessageTone, Dict[str, str]]:
        """Initialize tone-specific templates and guidelines"""
        return {
            MessageTone.WELCOMING: {
                "greeting_style": "warm and inclusive",
                "language": "friendly, enthusiastic",
                "closing": "welcoming and supportive",
                "emojis": "appropriate, 1-2 per message",
                "keywords": ["welcome", "excited", "community", "journey", "family"]
            },
            MessageTone.ENCOURAGING: {
                "greeting_style": "motivational",
                "language": "positive, empowering",
                "closing": "supportive and action-oriented",
                "emojis": "motivational, 1-2 per message",
                "keywords": ["amazing", "impact", "difference", "meaningful", "proud"]
            },
            MessageTone.INFORMATIVE: {
                "greeting_style": "professional but friendly",
                "language": "clear, factual",
                "closing": "helpful and available",
                "emojis": "minimal, informational only",
                "keywords": ["details", "information", "resources", "guide", "help"]
            },
            MessageTone.URGENT: {
                "greeting_style": "direct and clear",
                "language": "compelling, time-sensitive",
                "closing": "clear call-to-action",
                "emojis": "attention-getting, limited use",
                "keywords": ["limited", "soon", "opportunity", "act now", "don't miss"]
            },
            MessageTone.APPRECIATION: {
                "greeting_style": "grateful and personal",
                "language": "thankful, recognizing",
                "closing": "heartfelt appreciation",
                "emojis": "appreciation-focused",
                "keywords": ["thank you", "grateful", "appreciate", "valuable", "contribution"]
            },
            MessageTone.FOLLOW_UP: {
                "greeting_style": "checking in",
                "language": "caring, supportive",
                "closing": "open and available",
                "emojis": "supportive, 1 per message",
                "keywords": ["checking in", "how are you", "still interested", "support", "help"]
            },
            MessageTone.PERSONALIZED: {
                "greeting_style": "tailored to individual",
                "language": "reflects their interests and history",
                "closing": "specific to their situation",
                "emojis": "contextually appropriate",
                "keywords": "based on person's profile and preferences"
            }
        }
    
    def _initialize_purpose_frameworks(self) -> Dict[OutreachPurpose, Dict[str, str]]:
        """Initialize purpose-specific message frameworks"""
        return {
            OutreachPurpose.WELCOME_NEW: {
                "structure": "greeting -> welcome -> orientation -> next_steps -> support",
                "key_points": ["community welcome", "what to expect", "first steps", "available support"],
                "call_to_action": "complete registration or attend orientation"
            },
            OutreachPurpose.VOLUNTEER_MATCH: {
                "structure": "greeting -> opportunity -> why_good_match -> details -> action",
                "key_points": ["specific opportunity", "why it matches", "time commitment", "impact"],
                "call_to_action": "apply or learn more about opportunity"
            },
            OutreachPurpose.EVENT_INVITATION: {
                "structure": "greeting -> event_intro -> details -> benefits -> rsvp",
                "key_points": ["event description", "date/time/location", "what to expect", "how to attend"],
                "call_to_action": "RSVP or register for event"
            },
            OutreachPurpose.FOLLOW_UP_INQUIRY: {
                "structure": "greeting -> reference_previous -> check_status -> offer_help -> next_steps",
                "key_points": ["previous interaction", "current status", "available support", "options"],
                "call_to_action": "respond with questions or next preference"
            },
            OutreachPurpose.APPRECIATION: {
                "structure": "greeting -> specific_thanks -> impact -> recognition -> continued_support",
                "key_points": ["specific contribution", "measurable impact", "personal recognition", "future opportunities"],
                "call_to_action": "continue involvement or share experience"
            },
            OutreachPurpose.RE_ENGAGEMENT: {
                "structure": "greeting -> missed_you -> new_opportunities -> easy_return -> support",
                "key_points": ["acknowledge absence", "what's new", "easy re-entry", "available help"],
                "call_to_action": "explore new opportunities or reconnect"
            },
            OutreachPurpose.REMINDER: {
                "structure": "greeting -> friendly_reminder -> details -> importance -> easy_action",
                "key_points": ["what needs attention", "why it matters", "how to complete", "deadline if any"],
                "call_to_action": "complete required action"
            },
            OutreachPurpose.UPDATE: {
                "structure": "greeting -> update_intro -> key_changes -> impact_on_them -> next_steps",
                "key_points": ["what's changed", "why it matters to them", "any action needed", "benefits"],
                "call_to_action": "acknowledge or take advantage of update"
            }
        }
    
    async def draft_message(
        self, 
        person_context: PersonalizationContext,
        message_context: MessageContext,
        custom_instructions: Optional[str] = None
    ) -> DraftedMessage:
        """Draft a personalized message based on context"""
        
        # Analyze context and determine optimal approach
        personalization_level = self._calculate_personalization_level(person_context)
        
        # Build the AI prompt
        prompt = self._build_drafting_prompt(
            person_context, 
            message_context, 
            personalization_level,
            custom_instructions
        )
        
        # Get AI-generated draft
        draft_response = await self._generate_ai_draft(prompt, message_context.message_type)
        
        if not draft_response["success"]:
            # Fallback to template-based generation
            draft_content = self._generate_template_draft(person_context, message_context)
            subject = self._generate_template_subject(person_context, message_context)
        else:
            draft_content, subject = self._parse_ai_response(
                draft_response["content"], 
                message_context.message_type
            )
        
        # Apply final formatting and validation
        final_content = self._apply_final_formatting(
            draft_content, 
            message_context.message_type,
            person_context
        )
        
        # Calculate quality metrics
        personalization_score = self._calculate_personalization_score(
            final_content, person_context
        )
        engagement_estimate = self._estimate_engagement_potential(
            final_content, person_context, message_context
        )
        
        return DraftedMessage(
            subject=subject if message_context.message_type == MessageType.EMAIL else None,
            content=final_content,
            message_type=message_context.message_type,
            tone=message_context.tone,
            purpose=message_context.purpose,
            personalization_score=personalization_score,
            estimated_engagement=engagement_estimate,
            character_count=len(final_content),
            metadata={
                "personalization_level": personalization_level,
                "ai_generated": draft_response["success"],
                "context_used": self._get_context_summary(person_context)
            },
            created_at=datetime.now()
        )
    
    def _calculate_personalization_level(self, person_context: PersonalizationContext) -> str:
        """Determine how personalized the message should be based on available data"""
        score = 0
        
        if person_context.name:
            score += 1
        if person_context.volunteer_history:
            score += 2
        if person_context.preferences:
            score += 2
        if person_context.past_interactions:
            score += 1
        if person_context.member_branch:
            score += 1
        
        if score >= 6:
            return "highly_personalized"
        elif score >= 3:
            return "moderately_personalized"
        else:
            return "basic_personalized"
    
    def _build_drafting_prompt(
        self, 
        person_context: PersonalizationContext,
        message_context: MessageContext,
        personalization_level: str,
        custom_instructions: Optional[str]
    ) -> str:
        """Build the AI prompt for drafting the message"""
        
        # Get tone and purpose guidelines
        tone_guide = self.tone_templates[message_context.tone]
        purpose_guide = self.purpose_frameworks[message_context.purpose]
        
        # Build person description
        person_desc = self._format_person_context(person_context)
        
        # Build message requirements
        message_requirements = self._format_message_requirements(message_context)
        
        prompt = f"""You are drafting a {message_context.message_type.value} message for the YMCA of Greater Cincinnati's volunteer program.

RECIPIENT PROFILE:
{person_desc}

MESSAGE REQUIREMENTS:
- Type: {message_context.message_type.value.upper()}
- Purpose: {message_context.purpose.value.replace('_', ' ').title()}
- Tone: {message_context.tone.value.replace('_', ' ').title()}
- Personalization Level: {personalization_level.replace('_', ' ').title()}
{message_requirements}

TONE GUIDELINES:
- Greeting Style: {tone_guide['greeting_style']}
- Language: {tone_guide['language']}
- Closing: {tone_guide['closing']}
- Emoji Usage: {tone_guide['emojis']}
- Key Words/Phrases: {tone_guide['keywords']}

MESSAGE STRUCTURE:
{purpose_guide['structure']}

KEY POINTS TO INCLUDE:
{chr(10).join(['- ' + point for point in purpose_guide['key_points']])}

CALL TO ACTION:
{purpose_guide['call_to_action']}

{'CUSTOM INSTRUCTIONS:' + chr(10) + custom_instructions + chr(10) if custom_instructions else ''}

FORMATTING REQUIREMENTS:
- {'Email format with subject line and body' if message_context.message_type == MessageType.EMAIL else 'SMS format: concise, under 160 characters if possible'}
- Use YMCA branding voice: warm, inclusive, community-focused
- Include relevant YMCA resources or contact information
- Ensure accessibility and readability
- {'Make it personal but professional' if personalization_level == 'highly_personalized' else 'Keep it friendly and welcoming'}

Please draft the message now:"""
        
        return prompt
    
    def _format_person_context(self, person_context: PersonalizationContext) -> str:
        """Format person context for AI prompt"""
        context_parts = []
        
        if person_context.name:
            context_parts.append(f"Name: {person_context.name}")
        
        if person_context.age:
            context_parts.append(f"Age: {person_context.age}")
            
        if person_context.is_ymca_member:
            context_parts.append(f"YMCA Member: Yes{' at ' + person_context.member_branch if person_context.member_branch else ''}")
        
        context_parts.append(f"Engagement Level: {person_context.engagement_level.replace('_', ' ').title()}")
        
        if person_context.volunteer_history:
            history = person_context.volunteer_history
            context_parts.append(f"Volunteer History: {history.get('total_hours', 0)} hours, {history.get('sessions', 0)} sessions")
            if history.get('top_categories'):
                context_parts.append(f"Preferred Areas: {', '.join(list(history['top_categories'].keys())[:3])}")
        
        if person_context.preferences:
            prefs = person_context.preferences
            if prefs.get('interests'):
                context_parts.append(f"Interests: {prefs['interests']}")
            if prefs.get('location_preference'):
                context_parts.append(f"Preferred Location: {prefs['location_preference']}")
        
        return "\n".join(context_parts) if context_parts else "Basic contact information available"
    
    def _format_message_requirements(self, message_context: MessageContext) -> str:
        """Format message-specific requirements"""
        requirements = []
        
        if message_context.urgency_level > 1:
            urgency_text = ["", "moderate urgency", "high urgency"][message_context.urgency_level]
            requirements.append(f"- Urgency: {urgency_text}")
        
        if message_context.event_details:
            event = message_context.event_details
            requirements.append(f"- Event: {event.get('name', 'Event')} on {event.get('date', 'TBD')}")
            if event.get('location'):
                requirements.append(f"- Location: {event['location']}")
        
        if message_context.volunteer_opportunity:
            opp = message_context.volunteer_opportunity
            requirements.append(f"- Opportunity: {opp.get('project_name', 'Volunteer Opportunity')}")
            if opp.get('branch'):
                requirements.append(f"- Branch: {opp['branch']}")
        
        if message_context.branch_info:
            branch = message_context.branch_info
            requirements.append(f"- Branch Focus: {branch.get('name', 'YMCA Branch')}")
        
        return "\n".join(requirements) if requirements else ""
    
    async def _generate_ai_draft(self, prompt: str, message_type: MessageType) -> Dict[str, Any]:
        """Generate draft using AI assistant"""
        try:
            response = await self.ai_assistant.chat(prompt)
            return response
        except Exception as e:
            print(f"Error generating AI draft: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_ai_response(self, ai_content: str, message_type: MessageType) -> Tuple[str, Optional[str]]:
        """Parse AI response to extract content and subject"""
        if message_type == MessageType.EMAIL:
            # Look for subject line
            lines = ai_content.strip().split('\n')
            subject = None
            content_lines = []
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                if line_lower.startswith('subject:') or line_lower.startswith('subject line:'):
                    subject = line.split(':', 1)[1].strip()
                elif line.strip() and not (line_lower.startswith('subject') and ':' in line):
                    content_lines.extend(lines[i:])
                    break
            
            content = '\n'.join(content_lines).strip()
            return content, subject
        else:
            # SMS - just return content
            return ai_content.strip(), None
    
    def _generate_template_draft(
        self, 
        person_context: PersonalizationContext, 
        message_context: MessageContext
    ) -> str:
        """Generate fallback template-based draft"""
        
        # Basic template structure
        greeting = self._generate_greeting(person_context)
        body = self._generate_body(person_context, message_context)
        closing = self._generate_closing(person_context, message_context)
        
        if message_context.message_type == MessageType.SMS:
            # Condensed for SMS
            return f"{greeting} {body} {closing}".strip()
        else:
            # Full email format
            return f"{greeting}\n\n{body}\n\n{closing}".strip()
    
    def _generate_template_subject(
        self, 
        person_context: PersonalizationContext, 
        message_context: MessageContext
    ) -> Optional[str]:
        """Generate template-based subject line for emails"""
        if message_context.message_type != MessageType.EMAIL:
            return None
        
        name_part = f" {person_context.name}" if person_context.name else ""
        
        subject_templates = {
            OutreachPurpose.WELCOME_NEW: f"Welcome to YMCA Volunteering{name_part}! 🌟",
            OutreachPurpose.VOLUNTEER_MATCH: f"Perfect Volunteer Match Found{name_part}!",
            OutreachPurpose.EVENT_INVITATION: f"You're Invited: YMCA Event{name_part}",
            OutreachPurpose.FOLLOW_UP_INQUIRY: f"Following up on your volunteer interest{name_part}",
            OutreachPurpose.APPRECIATION: f"Thank You{name_part} - Your Impact Matters! 🙏",
            OutreachPurpose.RE_ENGAGEMENT: f"We Miss You{name_part} - New Opportunities Await!",
            OutreachPurpose.REMINDER: f"Friendly Reminder{name_part} - YMCA Volunteer",
            OutreachPurpose.UPDATE: f"Important Update{name_part} - YMCA Volunteers"
        }
        
        return subject_templates.get(message_context.purpose, f"YMCA Volunteer Program{name_part}")
    
    def _generate_greeting(self, person_context: PersonalizationContext) -> str:
        """Generate contextual greeting"""
        if person_context.name:
            return f"Hi {person_context.name.split()[0]},"
        else:
            return "Hello,"
    
    def _generate_body(
        self, 
        person_context: PersonalizationContext, 
        message_context: MessageContext
    ) -> str:
        """Generate message body based on purpose"""
        
        purpose_bodies = {
            OutreachPurpose.WELCOME_NEW: self._generate_welcome_body(person_context),
            OutreachPurpose.VOLUNTEER_MATCH: self._generate_match_body(person_context, message_context),
            OutreachPurpose.EVENT_INVITATION: self._generate_event_body(person_context, message_context),
            OutreachPurpose.FOLLOW_UP_INQUIRY: self._generate_follow_up_body(person_context, message_context),
            OutreachPurpose.APPRECIATION: self._generate_appreciation_body(person_context),
            OutreachPurpose.RE_ENGAGEMENT: self._generate_reengagement_body(person_context),
            OutreachPurpose.REMINDER: self._generate_reminder_body(person_context, message_context),
            OutreachPurpose.UPDATE: self._generate_update_body(person_context, message_context)
        }
        
        return purpose_bodies.get(message_context.purpose, "Thank you for your interest in YMCA volunteering!")
    
    def _generate_welcome_body(self, person_context: PersonalizationContext) -> str:
        """Generate welcome message body"""
        return "Welcome to the YMCA volunteer community! We're excited to have you join our mission of strengthening communities. Our team will help you find the perfect volunteer opportunity that matches your interests and schedule."
    
    def _generate_match_body(
        self, 
        person_context: PersonalizationContext, 
        message_context: MessageContext
    ) -> str:
        """Generate volunteer match message body"""
        if message_context.volunteer_opportunity:
            opp = message_context.volunteer_opportunity
            return f"Great news! We found a volunteer opportunity that's perfect for you: {opp.get('project_name', 'Volunteer Position')} at our {opp.get('branch', 'local')} branch. This role matches your interests and availability perfectly."
        return "We found some volunteer opportunities that would be perfect for you based on your interests and preferences!"
    
    def _generate_event_body(
        self, 
        person_context: PersonalizationContext, 
        message_context: MessageContext
    ) -> str:
        """Generate event invitation body"""
        if message_context.event_details:
            event = message_context.event_details
            return f"You're invited to {event.get('name', 'our upcoming event')} on {event.get('date', 'the scheduled date')}. This is a great opportunity to connect with fellow volunteers and learn more about our community programs."
        return "You're invited to join us for an upcoming volunteer event! It's a great way to meet fellow volunteers and learn more about our programs."
    
    def _generate_follow_up_body(
        self, 
        person_context: PersonalizationContext, 
        message_context: MessageContext
    ) -> str:
        """Generate follow-up message body"""
        return "I wanted to follow up on your interest in volunteering with the YMCA. Do you have any questions about the opportunities we discussed? I'm here to help make your volunteer journey as smooth as possible."
    
    def _generate_appreciation_body(self, person_context: PersonalizationContext) -> str:
        """Generate appreciation message body"""
        if person_context.volunteer_history:
            hours = person_context.volunteer_history.get('total_hours', 0)
            return f"Thank you for your incredible dedication to our community! Your {hours} hours of volunteer service have made a real difference in the lives of our members and neighbors."
        return "Thank you for your commitment to volunteering with the YMCA! Your contributions make a real difference in our community."
    
    def _generate_reengagement_body(self, person_context: PersonalizationContext) -> str:
        """Generate re-engagement message body"""
        return "We miss having you as part of our volunteer team! We have some exciting new opportunities that I think you'd love. Would you be interested in hearing about what's new?"
    
    def _generate_reminder_body(
        self, 
        person_context: PersonalizationContext, 
        message_context: MessageContext
    ) -> str:
        """Generate reminder message body"""
        return "Just a friendly reminder about completing your volunteer application. If you need any help with the process, please don't hesitate to reach out!"
    
    def _generate_update_body(
        self, 
        person_context: PersonalizationContext, 
        message_context: MessageContext
    ) -> str:
        """Generate update message body"""
        return "We have some exciting updates to share about our volunteer programs! These changes will help us serve our community even better, and we wanted to keep you informed."
    
    def _generate_closing(
        self, 
        person_context: PersonalizationContext, 
        message_context: MessageContext
    ) -> str:
        """Generate message closing"""
        closings = {
            MessageTone.WELCOMING: "Looking forward to welcoming you to our volunteer family!\n\nWarm regards,\nYMCA Volunteer Team",
            MessageTone.ENCOURAGING: "You're going to make an amazing impact!\n\nBest wishes,\nYMCA Volunteer Team", 
            MessageTone.INFORMATIVE: "Please let me know if you have any questions.\n\nSincerely,\nYMCA Volunteer Team",
            MessageTone.URGENT: "Please respond soon so we don't miss this opportunity!\n\nThank you,\nYMCA Volunteer Team",
            MessageTone.APPRECIATION: "With heartfelt gratitude,\nYMCA Volunteer Team",
            MessageTone.FOLLOW_UP: "I'm here to help whenever you're ready.\n\nBest regards,\nYMCA Volunteer Team",
            MessageTone.PERSONALIZED: "Thank you for being such an important part of our community!\n\nWarmly,\nYMCA Volunteer Team"
        }
        
        return closings.get(message_context.tone, "Best regards,\nYMCA Volunteer Team")
    
    def _apply_final_formatting(
        self, 
        content: str, 
        message_type: MessageType,
        person_context: PersonalizationContext
    ) -> str:
        """Apply final formatting and length constraints"""
        
        if message_type == MessageType.SMS:
            # SMS formatting - keep it concise
            if len(content) > 160:
                # Try to shorten while keeping key information
                sentences = content.split('.')
                shortened = sentences[0] + '.'
                if len(shortened) <= 160:
                    content = shortened
                else:
                    content = content[:155] + "..."
        
        # Add branch contact info if appropriate
        if person_context.member_branch and message_type == MessageType.EMAIL:
            branch_info = self._get_branch_contact_info(person_context.member_branch)
            if branch_info:
                content += f"\n\n{branch_info}"
        
        return content.strip()
    
    def _get_branch_contact_info(self, branch_name: str) -> Optional[str]:
        """Get contact information for specific branch"""
        branch_contacts = {
            "Blue Ash": "Questions? Contact Blue Ash YMCA at (513) 745-9622",
            "Blue Ash YMCA": "Questions? Contact Blue Ash YMCA at (513) 745-9622",
            "M.E. Lyons": "Questions? Contact M.E. Lyons YMCA at (513) 871-4900",
            "M.E. Lyons YMCA": "Questions? Contact M.E. Lyons YMCA at (513) 871-4900",
            "Campbell County": "Questions? Contact Campbell County YMCA at (859) 431-5000",
            "Campbell County YMCA": "Questions? Contact Campbell County YMCA at (859) 431-5000",
            "Clippard": "Questions? Contact Clippard YMCA at (513) 681-0003",
            "Clippard YMCA": "Questions? Contact Clippard YMCA at (513) 681-0003"
        }
        return branch_contacts.get(branch_name)
    
    def _calculate_personalization_score(
        self, 
        content: str, 
        person_context: PersonalizationContext
    ) -> float:
        """Calculate how personalized the message is (0-1)"""
        score = 0.0
        content_lower = content.lower()
        
        # Name usage
        if person_context.name and person_context.name.lower() in content_lower:
            score += 0.2
        
        # History references
        if person_context.volunteer_history:
            history_terms = ['hours', 'sessions', 'experience', 'work', 'contributions']
            if any(term in content_lower for term in history_terms):
                score += 0.2
        
        # Interest matching
        if person_context.preferences and person_context.preferences.get('interests'):
            interests = person_context.preferences['interests'].lower()
            if any(interest.strip() in content_lower for interest in interests.split(',')):
                score += 0.2
        
        # Branch specificity
        if person_context.member_branch and person_context.member_branch.lower() in content_lower:
            score += 0.2
        
        # Engagement level appropriateness
        engagement_indicators = {
            'new': ['welcome', 'getting started', 'begin'],
            'active': ['continue', 'ongoing', 'keep up'],
            'returning': ['back', 'return', 'again'],
            'champion': ['dedication', 'commitment', 'leadership']
        }
        
        level_terms = engagement_indicators.get(person_context.engagement_level, [])
        if any(term in content_lower for term in level_terms):
            score += 0.2
        
        return min(score, 1.0)
    
    def _estimate_engagement_potential(
        self, 
        content: str, 
        person_context: PersonalizationContext,
        message_context: MessageContext
    ) -> float:
        """Estimate potential engagement level (0-1)"""
        score = 0.5  # Base score
        
        # Personalization boosts engagement
        personalization = self._calculate_personalization_score(content, person_context)
        score += personalization * 0.3
        
        # Tone appropriateness
        if message_context.tone in [MessageTone.WELCOMING, MessageTone.ENCOURAGING, MessageTone.PERSONALIZED]:
            score += 0.1
        
        # Clear call to action
        cta_indicators = ['click', 'visit', 'call', 'contact', 'register', 'sign up', 'apply', 'join']
        if any(cta in content.lower() for cta in cta_indicators):
            score += 0.1
        
        # Length appropriateness
        if message_context.message_type == MessageType.SMS:
            if 50 <= len(content) <= 160:
                score += 0.1
        else:
            if 100 <= len(content) <= 500:
                score += 0.1
        
        return min(score, 1.0)
    
    def _get_context_summary(self, person_context: PersonalizationContext) -> Dict[str, bool]:
        """Summarize what context was available for personalization"""
        return {
            "has_name": bool(person_context.name),
            "has_history": bool(person_context.volunteer_history),
            "has_preferences": bool(person_context.preferences),
            "has_branch": bool(person_context.member_branch),
            "has_interactions": bool(person_context.past_interactions)
        }

    async def generate_multiple_variants(
        self,
        person_context: PersonalizationContext,
        message_context: MessageContext,
        num_variants: int = 3
    ) -> List[DraftedMessage]:
        """Generate multiple message variants for A/B testing"""
        variants = []
        
        # Generate variants with different tones
        tone_variants = [
            MessageTone.WELCOMING,
            MessageTone.ENCOURAGING,
            MessageTone.PERSONALIZED
        ]
        
        for i in range(min(num_variants, len(tone_variants))):
            variant_context = MessageContext(
                purpose=message_context.purpose,
                tone=tone_variants[i],
                message_type=message_context.message_type,
                urgency_level=message_context.urgency_level,
                event_details=message_context.event_details,
                volunteer_opportunity=message_context.volunteer_opportunity,
                branch_info=message_context.branch_info,
                follow_up_context=message_context.follow_up_context
            )
            
            variant = await self.draft_message(person_context, variant_context)
            variants.append(variant)
        
        return variants

    def get_optimal_send_time(
        self,
        person_context: PersonalizationContext,
        message_type: MessageType
    ) -> Dict[str, Any]:
        """Suggest optimal send time based on context"""
        
        # Default recommendations
        if message_type == MessageType.EMAIL:
            optimal_hours = [9, 10, 14, 15]  # 9am, 10am, 2pm, 3pm
            optimal_days = ['Tuesday', 'Wednesday', 'Thursday']
        else:  # SMS
            optimal_hours = [10, 14, 19]  # 10am, 2pm, 7pm
            optimal_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
        # Adjust based on person context
        if person_context.engagement_level == 'champion':
            # Champions might be more flexible
            optimal_hours.extend([8, 16, 17])
        
        if person_context.age and person_context.age > 65:
            # Older volunteers might prefer earlier times
            optimal_hours = [8, 9, 10, 14]
            if message_type == MessageType.SMS:
                optimal_hours = [10, 14]  # Avoid evening SMS for seniors
        
        return {
            "optimal_hours": sorted(list(set(optimal_hours))),
            "optimal_days": optimal_days,
            "avoid_weekends": message_type == MessageType.EMAIL,
            "timezone_consideration": "Consider local branch timezone"
        }