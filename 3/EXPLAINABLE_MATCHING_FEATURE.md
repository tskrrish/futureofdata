# Explainable Matching Feature

## Overview

The explainable matching feature provides detailed explanations for why volunteer opportunities match user preferences. It analyzes five key factors and presents visual indicators showing match strength with detailed reasoning.

## Key Features

### 1. Five Factor Analysis

#### Skills Alignment (35% weight)
- **Keywords Matching**: Analyzes user interests/skills against project requirements
- **Categories**: Youth development, fitness/wellness, events/admin, community service, creative arts, technical skills
- **Scoring**: Based on keyword overlap and specificity
- **Examples**: 
  - "Your youth development interests perfectly align with this project"
  - "Your fitness and wellness background is highly valuable here"

#### Proximity/Location (20% weight)
- **Branch Mapping**: Maps user location preferences to YMCA branches
- **Distance Categories**: Exact match, nearby, accessible
- **Branch Proximity**: Blue Ash area, Oakley area, Newport area, Western Hills area
- **Examples**:
  - "Located at your preferred Blue Ash branch"
  - "Conveniently located near your area at M.E. Lyons"

#### History/Experience Relevance (20% weight)
- **Branch Affinity**: Analyzes past volunteer locations
- **Category Affinity**: Looks at previous volunteer work types
- **Volunteer Type**: Matches based on Champion, Regular, Explorer, Newcomer patterns
- **Examples**:
  - "You've successfully volunteered at Blue Ash before"
  - "Great fit based on your Youth Development volunteer history"

#### Schedule Compatibility (15% weight)
- **Time Commitment**: Matches low/medium/high preferences
- **Availability**: Weekday, weekend, evening options
- **Session Frequency**: Multiple session opportunities
- **Examples**:
  - "Perfect for your flexible schedule with short time commitments"
  - "Ideal time commitment for regular volunteer involvement"

#### Experience Level Appropriateness (10% weight)
- **Beginner**: Well-established programs with support
- **Intermediate**: Moderate complexity opportunities
- **Advanced**: Leadership roles and high-impact positions
- **Examples**:
  - "Excellent support system for new volunteers"
  - "Excellent opportunity to utilize your volunteer expertise"

### 2. Visual Match Indicators

#### Factor Bars
- Color-coded progress bars for each factor (0-100%)
- Skills: Purple
- Location: Cyan
- History: Orange
- Schedule: Pink
- Experience: Green

#### Match Score Classification
- **Excellent Match** (80-100%): Green badge
- **Good Match** (60-79%): Orange badge
- **Fair Match** (Below 60%): Gray badge

### 3. Interactive UI Components

#### Match Cards
- Project name and branch
- Overall compatibility score
- Visual factor breakdown
- Primary reasons list
- Expandable detailed analysis

#### Detailed Breakdown
- Skill categories matched
- Location distance category
- Historical alignment details
- Schedule compatibility metrics
- Experience level appropriateness

## Technical Implementation

### Backend (matching_engine.py)

```python
def _explain_match(self, preferences, project) -> Dict[str, Any]:
    # Returns comprehensive explanation with:
    # - primary_reasons: List of top match reasons
    # - match_factors: Percentage scores for each factor
    # - compatibility_score: Overall match score (0-1)
    # - detailed_breakdown: In-depth analysis per factor
```

### Frontend (chat.html)

```javascript
function addExplainableMatch(match, rank) {
    // Creates interactive match card with:
    // - Visual factor bars
    // - Expandable details
    // - Color-coded scores
    // - Reason explanations
}
```

### API Integration (main.py)

The enhanced matching integrates seamlessly with existing endpoints:
- `/api/profile` - Profile analysis with enhanced recommendations
- `/api/match` - ML-based matching with explainable factors
- `/api/chat` - AI assistant with detailed match reasoning

## Usage Examples

### Example 1: Youth-Interested Newcomer
```
Skills Match: 85% - Your youth development interests perfectly align
Location: 95% - Located at your preferred Blue Ash branch
Experience: 70% - Good beginner-friendly environment with volunteer support
Schedule: 75% - Perfect for your flexible schedule with short time commitments
Level Fit: 90% - Excellent support system for new volunteers
```

### Example 2: Experienced Event Volunteer
```
Skills Match: 90% - Your event planning skills are exactly what this project needs
Location: 80% - Conveniently located near your area at Campbell County
History: 95% - You've successfully volunteered at Campbell County before
Schedule: 85% - Great opportunity for deeper volunteer engagement
Level Fit: 95% - Excellent opportunity to utilize your volunteer expertise
```

## Configuration

### Skill Keywords
Easily configurable keyword mappings in `_analyze_skills_match()`:
```python
skill_keywords = {
    'youth_development': ['youth', 'child', 'teen', 'mentoring', 'tutoring'],
    'fitness_wellness': ['fitness', 'exercise', 'wellness', 'health', 'sport'],
    # ... more categories
}
```

### Branch Proximity
Branch proximity mapping in `_analyze_proximity_match()`:
```python
branch_proximity = {
    'blue ash': ['blue ash', 'mason', 'sharonville', 'montgomery'],
    'm.e. lyons': ['oakley', 'hyde park', 'madeira', 'mariemont'],
    # ... more mappings
}
```

## Benefits

1. **Transparency**: Users understand why opportunities are recommended
2. **Trust**: Clear reasoning builds confidence in recommendations
3. **Personalization**: Detailed analysis shows individual preference matching
4. **Guidance**: Helps users understand what makes a good volunteer match
5. **Engagement**: Interactive UI encourages exploration of opportunities

## Future Enhancements

- Add geographic distance calculations
- Include real-time availability matching
- Implement machine learning feedback loops
- Add volunteer success prediction factors
- Include community impact metrics