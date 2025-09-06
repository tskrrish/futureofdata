# Proximity-Based Matching with Travel Time & Transit Scoring

This feature enhances the YMCA Volunteer PathFinder system with intelligent location-based matching that considers travel time, transportation options, and public transit accessibility.

## 🌟 Features

### Core Functionality
- **Travel Time Calculations**: Estimates travel time for driving, walking, cycling, and public transit
- **Transit Accessibility Scoring**: Rates each YMCA branch for public transit access (0-1 scale)
- **Transportation Cost Estimation**: Calculates estimated costs for different travel modes
- **Multi-Modal Analysis**: Compares all transportation options for each location
- **Smart Re-ranking**: Enhances existing ML matches with proximity scoring

### Transportation Modes Supported
- **Driving**: Considers traffic and urban speeds (~35 km/h average)
- **Public Transit**: Includes walking to stops, waiting times, transfers (~20 km/h effective)
- **Walking**: Standard walking speed (~5 km/h)
- **Cycling**: Urban cycling speed (~15 km/h, added for fitness-interested users)

## 🏗️ Architecture

### Key Components

#### 1. `ProximityMatcher` Class
- **Location Management**: Stores and manages YMCA branch locations
- **Distance Calculations**: Haversine distance calculations between points
- **Travel Time Estimation**: Mode-specific travel time calculations  
- **Transit Scoring**: Accessibility scoring based on proximity to public transit
- **Cost Estimation**: Transportation cost calculations

#### 2. Enhanced `VolunteerMatchingEngine`
- **Proximity Integration**: Seamlessly integrates with existing ML matching
- **New Methods**:
  - `find_proximity_matches()`: Enhanced matching with location awareness
  - `get_location_analysis()`: Comprehensive location accessibility analysis
- **Smart Scoring**: Combines traditional matching (70%) with proximity (30%)

#### 3. API Integration
- **Enhanced Endpoints**: Existing `/api/match` now supports location-based matching
- **New Endpoint**: `/api/location-analysis` for detailed location analysis
- **Backward Compatible**: Works with existing API clients

## 📍 YMCA Branch Locations & Transit Scores

| Branch | Location | Transit Score | Description |
|--------|----------|---------------|-------------|
| **Central Community YMCA** | Downtown Cincinnati | 0.9 | Excellent transit access |
| **M.E. Lyons YMCA** | Oakley/Madison Rd | 0.8 | Good bus connections |
| **Clippard YMCA** | Westwood | 0.7 | Good bus access |
| **Blue Ash YMCA** | Blue Ash | 0.6 | Suburban, limited transit |
| **East Community YMCA** | East Cincinnati | 0.5 | Moderate transit |
| **Campbell County YMCA** | Newport, KY | 0.4 | Cross-river, limited transit |

## 🚀 Usage Examples

### Basic Proximity Matching

```python
from proximity_matcher import ProximityMatcher

# Initialize matcher
matcher = ProximityMatcher()

# User preferences
user_prefs = {
    'interests': 'youth development fitness',
    'transportation': {
        'has_car': True,
        'prefers_transit': False
    }
}

# Calculate proximity score for a branch
proximity_info = matcher.calculate_proximity_score(
    user_location='downtown cincinnati',
    branch_name='M.E. Lyons YMCA',
    user_preferences=user_prefs
)

print(f"Proximity Score: {proximity_info['score']:.3f}")
print(f"Best Travel Option: {proximity_info['best_option']['mode']}")
print(f"Travel Time: {proximity_info['best_option']['duration_minutes']} minutes")
```

### Enhanced Volunteer Matching

```python
from matching_engine import VolunteerMatchingEngine

# Initialize with volunteer data
matching_engine = VolunteerMatchingEngine(volunteer_data)
matching_engine.train_models()

# User preferences with location
preferences = {
    'age': 28,
    'interests': 'youth mentoring',
    'user_location': 'blue ash oh',
    'transportation': {'has_car': True}
}

# Get proximity-enhanced matches
matches = matching_engine.find_proximity_matches(
    user_preferences=preferences,
    user_location='blue ash oh',
    top_k=5
)

for match in matches:
    print(f"{match['project_name']} - Score: {match['score']:.3f}")
    print(f"Travel: {match['recommended_transport']} ({match['travel_time']} min)")
```

### Location Analysis

```python
# Comprehensive location analysis
analysis = matching_engine.get_location_analysis(
    user_location='downtown cincinnati',
    user_preferences={'transportation': {'has_car': False}}
)

print("Recommendations:")
for rec in analysis['recommendations']:
    print(f"- {rec}")

print("\nBest Branches by Proximity:")
for branch, info in list(analysis['branch_analysis'].items())[:3]:
    print(f"- {branch}: {info['score']:.3f} score")
```

## 🔌 API Integration

### Enhanced Match Endpoint

**POST** `/api/match`

```json
{
  "interests": "youth development",
  "user_location": "downtown cincinnati",
  "transportation": {
    "has_car": false,
    "prefers_transit": true
  },
  "time_commitment": 2
}
```

Response includes proximity information:
```json
{
  "ml_matches": [
    {
      "project_name": "Youth Mentoring Program",
      "score": 0.847,
      "proximity_info": {
        "score": 0.892,
        "best_option": {
          "mode": "transit",
          "duration_minutes": 18,
          "distance_km": 5.2
        }
      },
      "travel_time": 18,
      "recommended_transport": "transit"
    }
  ],
  "location_analysis": {...},
  "proximity_enabled": true
}
```

### Location Analysis Endpoint

**POST** `/api/location-analysis`

```json
{
  "user_location": "newport ky",
  "preferences": {
    "transportation": {"has_car": true}
  }
}
```

## 🧮 Scoring Algorithm

### Proximity Score Components

1. **Distance Score (Weight varies by transport preference)**
   - Formula: `max(0, 1 - (distance_km / 30))`
   - Zero score at 30km distance

2. **Time Score (Weight varies by transport preference)**
   - Formula: `max(0, 1 - (duration_minutes / 60))`
   - Zero score at 60 minutes travel time

3. **Transit Score (Higher weight for non-car users)**
   - Based on branch transit accessibility (0.4-0.9)
   - Distance penalty for longer transit routes

### User Preference Weighting

| User Type | Distance | Time | Transit |
|-----------|----------|------|---------|
| **Has Car** | 50% | 40% | 10% |
| **Prefers Transit** | 30% | 20% | 50% |
| **No Car** | 30% | 30% | 40% |

### Final Match Score Integration

`Enhanced Score = (Original ML Score × 0.7) + (Proximity Score × 0.3)`

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_proximity_matching.py
```

Tests include:
- Basic proximity calculations
- Transportation mode comparisons
- Transit accessibility analysis
- Integration with ML matching
- Location analysis functionality

## 🔧 Configuration

### Adding New YMCA Branches

Edit `proximity_matcher.py`:

```python
self.branch_locations['New Branch YMCA'] = Location(
    address='123 Main St, City, OH 45XXX',
    lat=39.xxxx, lng=-84.xxxx,
    name='New Branch YMCA'
)

self.transit_accessibility['New Branch YMCA'] = 0.7  # 0-1 score
```

### Customizing Transportation Costs

```python
def calculate_cost_estimate(self, distance_km: float, mode: TransportMode) -> float:
    if mode == TransportMode.DRIVING:
        return distance_km * 2 * 0.60  # $0.60/km roundtrip
    elif mode == TransportMode.TRANSIT:
        return 2.00 + (distance_km * 0.05)  # $2.00 base + distance
    # ... customize as needed
```

## 🚀 Future Enhancements

### Phase 2 Features
- **Real-time Transit Data**: Integration with Cincinnati Metro APIs
- **Google Maps Integration**: Real driving times and traffic conditions
- **Weather Considerations**: Adjusted scoring for weather-dependent transport
- **Parking Information**: Availability and cost at each branch
- **Accessibility Features**: Wheelchair/mobility considerations

### Phase 3 Features  
- **Route Optimization**: Multi-stop volunteer routing
- **Carpooling Integration**: Volunteer carpooling matching
- **Dynamic Pricing**: Real-time ride-share cost integration
- **Carbon Footprint**: Environmental impact scoring

## 📊 Analytics & Insights

The system tracks:
- **Proximity Usage**: How often location-based matching is used
- **Transportation Preferences**: Popular transport modes by area
- **Branch Accessibility**: Which branches are most/least accessible
- **Match Quality**: Improvement in match satisfaction with proximity

## 🤝 Integration Points

### With Existing Systems
- **ML Matching Engine**: Seamlessly enhances existing algorithms
- **Database**: Stores location preferences and analytics
- **API**: Backward-compatible with existing clients
- **AI Assistant**: Location-aware conversation context

### With External Systems
- **VolunteerMatters**: Could integrate branch availability data
- **Cincinnati Metro**: Real-time transit information
- **Google Maps**: Real-time traffic and directions
- **Weather APIs**: Weather-adjusted recommendations

## 📈 Impact Metrics

Expected improvements:
- **25% increase** in volunteer retention (better location fit)
- **30% reduction** in travel-related volunteer dropouts  
- **20% increase** in match satisfaction scores
- **15% more** transit-dependent volunteers engaged

---

*This proximity matching feature makes volunteering more accessible by intelligently considering how volunteers can actually reach their volunteer opportunities, resulting in better matches and higher volunteer satisfaction.*