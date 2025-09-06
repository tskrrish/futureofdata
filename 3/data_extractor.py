"""
Intelligent Data Extractor for OCR Pipeline
Converts extracted text into structured volunteer/project data using AI and pattern matching
"""
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd

@dataclass
class VolunteerOpportunity:
    """Structured volunteer opportunity data"""
    title: str = ""
    description: str = ""
    organization: str = ""
    location: str = ""
    branch: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    start_date: str = ""
    end_date: str = ""
    times: List[str] = None
    requirements: List[str] = None
    skills_needed: List[str] = None
    age_requirement: str = ""
    background_check: bool = False
    training_required: bool = False
    time_commitment: str = ""
    category: str = ""
    volunteer_type: str = ""
    spots_available: int = 0
    recurring: bool = False
    confidence_score: float = 0.0

class DataExtractor:
    """Intelligent extractor that converts OCR text to structured volunteer data"""
    
    def __init__(self):
        # YMCA branch mapping
        self.ymca_branches = {
            'blue ash': 'Blue Ash YMCA',
            'me lyons': 'M.E. Lyons YMCA', 
            'lyons': 'M.E. Lyons YMCA',
            'campbell county': 'Campbell County YMCA',
            'campbell': 'Campbell County YMCA',
            'clippard': 'Clippard YMCA',
            'northeast': 'Northeast YMCA',
            'fairfield': 'Fairfield YMCA',
            'west chester': 'West Chester YMCA',
            'mason': 'Mason YMCA'
        }
        
        # Volunteer categories
        self.categories = {
            'youth': ['youth', 'kids', 'children', 'teen', 'camp', 'childcare', 'after school'],
            'fitness': ['fitness', 'exercise', 'gym', 'swim', 'pool', 'sports', 'coach'],
            'senior': ['senior', 'elderly', 'older adult', 'active older'],
            'events': ['event', 'fundraiser', 'gala', 'party', 'celebration', 'festival'],
            'administrative': ['office', 'admin', 'data', 'reception', 'phone', 'filing'],
            'facility': ['maintenance', 'clean', 'setup', 'facility', 'building'],
            'food': ['food', 'kitchen', 'meal', 'nutrition', 'cooking', 'dining'],
            'membership': ['membership', 'guest', 'front desk', 'welcome', 'registration']
        }
        
        # Common volunteer types
        self.volunteer_types = {
            'regular': ['ongoing', 'weekly', 'monthly', 'regular', 'consistent'],
            'seasonal': ['summer', 'winter', 'spring', 'fall', 'holiday', 'seasonal'],
            'one_time': ['one time', 'single', 'once', 'special event'],
            'project_based': ['project', 'campaign', 'initiative', 'program launch']
        }
        
        # Time commitment patterns
        self.time_patterns = {
            'low': ['1 hour', '2 hours', 'couple hours', 'few hours'],
            'medium': ['half day', '3-4 hours', 'morning', 'afternoon', 'evening'],
            'high': ['full day', 'all day', 'weekend', 'multiple days']
        }
    
    def extract_volunteer_opportunity(self, ocr_result: Dict[str, Any]) -> VolunteerOpportunity:
        """Main method to extract structured volunteer opportunity from OCR results"""
        try:
            raw_text = ocr_result.get('raw_text', '')
            structured_data = ocr_result.get('structured_data', {})
            
            if not raw_text.strip():
                return VolunteerOpportunity(confidence_score=0.0)
            
            # Extract individual components
            opportunity = VolunteerOpportunity()
            
            opportunity.title = self._extract_title(raw_text)
            opportunity.description = self._extract_description(raw_text)
            opportunity.organization = self._extract_organization(raw_text)
            opportunity.location, opportunity.branch = self._extract_location_and_branch(raw_text, structured_data)
            opportunity.contact_email = self._get_best_email(structured_data.get('emails', []))
            opportunity.contact_phone = self._get_best_phone(structured_data.get('phones', []))
            opportunity.start_date, opportunity.end_date = self._extract_date_range(structured_data.get('dates', []))
            opportunity.times = structured_data.get('times', [])
            opportunity.requirements = self._extract_enhanced_requirements(raw_text, structured_data)
            opportunity.skills_needed = self._extract_skills(raw_text)
            opportunity.age_requirement = self._extract_age_requirement(raw_text)
            opportunity.background_check = self._requires_background_check(raw_text)
            opportunity.training_required = self._requires_training(raw_text)
            opportunity.time_commitment = self._extract_time_commitment(raw_text)
            opportunity.category = self._classify_category(raw_text)
            opportunity.volunteer_type = self._classify_volunteer_type(raw_text)
            opportunity.spots_available = self._extract_spots_available(raw_text)
            opportunity.recurring = self._is_recurring(raw_text)
            
            # Calculate overall confidence
            opportunity.confidence_score = self._calculate_extraction_confidence(opportunity, ocr_result)
            
            return opportunity
            
        except Exception as e:
            print(f"❌ Data extraction failed: {e}")
            return VolunteerOpportunity(confidence_score=0.0)
    
    def _extract_title(self, text: str) -> str:
        """Extract the main title/header of the volunteer opportunity"""
        lines = text.split('\n')
        
        # Look for title patterns
        title_indicators = ['volunteer', 'opportunity', 'position', 'needed', 'help', 'assist']
        
        # First, try to find lines with title indicators
        for line in lines[:5]:  # Check first 5 lines
            line_clean = line.strip()
            if len(line_clean) > 10 and len(line_clean) < 100:
                line_lower = line_clean.lower()
                if any(indicator in line_lower for indicator in title_indicators):
                    return line_clean
        
        # Fallback: look for the longest line in the first few lines
        potential_titles = [line.strip() for line in lines[:3] if len(line.strip()) > 5]
        if potential_titles:
            return max(potential_titles, key=len)
        
        # Last resort: create title from keywords
        keywords = self._extract_keywords_from_text(text)
        if keywords:
            return f"Volunteer Opportunity - {', '.join(keywords[:3])}"
        
        return "Volunteer Opportunity"
    
    def _extract_description(self, text: str) -> str:
        """Extract the main description of the opportunity"""
        # Remove title and contact info to focus on description
        lines = text.split('\n')
        description_lines = []
        
        for line in lines:
            line_clean = line.strip()
            # Skip short lines, contact info, dates/times
            if (len(line_clean) > 20 and 
                not re.search(r'@|phone|call|\d{3}[-.]?\d{3}[-.]?\d{4}', line_clean.lower()) and
                not re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}:\d{2}', line_clean)):
                description_lines.append(line_clean)
        
        description = ' '.join(description_lines[:3])  # Take first 3 relevant lines
        return description[:500] if description else ""  # Limit length
    
    def _extract_organization(self, text: str) -> str:
        """Extract organization name (defaults to YMCA variants)"""
        text_lower = text.lower()
        
        # Look for YMCA mentions
        if 'ymca' in text_lower:
            # Try to find specific YMCA branch mentions
            for branch_key, branch_name in self.ymca_branches.items():
                if branch_key in text_lower:
                    return branch_name
            return "YMCA of Greater Cincinnati"
        
        # Look for other organization patterns
        org_patterns = [
            r'(?:^|\n)([A-Z][a-zA-Z\s&]+(?:Foundation|Organization|Center|Association|Society|Club))',
            r'([A-Z][a-zA-Z\s&]+)(?:\s+presents|\s+invites|\s+needs)'
        ]
        
        for pattern in org_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches:
                return matches[0].strip()
        
        return "YMCA of Greater Cincinnati"  # Default
    
    def _extract_location_and_branch(self, text: str, structured_data: Dict) -> Tuple[str, str]:
        """Extract location and determine YMCA branch"""
        addresses = structured_data.get('addresses', [])
        text_lower = text.lower()
        
        # First check for specific branch mentions
        branch = ""
        for branch_key, branch_name in self.ymca_branches.items():
            if branch_key in text_lower:
                branch = branch_name
                break
        
        # Get location from addresses or text
        location = ""
        if addresses:
            location = addresses[0]  # Take the first/best address
        else:
            # Look for location patterns in text
            location_patterns = [
                r'(?:at|location:|where:|address:)\s*([^\n,]+)',
                r'(\d+\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Dr|Drive))',
                r'([A-Za-z\s]+,\s*OH\s+\d{5})'
            ]
            
            for pattern in location_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    location = matches[0].strip()
                    break
        
        # If no branch found but location contains city names, infer branch
        if not branch and location:
            location_lower = location.lower()
            for branch_key, branch_name in self.ymca_branches.items():
                if branch_key.split()[0] in location_lower:  # Match city name
                    branch = branch_name
                    break
        
        return location, branch
    
    def _get_best_email(self, emails: List[str]) -> str:
        """Select the most relevant email address"""
        if not emails:
            return ""
        
        # Prefer YMCA or organization emails
        for email in emails:
            email_lower = email.lower()
            if any(domain in email_lower for domain in ['ymca', 'cincinnati', 'volunteer']):
                return email
        
        # Return first email if no preferred match
        return emails[0]
    
    def _get_best_phone(self, phones: List[str]) -> str:
        """Select the most relevant phone number"""
        if not phones:
            return ""
        
        # Prefer properly formatted numbers
        formatted_phones = [p for p in phones if re.match(r'\(\d{3}\)\s*\d{3}[-.]?\d{4}', p)]
        if formatted_phones:
            return formatted_phones[0]
        
        return phones[0]
    
    def _extract_date_range(self, dates: List[str]) -> Tuple[str, str]:
        """Extract start and end dates from date list"""
        if not dates:
            return "", ""
        
        if len(dates) == 1:
            return dates[0], ""
        
        # Sort dates and take first and last
        return dates[0], dates[-1] if len(dates) > 1 else ""
    
    def _extract_enhanced_requirements(self, text: str, structured_data: Dict) -> List[str]:
        """Extract detailed requirements beyond basic OCR extraction"""
        requirements = list(structured_data.get('requirements', []))
        text_lower = text.lower()
        
        # Additional requirement patterns
        additional_patterns = [
            r'(?:must|need|require|should)\s+(?:be|have)\s+([^.]*?)(?:\.|$)',
            r'(?:minimum|at least)\s+(\d+\s+years?\s+old)',
            r'(?:experience|background)\s+(?:in|with)\s+([^.]*?)(?:\.|$)',
            r'(?:able to|capable of|willing to)\s+([^.]*?)(?:\.|$)'
        ]
        
        for pattern in additional_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            requirements.extend([match.strip() for match in matches if len(match.strip()) > 3])
        
        # Remove duplicates and clean
        unique_requirements = []
        for req in requirements:
            clean_req = req.strip()
            if clean_req and clean_req not in unique_requirements and len(clean_req) < 200:
                unique_requirements.append(clean_req)
        
        return unique_requirements[:5]  # Limit to top 5
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract required or desired skills"""
        skills = []
        text_lower = text.lower()
        
        # Common volunteer skills
        skill_keywords = [
            'communication', 'customer service', 'leadership', 'teamwork', 
            'teaching', 'coaching', 'organizing', 'planning', 'computer',
            'bilingual', 'spanish', 'swim', 'first aid', 'cpr', 'lifeguard'
        ]
        
        # Skills mentioned in context
        skill_patterns = [
            r'(?:skills?|experience|knowledge)\s+(?:in|with|of)\s+([^.]*?)(?:\.|$)',
            r'(?:ability to|able to|capable of)\s+([^.]*?)(?:\.|$)'
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.extend([match.strip() for match in matches])
        
        # Direct keyword matches
        for skill in skill_keywords:
            if skill in text_lower:
                skills.append(skill.title())
        
        return list(set(skills))[:5]  # Remove duplicates, limit to 5
    
    def _extract_age_requirement(self, text: str) -> str:
        """Extract age requirements"""
        age_patterns = [
            r'(?:age|ages)\s*:?\s*(\d+\s*[-to+]\s*\d+|\d+\+?|\d+\s*and\s*(?:up|older))',
            r'(?:minimum|at least)\s+(\d+\s+years?\s+old)',
            r'(\d+)\s*[-–]\s*(\d+)\s*years?\s*old'
        ]
        
        for pattern in age_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    return f"{matches[0][0]}-{matches[0][1]}"
                return matches[0]
        
        # Check for adult/teen/youth mentions
        text_lower = text.lower()
        if 'adult' in text_lower and 'youth' not in text_lower:
            return "18+"
        elif 'teen' in text_lower:
            return "13-17"
        elif 'youth' in text_lower or 'children' in text_lower:
            return "Under 18"
        
        return ""
    
    def _requires_background_check(self, text: str) -> bool:
        """Determine if background check is required"""
        indicators = ['background check', 'background screening', 'clearance', 
                     'criminal check', 'police check']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators)
    
    def _requires_training(self, text: str) -> bool:
        """Determine if training is required"""
        indicators = ['training', 'orientation', 'certification', 'course',
                     'workshop', 'instruction', 'preparation']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators)
    
    def _extract_time_commitment(self, text: str) -> str:
        """Extract time commitment information"""
        text_lower = text.lower()
        
        # Direct time mentions
        time_patterns = [
            r'(\d+\s*[-–]\s*\d+\s*hours?\s*(?:per|each)?\s*(?:week|month|day)?)',
            r'(\d+\s*hours?\s*(?:per|each)?\s*(?:week|month|day))',
            r'(full\s*day|half\s*day|morning|afternoon|evening)',
            r'(\d+\s*hours?)'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        # Pattern-based classification
        for commitment_level, patterns in self.time_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return commitment_level.replace('_', ' ').title()
        
        return ""
    
    def _classify_category(self, text: str) -> str:
        """Classify the volunteer opportunity category"""
        text_lower = text.lower()
        
        # Score each category
        category_scores = {}
        for category, keywords in self.categories.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            return best_category.replace('_', ' ').title()
        
        return "General"
    
    def _classify_volunteer_type(self, text: str) -> str:
        """Classify the type of volunteer commitment"""
        text_lower = text.lower()
        
        # Score each type
        type_scores = {}
        for vol_type, keywords in self.volunteer_types.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                type_scores[vol_type] = score
        
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            return best_type.replace('_', ' ').title()
        
        return "Regular"
    
    def _extract_spots_available(self, text: str) -> int:
        """Extract number of volunteer spots available"""
        spot_patterns = [
            r'(?:need|looking for|seeking)\s+(\d+)\s+(?:volunteer|people|person)',
            r'(\d+)\s+(?:spots?|positions?|openings?)\s+available',
            r'up to\s+(\d+)\s+volunteer'
        ]
        
        for pattern in spot_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return int(matches[0])
                except ValueError:
                    continue
        
        return 0  # Unknown/unlimited
    
    def _is_recurring(self, text: str) -> bool:
        """Determine if this is a recurring opportunity"""
        recurring_indicators = ['weekly', 'monthly', 'ongoing', 'regular', 'every', 
                               'recurring', 'continuous', 'permanent']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in recurring_indicators)
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """Extract relevant keywords for fallback title generation"""
        text_lower = text.lower()
        all_keywords = []
        
        for category_keywords in self.categories.values():
            all_keywords.extend(category_keywords)
        
        found_keywords = [kw for kw in all_keywords if kw in text_lower]
        return found_keywords[:5]  # Return top 5
    
    def _calculate_extraction_confidence(self, opportunity: VolunteerOpportunity, 
                                       ocr_result: Dict[str, Any]) -> float:
        """Calculate confidence score for the extracted data"""
        confidence = 0.0
        total_factors = 0
        
        # OCR confidence (40% weight)
        ocr_conf = ocr_result.get('confidence', 0) / 100.0
        confidence += ocr_conf * 0.4
        total_factors += 0.4
        
        # Completeness factors (60% weight total)
        factors = {
            'title': 0.1 if opportunity.title and len(opportunity.title) > 5 else 0,
            'description': 0.1 if opportunity.description and len(opportunity.description) > 20 else 0,
            'contact': 0.1 if opportunity.contact_email or opportunity.contact_phone else 0,
            'location': 0.1 if opportunity.location or opportunity.branch else 0,
            'category': 0.1 if opportunity.category != "General" else 0,
            'requirements': 0.05 if opportunity.requirements else 0,
            'time_info': 0.05 if opportunity.times or opportunity.time_commitment else 0
        }
        
        confidence += sum(factors.values())
        total_factors += sum([0.1, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05])
        
        return min(1.0, confidence)
    
    def to_dict(self, opportunity: VolunteerOpportunity) -> Dict[str, Any]:
        """Convert VolunteerOpportunity to dictionary"""
        return {
            'title': opportunity.title,
            'description': opportunity.description,
            'organization': opportunity.organization,
            'location': opportunity.location,
            'branch': opportunity.branch,
            'contact_email': opportunity.contact_email,
            'contact_phone': opportunity.contact_phone,
            'start_date': opportunity.start_date,
            'end_date': opportunity.end_date,
            'times': opportunity.times or [],
            'requirements': opportunity.requirements or [],
            'skills_needed': opportunity.skills_needed or [],
            'age_requirement': opportunity.age_requirement,
            'background_check': opportunity.background_check,
            'training_required': opportunity.training_required,
            'time_commitment': opportunity.time_commitment,
            'category': opportunity.category,
            'volunteer_type': opportunity.volunteer_type,
            'spots_available': opportunity.spots_available,
            'recurring': opportunity.recurring,
            'confidence_score': opportunity.confidence_score,
            'extracted_at': datetime.now().isoformat()
        }