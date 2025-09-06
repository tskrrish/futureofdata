"""
Message Templates and Personalization Logic
Provides template-based message generation with smart personalization
"""
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from email_sms_drafting import MessageType, MessageTone, OutreachPurpose, PersonalizationContext
from contextual_tone_analyzer import CommunicationStyle, EngagementPattern


@dataclass
class TemplateVariable:
    """Represents a variable that can be substituted in templates"""
    name: str
    default_value: str
    description: str
    required: bool = False
    validation_pattern: Optional[str] = None


@dataclass
class MessageTemplate:
    """A message template with personalization logic"""
    id: str
    name: str
    purpose: OutreachPurpose
    tone: MessageTone
    message_type: MessageType
    subject_template: Optional[str]  # For emails
    content_template: str
    variables: List[TemplateVariable]
    personalization_rules: Dict[str, Any]
    usage_notes: Optional[str] = None
    created_date: Optional[datetime] = None


class MessageTemplateEngine:
    """Engine for managing and processing message templates"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.personalization_functions = self._initialize_personalization_functions()
    
    def _initialize_templates(self) -> Dict[str, MessageTemplate]:
        """Initialize the template library"""
        templates = {}
        
        # Welcome New Volunteer Templates
        templates['welcome_new_email_welcoming'] = MessageTemplate(
            id='welcome_new_email_welcoming',
            name='New Volunteer Welcome - Welcoming Email',
            purpose=OutreachPurpose.WELCOME_NEW,
            tone=MessageTone.WELCOMING,
            message_type=MessageType.EMAIL,
            subject_template='Welcome to YMCA Volunteering{name_part}! 🌟',
            content_template='''Hi {first_name},

Welcome to the YMCA of Greater Cincinnati volunteer community! {enthusiasm_phrase} We're absolutely thrilled to have you join our mission of strengthening communities and changing lives.

{personalized_welcome_context}

Here's what happens next:
• Complete your volunteer profile at {volunteer_portal_url}
• Browse opportunities that match your interests in {interest_areas}
• Connect with our {branch_name} team for your first volunteer experience

{member_specific_note}

Your volunteer journey starts now, and we can't wait to see the amazing impact you'll make! Our community is stronger because people like you choose to make a difference.

{support_contact}

Welcome to the family! 🏠

Warmly,
YMCA Volunteer Team''',
            variables=[
                TemplateVariable('first_name', 'there', 'Person\'s first name', True),
                TemplateVariable('enthusiasm_phrase', '✨', 'Enthusiastic opening phrase'),
                TemplateVariable('personalized_welcome_context', '', 'Context based on their background'),
                TemplateVariable('volunteer_portal_url', 'https://cincinnatiymca.volunteermatters.org', 'Portal URL'),
                TemplateVariable('interest_areas', 'youth development, fitness programs, and community events', 'Their areas of interest'),
                TemplateVariable('branch_name', 'local YMCA', 'Their preferred branch'),
                TemplateVariable('member_specific_note', '', 'Note if they\'re a YMCA member'),
                TemplateVariable('support_contact', 'Questions? We\'re here to help at volunteer@ymcacincinnati.org', 'Support contact info'),
                TemplateVariable('name_part', '', 'Name for subject line')
            ],
            personalization_rules={
                'use_name_in_greeting': True,
                'reference_interests': True,
                'include_branch_info': True,
                'add_member_benefits': 'if_member'
            }
        )
        
        templates['welcome_new_sms_welcoming'] = MessageTemplate(
            id='welcome_new_sms_welcoming',
            name='New Volunteer Welcome - SMS',
            purpose=OutreachPurpose.WELCOME_NEW,
            tone=MessageTone.WELCOMING,
            message_type=MessageType.SMS,
            subject_template=None,
            content_template='Hi {first_name}! Welcome to YMCA volunteering! 🌟 Ready to make an impact? Complete your profile: {short_url} Questions? Reply HELP',
            variables=[
                TemplateVariable('first_name', 'there', 'Person\'s first name', True),
                TemplateVariable('short_url', 'bit.ly/ymcavol', 'Shortened portal URL')
            ],
            personalization_rules={
                'keep_under_160_chars': True,
                'include_action_keyword': True
            }
        )
        
        # Volunteer Match Templates
        templates['volunteer_match_email_personalized'] = MessageTemplate(
            id='volunteer_match_email_personalized',
            name='Volunteer Opportunity Match - Personalized Email',
            purpose=OutreachPurpose.VOLUNTEER_MATCH,
            tone=MessageTone.PERSONALIZED,
            message_type=MessageType.EMAIL,
            subject_template='Perfect Match Found: {opportunity_name} at {branch_name}!',
            content_template='''Hi {first_name},

{match_opening_line}

I found an opportunity that's tailor-made for you: **{opportunity_name}** at our {branch_name} branch.

**Why this is perfect for you:**
{personalized_match_reasons}

**The Details:**
• **Role**: {role_description}
• **Time Commitment**: {time_commitment}
• **Schedule**: {schedule_options}
• **Location**: {location_details}
• **Start Date**: {start_date}

{volunteer_history_reference}

{special_requirements_note}

Ready to make a difference? {call_to_action}

{opportunity_contact}

Looking forward to seeing you in action!

Best regards,
{coordinator_name}
YMCA Volunteer Coordinator''',
            variables=[
                TemplateVariable('first_name', 'there', 'Person\'s first name', True),
                TemplateVariable('match_opening_line', 'Great news!', 'Opening line based on match quality'),
                TemplateVariable('opportunity_name', 'Volunteer Opportunity', 'Name of the opportunity', True),
                TemplateVariable('branch_name', 'YMCA', 'Branch name', True),
                TemplateVariable('personalized_match_reasons', '', 'Why this matches their profile'),
                TemplateVariable('role_description', 'Help with community programs', 'What they\'ll be doing'),
                TemplateVariable('time_commitment', '2-3 hours per week', 'Expected time commitment'),
                TemplateVariable('schedule_options', 'Flexible weekday evenings', 'Available schedule'),
                TemplateVariable('location_details', 'Main facility', 'Where they\'ll volunteer'),
                TemplateVariable('start_date', 'Immediately', 'When they can start'),
                TemplateVariable('volunteer_history_reference', '', 'Reference to their past experience'),
                TemplateVariable('special_requirements_note', '', 'Any special requirements'),
                TemplateVariable('call_to_action', 'Click here to apply!', 'What they should do next'),
                TemplateVariable('opportunity_contact', '', 'Contact info for the opportunity'),
                TemplateVariable('coordinator_name', 'The Team', 'Coordinator\'s name')
            ],
            personalization_rules={
                'match_reasons_required': True,
                'reference_volunteer_history': 'if_available',
                'include_branch_specifics': True,
                'personalize_call_to_action': True
            }
        )
        
        # Appreciation Templates
        templates['appreciation_email_heartfelt'] = MessageTemplate(
            id='appreciation_email_heartfelt',
            name='Volunteer Appreciation - Heartfelt Email',
            purpose=OutreachPurpose.APPRECIATION,
            tone=MessageTone.APPRECIATION,
            message_type=MessageType.EMAIL,
            subject_template='Thank You {first_name} - Your {contribution_highlight}! 🙏',
            content_template='''Dear {first_name},

{appreciation_opening}

{specific_contribution_recognition}

**Your Impact by the Numbers:**
{impact_statistics}

{personal_story_or_feedback}

{recognition_specific_achievements}

{community_impact_statement}

Your dedication embodies the YMCA spirit of caring, honesty, respect, and responsibility. {future_engagement_note}

{gift_or_recognition_note}

With heartfelt gratitude,

{signature_name}
{signature_title}
{branch_name}''',
            variables=[
                TemplateVariable('first_name', 'Friend', 'Person\'s first name', True),
                TemplateVariable('contribution_highlight', 'Amazing Dedication', 'Brief highlight for subject'),
                TemplateVariable('appreciation_opening', 'Thank you for being an incredible part of our YMCA community!', 'Opening appreciation statement'),
                TemplateVariable('specific_contribution_recognition', '', 'Specific things they\'ve contributed'),
                TemplateVariable('impact_statistics', '', 'Numbers showing their impact'),
                TemplateVariable('personal_story_or_feedback', '', 'Personal story or feedback from beneficiaries'),
                TemplateVariable('recognition_specific_achievements', '', 'Specific achievements to recognize'),
                TemplateVariable('community_impact_statement', '', 'How they\'ve impacted the community'),
                TemplateVariable('future_engagement_note', '', 'Note about continued engagement'),
                TemplateVariable('gift_or_recognition_note', '', 'Any gifts or special recognition'),
                TemplateVariable('signature_name', 'YMCA Team', 'Sender\'s name'),
                TemplateVariable('signature_title', '', 'Sender\'s title'),
                TemplateVariable('branch_name', 'YMCA of Greater Cincinnati', 'Branch name')
            ],
            personalization_rules={
                'require_specific_contributions': True,
                'include_measurable_impact': 'if_available',
                'add_personal_touches': True,
                'reference_ymca_values': True
            }
        )
        
        # Re-engagement Templates
        templates['reengagement_email_encouraging'] = MessageTemplate(
            id='reengagement_email_encouraging',
            name='Volunteer Re-engagement - Encouraging Email',
            purpose=OutreachPurpose.RE_ENGAGEMENT,
            tone=MessageTone.ENCOURAGING,
            message_type=MessageType.EMAIL,
            subject_template='We Miss You {first_name} - Exciting New Opportunities! 🌟',
            content_template='''Hi {first_name},

{miss_you_opening}

{acknowledge_past_contributions}

We have some exciting updates to share:

{whats_new_section}

**New Opportunities Perfect for You:**
{personalized_new_opportunities}

{easy_return_process}

{flexible_options_note}

{no_pressure_statement}

{direct_contact_invitation}

We'd love to have you back when you're ready!

{warm_closing}

{coordinator_signature}''',
            variables=[
                TemplateVariable('first_name', 'Friend', 'Person\'s first name', True),
                TemplateVariable('miss_you_opening', 'We\'ve missed having you as part of our volunteer community!', 'Opening statement'),
                TemplateVariable('acknowledge_past_contributions', '', 'Acknowledge their previous volunteer work'),
                TemplateVariable('whats_new_section', '', 'What\'s new since they\'ve been away'),
                TemplateVariable('personalized_new_opportunities', '', 'New opportunities that match their interests'),
                TemplateVariable('easy_return_process', '', 'How easy it is to get back involved'),
                TemplateVariable('flexible_options_note', '', 'Note about flexible volunteering options'),
                TemplateVariable('no_pressure_statement', 'No pressure at all - we know life gets busy!', 'Reassuring statement'),
                TemplateVariable('direct_contact_invitation', '', 'Invitation to contact directly'),
                TemplateVariable('warm_closing', 'Hope to see you soon!', 'Warm closing statement'),
                TemplateVariable('coordinator_signature', 'YMCA Volunteer Team', 'Coordinator signature')
            ],
            personalization_rules={
                'reference_past_activity': 'if_available',
                'match_previous_interests': True,
                'emphasize_flexibility': True,
                'no_guilt_approach': True
            }
        )
        
        # Event Invitation Templates
        templates['event_invitation_email_informative'] = MessageTemplate(
            id='event_invitation_email_informative',
            name='Event Invitation - Informative Email',
            purpose=OutreachPurpose.EVENT_INVITATION,
            tone=MessageTone.INFORMATIVE,
            message_type=MessageType.EMAIL,
            subject_template='You\'re Invited: {event_name} - {event_date}',
            content_template='''Hi {first_name},

{event_invitation_opening}

**Event Details:**
• **What**: {event_name}
• **When**: {event_date_time}
• **Where**: {event_location}
• **Duration**: {event_duration}

{event_description}

**What to Expect:**
{event_agenda}

{why_perfect_for_them}

{what_to_bring_note}

{networking_opportunity_note}

**RSVP Required:** {rsvp_instructions}

{event_contact_info}

{looking_forward_statement}

Best regards,
{event_organizer}''',
            variables=[
                TemplateVariable('first_name', 'there', 'Person\'s first name', True),
                TemplateVariable('event_invitation_opening', 'You\'re invited to join us for an upcoming volunteer event!', 'Event invitation opening'),
                TemplateVariable('event_name', 'YMCA Volunteer Event', 'Name of the event', True),
                TemplateVariable('event_date', 'TBD', 'Event date', True),
                TemplateVariable('event_date_time', 'TBD', 'Full date and time', True),
                TemplateVariable('event_location', 'YMCA Branch', 'Event location', True),
                TemplateVariable('event_duration', '2 hours', 'How long the event will be'),
                TemplateVariable('event_description', '', 'Description of the event'),
                TemplateVariable('event_agenda', '', 'What will happen at the event'),
                TemplateVariable('why_perfect_for_them', '', 'Why this event matches their interests'),
                TemplateVariable('what_to_bring_note', '', 'What they should bring'),
                TemplateVariable('networking_opportunity_note', '', 'Note about networking opportunities'),
                TemplateVariable('rsvp_instructions', 'Reply to this email or call us!', 'How to RSVP'),
                TemplateVariable('event_contact_info', '', 'Contact info for event questions'),
                TemplateVariable('looking_forward_statement', 'Looking forward to seeing you there!', 'Closing statement'),
                TemplateVariable('event_organizer', 'YMCA Event Team', 'Event organizer name')
            ],
            personalization_rules={
                'match_event_to_interests': True,
                'include_clear_logistics': True,
                'add_networking_value': 'if_appropriate',
                'personalize_why_invited': True
            }
        )
        
        # Follow-up Templates
        templates['follow_up_email_supportive'] = MessageTemplate(
            id='follow_up_email_supportive',
            name='Follow-up Inquiry - Supportive Email',
            purpose=OutreachPurpose.FOLLOW_UP_INQUIRY,
            tone=MessageTone.FOLLOW_UP,
            message_type=MessageType.EMAIL,
            subject_template='Checking In - How Can We Help You Get Started?',
            content_template='''Hi {first_name},

{follow_up_opening}

{reference_previous_interaction}

{understanding_statement}

{offer_specific_help}

**Ways We Can Support You:**
{support_options}

{remove_barriers_note}

{alternative_opportunities}

{no_commitment_reassurance}

{direct_contact_offer}

{encouragement_closing}

Here to help,
{support_coordinator}''',
            variables=[
                TemplateVariable('first_name', 'there', 'Person\'s first name', True),
                TemplateVariable('follow_up_opening', 'I wanted to check in and see how your volunteer journey is going!', 'Follow-up opening'),
                TemplateVariable('reference_previous_interaction', '', 'Reference to previous interaction'),
                TemplateVariable('understanding_statement', 'We know getting started can sometimes feel overwhelming.', 'Understanding statement'),
                TemplateVariable('offer_specific_help', '', 'Specific help we can offer'),
                TemplateVariable('support_options', '', 'List of support options'),
                TemplateVariable('remove_barriers_note', '', 'Note about removing barriers'),
                TemplateVariable('alternative_opportunities', '', 'Alternative volunteer options'),
                TemplateVariable('no_commitment_reassurance', 'No pressure - we\'re here when you\'re ready!', 'Reassurance statement'),
                TemplateVariable('direct_contact_offer', '', 'Offer for direct contact'),
                TemplateVariable('encouragement_closing', 'We believe you\'ll make an amazing volunteer!', 'Encouraging closing'),
                TemplateVariable('support_coordinator', 'YMCA Support Team', 'Support coordinator name')
            ],
            personalization_rules={
                'reference_specific_barriers': 'if_known',
                'offer_tailored_support': True,
                'maintain_encouraging_tone': True,
                'provide_easy_next_steps': True
            }
        )
        
        return templates
    
    def _initialize_personalization_functions(self) -> Dict[str, callable]:
        """Initialize personalization helper functions"""
        return {
            'format_name_part': self._format_name_part,
            'generate_enthusiasm_phrase': self._generate_enthusiasm_phrase,
            'create_personalized_welcome': self._create_personalized_welcome,
            'format_match_reasons': self._format_match_reasons,
            'generate_impact_statistics': self._generate_impact_statistics,
            'create_whats_new_section': self._create_whats_new_section,
            'format_support_options': self._format_support_options
        }
    
    def get_template(self, template_id: str) -> Optional[MessageTemplate]:
        """Get a specific template by ID"""
        return self.templates.get(template_id)
    
    def get_templates_by_criteria(
        self,
        purpose: Optional[OutreachPurpose] = None,
        tone: Optional[MessageTone] = None,
        message_type: Optional[MessageType] = None
    ) -> List[MessageTemplate]:
        """Get templates matching specific criteria"""
        results = []
        for template in self.templates.values():
            if purpose and template.purpose != purpose:
                continue
            if tone and template.tone != tone:
                continue
            if message_type and template.message_type != message_type:
                continue
            results.append(template)
        return results
    
    def render_template(
        self,
        template_id: str,
        person_context: PersonalizationContext,
        custom_variables: Optional[Dict[str, str]] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Render a template with personalized content"""
        
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Prepare variables
        variables = self._prepare_template_variables(
            template, person_context, custom_variables or {}, context_data or {}
        )
        
        # Render subject (for emails)
        subject = None
        if template.subject_template:
            subject = self._render_template_string(template.subject_template, variables)
        
        # Render content
        content = self._render_template_string(template.content_template, variables)
        
        # Apply post-processing
        content = self._apply_post_processing(content, template, person_context)
        
        return {
            'subject': subject,
            'content': content,
            'variables_used': list(variables.keys()),
            'template_id': template_id
        }
    
    def _prepare_template_variables(
        self,
        template: MessageTemplate,
        person_context: PersonalizationContext,
        custom_variables: Dict[str, str],
        context_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Prepare all variables for template rendering"""
        
        variables = {}
        
        # Start with defaults from template
        for var in template.variables:
            variables[var.name] = var.default_value
        
        # Add personalization from context
        if person_context.name:
            name_parts = person_context.name.split()
            variables['first_name'] = name_parts[0] if name_parts else 'there'
            variables['last_name'] = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            variables['full_name'] = person_context.name
            variables['name_part'] = f" {variables['first_name']}"
        
        # Add volunteer history variables
        if person_context.volunteer_history:
            history = person_context.volunteer_history
            variables['total_hours'] = str(history.get('total_hours', 0))
            variables['total_sessions'] = str(history.get('sessions', 0))
            variables['volunteer_experience'] = self._format_volunteer_experience(history)
            
            # Interest areas
            if history.get('top_categories'):
                categories = list(history['top_categories'].keys())[:3]
                variables['interest_areas'] = ', '.join(categories).lower()
        
        # Add branch information
        if person_context.member_branch:
            variables['branch_name'] = person_context.member_branch
            variables['branch_contact'] = self._get_branch_contact(person_context.member_branch)
        
        # Add preference-based variables
        if person_context.preferences:
            prefs = person_context.preferences
            if prefs.get('interests'):
                variables['user_interests'] = prefs['interests']
            if prefs.get('location_preference'):
                variables['preferred_location'] = prefs['location_preference']
        
        # Add context-specific variables
        if context_data.get('opportunity'):
            opp = context_data['opportunity']
            variables['opportunity_name'] = opp.get('project_name', 'Volunteer Opportunity')
            variables['role_description'] = opp.get('description', 'Help with community programs')
            variables['time_commitment'] = opp.get('time_commitment', '2-3 hours per week')
        
        if context_data.get('event'):
            event = context_data['event']
            variables['event_name'] = event.get('name', 'YMCA Event')
            variables['event_date'] = event.get('date', 'TBD')
            variables['event_location'] = event.get('location', 'YMCA Branch')
        
        # Apply personalization functions
        variables = self._apply_personalization_functions(
            variables, template, person_context, context_data
        )
        
        # Override with custom variables
        variables.update(custom_variables)
        
        return variables
    
    def _apply_personalization_functions(
        self,
        variables: Dict[str, str],
        template: MessageTemplate,
        person_context: PersonalizationContext,
        context_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Apply personalization functions based on template rules"""
        
        rules = template.personalization_rules
        
        # Generate enthusiasm phrase
        if 'enthusiasm_phrase' in variables:
            variables['enthusiasm_phrase'] = self._generate_enthusiasm_phrase(
                person_context, template.tone
            )
        
        # Create personalized welcome context
        if 'personalized_welcome_context' in variables:
            variables['personalized_welcome_context'] = self._create_personalized_welcome(
                person_context
            )
        
        # Generate match reasons for volunteer opportunities
        if 'personalized_match_reasons' in variables and context_data.get('opportunity'):
            variables['personalized_match_reasons'] = self._format_match_reasons(
                person_context, context_data['opportunity']
            )
        
        # Generate impact statistics for appreciation messages
        if 'impact_statistics' in variables and person_context.volunteer_history:
            variables['impact_statistics'] = self._generate_impact_statistics(
                person_context.volunteer_history
            )
        
        # Member-specific notes
        if 'member_specific_note' in variables and person_context.is_ymca_member:
            variables['member_specific_note'] = (
                f"As a YMCA member at {person_context.member_branch or 'our facility'}, "
                "you already know how much community matters to us!"
            )
        
        return variables
    
    def _render_template_string(self, template_str: str, variables: Dict[str, str]) -> str:
        """Render a template string with variable substitution"""
        
        result = template_str
        
        # Simple variable substitution
        for var_name, var_value in variables.items():
            placeholder = f'{{{var_name}}}'
            result = result.replace(placeholder, str(var_value))
        
        # Clean up any remaining placeholders
        result = re.sub(r'\{[^}]+\}', '', result)
        
        # Clean up extra whitespace
        result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)
        result = result.strip()
        
        return result
    
    def _apply_post_processing(
        self,
        content: str,
        template: MessageTemplate,
        person_context: PersonalizationContext
    ) -> str:
        """Apply post-processing rules to rendered content"""
        
        # Remove empty sections
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip lines that are just bullet points or empty
            if line.strip() in ['•', '-', '*'] or not line.strip():
                continue
            cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        # Apply message type specific formatting
        if template.message_type == MessageType.SMS:
            # Ensure SMS length limits
            if len(content) > 160:
                content = content[:155] + "..."
        
        # Apply tone-specific adjustments
        if template.tone == MessageTone.ENTHUSIASTIC:
            # Ensure at least one exclamation mark
            if '!' not in content:
                content = content.rstrip('.') + '!'
        
        return content
    
    # Personalization helper functions
    def _format_name_part(self, person_context: PersonalizationContext) -> str:
        """Format name part for subject lines"""
        if person_context.name:
            first_name = person_context.name.split()[0]
            return f" {first_name}"
        return ""
    
    def _generate_enthusiasm_phrase(
        self,
        person_context: PersonalizationContext,
        tone: MessageTone
    ) -> str:
        """Generate enthusiasm phrase based on context and tone"""
        
        phrases = {
            MessageTone.WELCOMING: ["🌟", "We're so excited!", "Welcome aboard!", "✨"],
            MessageTone.ENCOURAGING: ["You're amazing!", "This is going to be great!", "We believe in you!", "🎉"],
            MessageTone.PERSONALIZED: ["Perfect timing!", "This feels like destiny!", "What a match!", "🎯"],
            MessageTone.APPRECIATION: ["We're so grateful!", "You're incredible!", "Thank you so much!", "🙏"]
        }
        
        tone_phrases = phrases.get(tone, ["Great news!"])
        
        # Select based on engagement level
        if person_context.engagement_level == 'champion':
            return tone_phrases[0]  # Most enthusiastic
        elif person_context.engagement_level == 'new':
            return tone_phrases[-1] if len(tone_phrases) > 1 else tone_phrases[0]  # More welcoming
        
        return tone_phrases[0]
    
    def _create_personalized_welcome(self, person_context: PersonalizationContext) -> str:
        """Create personalized welcome context"""
        
        welcome_parts = []
        
        if person_context.is_ymca_member:
            welcome_parts.append(
                f"As a member at {person_context.member_branch or 'our YMCA'}, "
                "you already know how much community means to us."
            )
        
        if person_context.preferences and person_context.preferences.get('interests'):
            interests = person_context.preferences['interests']
            welcome_parts.append(
                f"We noticed your interest in {interests} - we have some fantastic opportunities "
                "in those exact areas!"
            )
        
        if person_context.age:
            if person_context.age <= 25:
                welcome_parts.append(
                    "Your energy and fresh perspective will bring so much to our programs!"
                )
            elif person_context.age >= 55:
                welcome_parts.append(
                    "Your experience and wisdom will be invaluable to our community!"
                )
        
        return ' '.join(welcome_parts) if welcome_parts else (
            "Every volunteer brings something unique to our community, and we can't wait to "
            "discover what special gifts you'll share!"
        )
    
    def _format_match_reasons(
        self,
        person_context: PersonalizationContext,
        opportunity: Dict[str, Any]
    ) -> str:
        """Format personalized match reasons for volunteer opportunities"""
        
        reasons = []
        
        # Interest matching
        if (person_context.preferences and person_context.preferences.get('interests') and 
            opportunity.get('category')):
            user_interests = person_context.preferences['interests'].lower()
            opp_category = opportunity['category'].lower()
            if any(interest.strip() in opp_category for interest in user_interests.split(',')):
                reasons.append(f"• Matches your interest in {opportunity['category'].lower()}")
        
        # Location matching
        if (person_context.member_branch and opportunity.get('branch') and
            person_context.member_branch in opportunity['branch']):
            reasons.append(f"• Located at your home branch: {person_context.member_branch}")
        
        # Experience level matching
        if person_context.volunteer_history:
            hours = person_context.volunteer_history.get('total_hours', 0)
            if hours > 50:
                reasons.append("• Perfect for someone with your volunteer experience")
            elif hours > 10:
                reasons.append("• Great next step based on your volunteer background")
            else:
                reasons.append("• Ideal opportunity to build on your volunteer journey")
        
        # Schedule matching (if available)
        if (person_context.preferences and person_context.preferences.get('availability') and
            opportunity.get('schedule')):
            reasons.append("• Schedule aligns with your availability")
        
        # Default reasons if no specific matches
        if not reasons:
            reasons = [
                "• Great opportunity to make a meaningful impact",
                "• Supportive team environment",
                "• Flexible and rewarding experience"
            ]
        
        return '\n'.join(reasons)
    
    def _generate_impact_statistics(self, volunteer_history: Dict[str, Any]) -> str:
        """Generate impact statistics for appreciation messages"""
        
        stats = []
        
        hours = volunteer_history.get('total_hours', 0)
        sessions = volunteer_history.get('sessions', 0)
        
        if hours > 0:
            stats.append(f"• **{hours} volunteer hours** contributing to our community")
        
        if sessions > 0:
            stats.append(f"• **{sessions} volunteer sessions** showing your commitment")
        
        # Calculate estimated impact
        if hours > 0:
            # Rough estimates based on YMCA program impact
            estimated_people = hours * 2  # Rough estimate of people impacted per hour
            stats.append(f"• Approximately **{estimated_people} community members** positively impacted")
        
        if volunteer_history.get('top_categories'):
            categories = list(volunteer_history['top_categories'].keys())
            stats.append(f"• Active in **{len(categories)} program areas**: {', '.join(categories[:3])}")
        
        return '\n'.join(stats) if stats else "• Your dedication and time have made a real difference!"
    
    def _format_volunteer_experience(self, history: Dict[str, Any]) -> str:
        """Format volunteer experience description"""
        
        hours = history.get('total_hours', 0)
        sessions = history.get('sessions', 0)
        
        if hours >= 100:
            return "extensive volunteer experience"
        elif hours >= 50:
            return "significant volunteer experience"
        elif hours >= 20:
            return "solid volunteer background"
        elif sessions >= 5:
            return "growing volunteer experience"
        else:
            return "volunteer experience"
    
    def _get_branch_contact(self, branch_name: str) -> str:
        """Get contact information for a branch"""
        
        contacts = {
            "Blue Ash YMCA": "Questions? Contact Blue Ash YMCA at (513) 745-9622",
            "M.E. Lyons YMCA": "Questions? Contact M.E. Lyons YMCA at (513) 871-4900", 
            "Campbell County YMCA": "Questions? Contact Campbell County YMCA at (859) 431-5000",
            "Clippard YMCA": "Questions? Contact Clippard YMCA at (513) 681-0003"
        }
        
        return contacts.get(branch_name, "Questions? Contact your local YMCA branch!")

    def get_template_recommendations(
        self,
        purpose: OutreachPurpose,
        person_context: PersonalizationContext,
        engagement_pattern: EngagementPattern,
        communication_style: CommunicationStyle
    ) -> List[str]:
        """Recommend best templates based on context"""
        
        # Get all templates for the purpose
        purpose_templates = self.get_templates_by_criteria(purpose=purpose)
        
        if not purpose_templates:
            return []
        
        # Score templates based on context
        scored_templates = []
        
        for template in purpose_templates:
            score = self._score_template_fit(
                template, person_context, engagement_pattern, communication_style
            )
            scored_templates.append((template.id, score))
        
        # Sort by score and return top recommendations
        scored_templates.sort(key=lambda x: x[1], reverse=True)
        return [template_id for template_id, _ in scored_templates[:3]]
    
    def _score_template_fit(
        self,
        template: MessageTemplate,
        person_context: PersonalizationContext,
        engagement_pattern: EngagementPattern,
        communication_style: CommunicationStyle
    ) -> float:
        """Score how well a template fits the context"""
        
        score = 0.0
        
        # Tone matching
        tone_compatibility = {
            CommunicationStyle.ENTHUSIASTIC: [MessageTone.ENCOURAGING, MessageTone.WELCOMING],
            CommunicationStyle.FORMAL: [MessageTone.INFORMATIVE, MessageTone.APPRECIATION],
            CommunicationStyle.CASUAL: [MessageTone.WELCOMING, MessageTone.PERSONALIZED],
            CommunicationStyle.SUPPORTIVE: [MessageTone.FOLLOW_UP, MessageTone.ENCOURAGING],
            CommunicationStyle.DIRECT: [MessageTone.INFORMATIVE, MessageTone.URGENT],
            CommunicationStyle.NURTURING: [MessageTone.WELCOMING, MessageTone.FOLLOW_UP]
        }
        
        compatible_tones = tone_compatibility.get(communication_style, [])
        if template.tone in compatible_tones:
            score += 0.4
        
        # Engagement pattern matching
        if engagement_pattern == EngagementPattern.HIGHLY_ENGAGED:
            if template.tone == MessageTone.PERSONALIZED:
                score += 0.3
        elif engagement_pattern in [EngagementPattern.DECLINING, EngagementPattern.DORMANT]:
            if template.tone in [MessageTone.ENCOURAGING, MessageTone.FOLLOW_UP]:
                score += 0.3
        elif engagement_pattern == EngagementPattern.NEW_UNKNOWN:
            if template.tone == MessageTone.WELCOMING:
                score += 0.3
        
        # Age appropriateness
        if person_context.age:
            if person_context.age >= 65:
                if template.tone in [MessageTone.INFORMATIVE, MessageTone.APPRECIATION]:
                    score += 0.2
            elif person_context.age <= 30:
                if template.tone in [MessageTone.ENCOURAGING, MessageTone.PERSONALIZED]:
                    score += 0.2
        
        # Experience level matching
        if person_context.volunteer_history:
            hours = person_context.volunteer_history.get('total_hours', 0)
            if hours > 50 and template.tone == MessageTone.PERSONALIZED:
                score += 0.1
        
        return score