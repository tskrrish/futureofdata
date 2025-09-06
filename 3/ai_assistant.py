"""
AI Assistant for Volunteer PathFinder
Uses inference.net with meta-llama/llama-3.2-11b-instruct/fp-16
"""
import httpx
import json
import asyncio
from typing import Dict, List, Optional, Any
from config import settings
import pandas as pd

class VolunteerAIAssistant:
    def __init__(self):
        self.api_key = settings.INFERENCE_NET_API_KEY
        self.model = settings.INFERENCE_NET_MODEL
        self.base_url = settings.INFERENCE_NET_BASE_URL
        self.conversation_history = []
        self.volunteer_context = {}
        
        # YMCA and volunteer-specific knowledge
        self.ymca_knowledge = {
            "volunteer_page": settings.YMCA_VOLUNTEER_PAGE,
            "project_catalog": settings.VOLUNTEER_MATTERS_CATALOG,
            "interest_form": settings.VOLUNTEER_INTEREST_FORM,
            "volunteer_matters_register": "https://cincinnatiymca.volunteermatters.org/volunteer/register"
        }
        
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the AI assistant"""
        return """You are a friendly and knowledgeable AI assistant for the YMCA of Greater Cincinnati's Volunteer PathFinder system. Your role is to help people discover, understand, and connect with perfect volunteer opportunities.

PERSONALITY & TONE:
- Warm, enthusiastic, and encouraging
- Professional but approachable 
- Knowledgeable about YMCA values and volunteer opportunities
- Empathetic and understanding of different volunteer motivations
- Use emojis sparingly but appropriately to add warmth

YOUR EXPERTISE:
- YMCA volunteer opportunities across all Cincinnati branches
- Volunteer requirements, onboarding process, and credentials needed
- Matching volunteers to opportunities based on interests, skills, and availability
- Guiding users through VolunteerMatters registration
- Understanding volunteer motivations and addressing concerns

KEY RESOURCES:
- YMCA Volunteer Page: https://www.myy.org/volunteering
- VolunteerMatters Project Catalog: https://cincinnatiymca.volunteermatters.org/project-catalog
- Volunteer Interest Form: https://ymcacincinnati.qualtrics.com/jfe/form/SV_0JklTjQEJTQmS2i
- Registration: https://cincinnatiymca.volunteermatters.org/volunteer/register

CONVERSATION FLOW:
1. Warm greeting and understanding their volunteer interests
2. Ask clarifying questions about preferences, availability, skills
3. Provide personalized recommendations with explanations
4. Guide through next steps (registration, contact info, requirements)
5. Offer ongoing support and check-in opportunities

VOLUNTEER CATEGORIES AVAILABLE:
- Youth Development (mentoring, after-school programs, camps)
- Fitness & Wellness (group exercise, swimming, sports)
- Special Events (fundraisers, community events, holiday programs)
- Facility Support (maintenance, organization, greeting)
- Administrative (office support, data entry, communications)
- Competitive Sports (swim teams, coaching assistance)

BRANCHES:
- Blue Ash YMCA
- M.E. Lyons YMCA  
- Campbell County YMCA
- Clippard YMCA
- Youth Development & Education centers

Always provide specific, actionable next steps and make volunteering feel accessible and rewarding!"""
    
    async def chat(self, user_message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Main chat interface with the AI assistant"""
        
        # Build conversation context
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Inject volunteer profile context if available
        profile_ctx = self.volunteer_context.get("profile") if isinstance(self.volunteer_context, dict) else None
        if profile_ctx:
            try:
                profile_summary = profile_ctx.get("summary", "")
                recs = profile_ctx.get("recommendations", [])
                rec_lines = []
                for i, r in enumerate(recs[:3], 1):
                    name = r.get("project_name") or r.get("project") or "Opportunity"
                    branch = r.get("branch", "")
                    score = r.get("score")
                    rec_lines.append(f"{i}. {name} at {branch} (score: {score:.2f})" if score is not None else f"{i}. {name} at {branch}")
                profile_block = "\n".join([
                    "Volunteer profile context:",
                    profile_summary,
                    "Top recommendations:",
                    *rec_lines
                ])
                messages.append({"role": "system", "content": profile_block})
            except Exception:
                pass
        
        # Add conversation history if available
        for msg in self.conversation_history[-10:]:  # Keep last 10 messages for context
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Call inference.net API
            response = await self._call_inference_api(messages)
            
            if response and "content" in response:
                assistant_response = response["content"]
                
                # Update conversation history
                self.conversation_history.append({"role": "user", "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": assistant_response})
                
                return {
                    "response": assistant_response,
                    "success": True,
                    "conversation_id": conversation_id,
                    "suggestions": self._generate_quick_replies(user_message, assistant_response)
                }
            else:
                return {
                    "response": "I apologize, but I'm having trouble connecting right now. Please try again in a moment, or feel free to browse our volunteer opportunities directly at myy.org/volunteering.",
                    "success": False,
                    "error": "API response error"
                }
                
        except Exception as e:
            print(f"Error in chat: {e}")
            return {
                "response": "I'm experiencing some technical difficulties. While I get back online, you can explore volunteer opportunities at https://cincinnatiymca.volunteermatters.org/project-catalog or contact your local YMCA branch directly.",
                "success": False,
                "error": str(e)
            }
    
    async def _call_inference_api(self, messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Call the inference.net API with Llama model (OpenAI-compatible format)"""
        
        # Check if API key is available
        if not self.api_key:
            print("⚠️ No inference.net API key configured. Using fallback response.")
            return {
                "content": "I'm here to help you find perfect volunteer opportunities at the YMCA! While my AI features are currently limited, I can still guide you to the right resources and help you get connected with meaningful volunteer work.",
                "usage": {}
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "VolunteerPathFinder/1.0"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": False,
            "presence_penalty": 0.1,
            "frequency_penalty": 0.1
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                print(f"🤖 Calling inference.net API with model: {self.model}")
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                print(f"📡 API Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"]["content"]
                        usage = data.get("usage", {})
                        
                        print(f"✅ AI Response received: {len(content)} characters")
                        print(f"📊 Token usage: {usage}")
                        
                        return {
                            "content": content,
                            "usage": usage
                        }
                    else:
                        print(f"❌ Unexpected API response format: {data}")
                        return None
                        
                elif response.status_code == 401:
                    print("❌ API Authentication failed. Please check your inference.net API key.")
                    return None
                    
                elif response.status_code == 429:
                    print("⚠️ Rate limit exceeded. Please try again later.")
                    return None
                    
                else:
                    print(f"❌ API Error {response.status_code}: {response.text}")
                    return None
                    
            except httpx.TimeoutException:
                print("⏰ API request timed out. The model may be busy.")
                return None
                
            except httpx.ConnectError:
                print("🌐 Connection error. Please check your internet connection.")
                return None
                
            except Exception as e:
                print(f"❌ Unexpected error calling inference.net: {e}")
                return None
    
    def _generate_quick_replies(self, user_message: str, assistant_response: str) -> List[str]:
        """Generate contextual quick reply suggestions"""
        user_lower = user_message.lower()
        response_lower = assistant_response.lower()
        
        suggestions = []
        
        # Based on user input patterns
        if "interested" in user_lower or "want to" in user_lower:
            suggestions.extend([
                "Tell me more about requirements",
                "How do I sign up?",
                "What's the time commitment?"
            ])
        
        if "youth" in user_lower or "kids" in user_lower:
            suggestions.extend([
                "Show me youth programs",
                "What background checks are needed?",
                "When are youth programs typically scheduled?"
            ])
        
        if "fitness" in user_lower or "exercise" in user_lower:
            suggestions.extend([
                "Fitness volunteer opportunities",
                "Do I need to be certified?",
                "What are the time slots?"
            ])
        
        if "schedule" in user_lower or "time" in user_lower:
            suggestions.extend([
                "Show flexible opportunities",
                "Weekend volunteer options",
                "Evening opportunities"
            ])
        
        # Based on assistant response patterns
        if "registration" in response_lower or "sign up" in response_lower:
            suggestions.extend([
                "Help me register now",
                "What information do I need?",
                "Walk me through the process"
            ])
        
        if "branch" in response_lower or "location" in response_lower:
            suggestions.extend([
                "Show me all locations",
                "Which is closest to me?",
                "Compare branch programs"
            ])
        
        # Default helpful options
        default_suggestions = [
            "Browse all opportunities",
            "Help me find the perfect match",
            "Start my volunteer journey",
            "Contact a branch directly"
        ]
        
        # Return unique suggestions, prioritizing specific ones
        all_suggestions = suggestions + default_suggestions
        unique_suggestions = []
        for suggestion in all_suggestions:
            if suggestion not in unique_suggestions:
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:4]  # Return top 4 suggestions
    
    async def get_volunteer_recommendations(self, user_preferences: Dict[str, Any], volunteer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized volunteer recommendations using AI + data analysis"""
        
        # Analyze user preferences
        preferences_text = self._format_preferences_for_ai(user_preferences)
        
        # Create recommendation prompt
        recommendation_prompt = f"""Based on this person's preferences and our volunteer data, provide 3 specific volunteer opportunity recommendations:

USER PREFERENCES:
{preferences_text}

AVAILABLE DATA:
- Total unique projects: {len(volunteer_data.get('projects', []))}
- Top project categories: Youth Development, Fitness & Wellness, Special Events, Facility Support
- Available branches: Blue Ash, M.E. Lyons, Campbell County, Clippard, YDE
- Age range of current volunteers: 18-78 years
- Most successful volunteer types: Champions (100+ hours), Regular (10+ sessions), Explorers (3+ projects)

Please provide:
1. Top 3 specific recommendations with branch and project type
2. Brief explanation of why each is a good match
3. Expected time commitment and schedule
4. Any special requirements or credentials needed
5. One "stretch" opportunity that could help them grow

Format as a friendly, encouraging response that makes them excited to volunteer!"""

        try:
            # Get AI recommendations
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": recommendation_prompt}
            ]
            
            ai_response = await self._call_inference_api(messages)
            
            if ai_response:
                return {
                    "recommendations": ai_response["content"],
                    "success": True,
                    "data_insights": {
                        "total_projects": len(volunteer_data.get('projects', [])),
                        "total_volunteers": volunteer_data.get('insights', {}).get('total_volunteers', 0),
                        "avg_hours_per_volunteer": volunteer_data.get('insights', {}).get('avg_hours_per_volunteer', 0)
                    }
                }
            else:
                # Fallback to rule-based recommendations
                return await self._generate_fallback_recommendations(user_preferences, volunteer_data)
                
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return await self._generate_fallback_recommendations(user_preferences, volunteer_data)
    
    def _format_preferences_for_ai(self, preferences: Dict[str, Any]) -> str:
        """Format user preferences for AI processing"""
        formatted = []
        
        for key, value in preferences.items():
            if value:
                formatted.append(f"- {key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(formatted)
    
    async def _generate_fallback_recommendations(self, preferences: Dict[str, Any], volunteer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic recommendations if AI fails"""
        
        # Simple rule-based matching
        recommendations = []
        
        if preferences.get('interests'):
            interests = preferences['interests'].lower()
            if 'youth' in interests or 'children' in interests:
                recommendations.append("Youth Development programs at Blue Ash YMCA - perfect for mentoring and making a difference in young lives!")
            
            if 'fitness' in interests or 'health' in interests:
                recommendations.append("Group Exercise Volunteer at M.E. Lyons YMCA - help with fitness classes and support community wellness!")
            
            if 'event' in interests or 'community' in interests:
                recommendations.append("Special Events Volunteer - help with fundraisers and community celebrations across all branches!")
        
        if not recommendations:
            recommendations = [
                "Facility Volunteer - flexible schedule, multiple branches available",
                "Youth Development - after school programs, high impact opportunity",
                "Fitness Support - help with group exercise classes and equipment"
            ]
        
        return {
            "recommendations": "\n\n".join([f"{i+1}. {rec}" for i, rec in enumerate(recommendations[:3])]),
            "success": True,
            "fallback": True
        }
    
    def add_context(self, context_type: str, context_data: Any):
        """Add additional context to the assistant"""
        self.volunteer_context[context_type] = context_data
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.volunteer_context = {}
    
    async def get_onboarding_guidance(self, step: str = "start") -> Dict[str, Any]:
        """Provide step-by-step onboarding guidance"""
        
        onboarding_prompts = {
            "start": "A new volunteer wants to get started. Provide them with a clear, encouraging overview of the YMCA volunteer onboarding process, including the main steps and what to expect. Make it feel welcoming and not overwhelming.",
            
            "registration": "Guide someone through the VolunteerMatters registration process step-by-step. Be specific about what information they'll need and what to expect during registration.",
            
            "credentials": "Explain the different credentials and background checks required for YMCA volunteering. Help them understand why these are important and how to complete them.",
            
            "first_steps": "Someone has just registered and completed their credentials. What are their next steps to actually start volunteering? Help them feel prepared and excited for their first volunteer experience."
        }
        
        prompt = onboarding_prompts.get(step, onboarding_prompts["start"])
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = await self._call_inference_api(messages)
            
            if response:
                return {
                    "guidance": response["content"],
                    "success": True,
                    "step": step,
                    "next_steps": self._get_next_onboarding_steps(step)
                }
            else:
                return {
                    "guidance": self._get_fallback_guidance(step),
                    "success": False,
                    "step": step
                }
                
        except Exception as e:
            return {
                "guidance": self._get_fallback_guidance(step),
                "success": False,
                "error": str(e),
                "step": step
            }
    
    def _get_next_onboarding_steps(self, current_step: str) -> List[str]:
        """Get the next steps in the onboarding process"""
        step_flow = {
            "start": ["registration"],
            "registration": ["credentials"],
            "credentials": ["first_steps"],
            "first_steps": ["complete"]
        }
        
        return step_flow.get(current_step, [])
    
    def _get_fallback_guidance(self, step: str) -> str:
        """Provide fallback guidance if AI is unavailable"""
        
        fallback_guidance = {
            "start": """Welcome to YMCA volunteering! 🎉 Here's how to get started:

1. **Explore Opportunities**: Browse our volunteer opportunities at cincinnatiymca.volunteermatters.org/project-catalog
2. **Register**: Create your account at cincinnatiymca.volunteermatters.org/volunteer/register  
3. **Complete Requirements**: Finish any required credentials or training
4. **Start Volunteering**: Connect with branch staff and begin your volunteer journey!

Each step is designed to ensure you have the best volunteer experience possible. Ready to make a difference?""",

            "registration": """Here's how to register with VolunteerMatters:

1. **Visit**: https://cincinnatiymca.volunteermatters.org/volunteer/register
2. **Create Account**: Provide your basic information (name, email, phone)
3. **Fill Profile**: Add your interests, skills, and availability
4. **Select Interests**: Choose volunteer areas that interest you
5. **Submit**: Complete your registration

You'll receive a confirmation email once registered. The whole process takes about 5-10 minutes!""",

            "credentials": """Credential requirements vary by volunteer role:

**Basic Requirements (All Volunteers):**
- Volunteer Relationship Agreement
- Liability Waiver  
- Child Protection Policy (if working with minors)

**Additional Requirements (Role-Specific):**
- Background Check (youth programs)
- Interview (leadership positions)
- Special Training (program-specific)

These requirements help ensure safety for everyone and prepare you for success!""",

            "first_steps": """Congratulations on completing your registration! 🎉

**What's Next:**
1. **Check Your Email**: Look for welcome messages and opportunity matches
2. **Browse Projects**: Review available opportunities in your areas of interest
3. **Connect**: Reach out to branch coordinators for projects you're interested in
4. **Schedule**: Set up your first volunteer session
5. **Prepare**: Ask about what to bring or expect for your first day

Your volunteer coordinator will help guide you through everything. Welcome to the YMCA volunteer family!"""
        }
        
        return fallback_guidance.get(step, "Please contact your local YMCA branch for assistance with volunteering!")

# Example usage
async def test_assistant():
    assistant = VolunteerAIAssistant()
    
    # Test basic chat
    response = await assistant.chat("Hi! I'm interested in volunteering with youth programs.")
    print("Chat Response:", response)
    
    # Test onboarding guidance
    guidance = await assistant.get_onboarding_guidance("start")
    print("Onboarding Guidance:", guidance)

if __name__ == "__main__":
    asyncio.run(test_assistant())
