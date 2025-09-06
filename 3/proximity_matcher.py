"""
Proximity-Based Matching with Travel Time & Transit Scoring
Enhances volunteer matching by considering geographic proximity, travel time, and public transit accessibility
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import math
import asyncio
import aiohttp
import json
from dataclasses import dataclass
from enum import Enum

class TransportMode(Enum):
    DRIVING = "driving"
    WALKING = "walking"
    TRANSIT = "transit"
    CYCLING = "bicycling"

@dataclass
class Location:
    """Represents a geographic location"""
    address: str
    lat: float
    lng: float
    name: Optional[str] = None

@dataclass
class TravelInfo:
    """Travel information between two locations"""
    distance_km: float
    duration_minutes: int
    transport_mode: TransportMode
    transit_score: float = 0.0  # 0-1 score for transit accessibility
    cost_estimate: float = 0.0  # Estimated cost (gas, transit fare, etc.)

class ProximityMatcher:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize proximity matcher with optional Google Maps API key for real travel times
        If no API key provided, will use haversine distance calculations
        """
        self.api_key = api_key
        self.use_real_apis = api_key is not None
        
        # YMCA branch locations (Cincinnati area)
        self.branch_locations = {
            'Blue Ash YMCA': Location(
                address='4449 Cooper Rd, Blue Ash, OH 45242',
                lat=39.2320, lng=-84.3783, name='Blue Ash YMCA'
            ),
            'M.E. Lyons YMCA': Location(
                address='3447 Madison Rd, Cincinnati, OH 45209',
                lat=39.1312, lng=-84.4569, name='M.E. Lyons YMCA'
            ),
            'Campbell County YMCA': Location(
                address='2.05 Dave Cowens Dr, Newport, KY 41071',
                lat=39.0917, lng=-84.4686, name='Campbell County YMCA'
            ),
            'Clippard YMCA': Location(
                address='2143 Ferguson Rd, Cincinnati, OH 45238',
                lat=39.1570, lng=-84.6370, name='Clippard YMCA'
            ),
            'Central Community YMCA': Location(
                address='2055 Reading Rd, Cincinnati, OH 45202',
                lat=39.1209, lng=-84.5037, name='Central Community YMCA'
            ),
            'East Community YMCA': Location(
                address='4721 E Galbraith Rd, Cincinnati, OH 45236',
                lat=39.2084, lng=-84.3542, name='East Community YMCA'
            )
        }
        
        # Transit accessibility scores (based on proximity to bus routes/metro)
        self.transit_accessibility = {
            'Blue Ash YMCA': 0.6,  # Suburban location, limited transit
            'M.E. Lyons YMCA': 0.8,  # Urban location, good bus access
            'Campbell County YMCA': 0.4,  # Across river, limited transit
            'Clippard YMCA': 0.7,  # Good bus connections
            'Central Community YMCA': 0.9,  # Downtown, excellent transit
            'East Community YMCA': 0.5   # Suburban, moderate transit
        }
        
    def haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate haversine distance between two points in kilometers"""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Simple geocoding for common Cincinnati area locations
        In production, would use Google Geocoding API
        """
        # Common Cincinnati area geocoding
        location_map = {
            'cincinnati': (39.1031, -84.5120),
            'blue ash': (39.2320, -84.3783),
            'oakley': (39.1312, -84.4569),
            'newport': (39.0917, -84.4686),
            'covington': (39.0837, -84.5085),
            'norwood': (39.1556, -84.4594),
            'mount adams': (39.1103, -84.4936),
            'over-the-rhine': (39.1167, -84.5167),
            'downtown': (39.0997, -84.5122),
            'westwood': (39.1570, -84.6370),
            'clifton': (39.1353, -84.5183),
            'walnut hills': (39.1150, -84.4850)
        }
        
        address_lower = address.lower()
        for location, coords in location_map.items():
            if location in address_lower:
                return coords
        
        # Default to Cincinnati center if no match
        return (39.1031, -84.5120)
    
    def estimate_travel_time(self, distance_km: float, mode: TransportMode) -> int:
        """Estimate travel time based on distance and transportation mode"""
        if mode == TransportMode.DRIVING:
            # Account for city traffic, average 35 km/h in urban areas
            speed_kmh = 35
        elif mode == TransportMode.WALKING:
            speed_kmh = 5
        elif mode == TransportMode.CYCLING:
            speed_kmh = 15
        elif mode == TransportMode.TRANSIT:
            # Transit includes walking to stops, waiting, transfers
            speed_kmh = 20  # Effective speed including waits
        else:
            speed_kmh = 35  # Default to driving
        
        return int((distance_km / speed_kmh) * 60)  # Convert to minutes
    
    def calculate_transit_score(self, origin: Location, destination: Location, 
                              branch_name: str) -> float:
        """Calculate transit accessibility score between locations"""
        base_score = self.transit_accessibility.get(branch_name, 0.5)
        
        # Distance penalty - transit becomes less viable for longer distances
        distance = self.haversine_distance(origin.lat, origin.lng, 
                                         destination.lat, destination.lng)
        
        if distance > 25:  # > 25km
            distance_penalty = 0.3
        elif distance > 15:  # > 15km
            distance_penalty = 0.1
        elif distance > 10:  # > 10km
            distance_penalty = 0.05
        else:
            distance_penalty = 0
        
        return max(0, base_score - distance_penalty)
    
    def calculate_cost_estimate(self, distance_km: float, mode: TransportMode) -> float:
        """Estimate travel cost in USD"""
        if mode == TransportMode.DRIVING:
            # Gas + wear: ~$0.60 per km roundtrip
            return distance_km * 2 * 0.60
        elif mode == TransportMode.TRANSIT:
            # Cincinnati Metro bus fare: $1.00 per ride, assume roundtrip
            return 2.00 + (distance_km * 0.05)  # Small distance fee
        elif mode in [TransportMode.WALKING, TransportMode.CYCLING]:
            return 0.0  # Free
        else:
            return distance_km * 2 * 0.60  # Default to driving cost
    
    async def get_real_travel_info(self, origin: Location, destination: Location, 
                                  mode: TransportMode) -> Optional[TravelInfo]:
        """Get real travel information using Google Maps API (if available)"""
        if not self.use_real_apis:
            return None
        
        # In production, would call Google Maps Directions API
        # For now, return None to fall back to estimations
        return None
    
    def get_travel_info(self, origin: Location, destination: Location,
                       mode: TransportMode, branch_name: str) -> TravelInfo:
        """Get travel information between two locations"""
        distance = self.haversine_distance(origin.lat, origin.lng,
                                         destination.lat, destination.lng)
        
        duration = self.estimate_travel_time(distance, mode)
        transit_score = self.calculate_transit_score(origin, destination, branch_name)
        cost = self.calculate_cost_estimate(distance, mode)
        
        return TravelInfo(
            distance_km=distance,
            duration_minutes=duration,
            transport_mode=mode,
            transit_score=transit_score,
            cost_estimate=cost
        )
    
    def calculate_proximity_score(self, user_location: str, branch_name: str,
                                user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive proximity score for a branch"""
        
        # Geocode user location
        user_coords = self.geocode_address(user_location)
        if not user_coords:
            return {"score": 0.5, "travel_options": [], "reasons": ["Location not found"]}
        
        user_loc = Location(address=user_location, lat=user_coords[0], lng=user_coords[1])
        
        # Get branch location
        if branch_name not in self.branch_locations:
            return {"score": 0.5, "travel_options": [], "reasons": ["Branch location unknown"]}
        
        branch_loc = self.branch_locations[branch_name]
        
        # Calculate travel options
        travel_options = []
        transport_modes = [TransportMode.DRIVING, TransportMode.TRANSIT, TransportMode.WALKING]
        
        # Add cycling if user expresses fitness interest
        interests = user_preferences.get('interests', '').lower()
        if 'fitness' in interests or 'cycling' in interests or 'bike' in interests:
            transport_modes.append(TransportMode.CYCLING)
        
        for mode in transport_modes:
            travel_info = self.get_travel_info(user_loc, branch_loc, mode, branch_name)
            travel_options.append({
                'mode': mode.value,
                'distance_km': round(travel_info.distance_km, 1),
                'duration_minutes': travel_info.duration_minutes,
                'transit_score': round(travel_info.transit_score, 2),
                'cost_estimate': round(travel_info.cost_estimate, 2)
            })
        
        # Calculate overall proximity score
        driving_info = next(t for t in travel_options if t['mode'] == 'driving')
        transit_info = next(t for t in travel_options if t['mode'] == 'transit')
        
        # Base score from distance (closer = better)
        distance_score = max(0, 1 - (driving_info['distance_km'] / 30))  # 0 score at 30km
        
        # Time convenience score (shorter time = better)
        time_score = max(0, 1 - (driving_info['duration_minutes'] / 60))  # 0 score at 60min
        
        # Transit accessibility score
        transit_score = transit_info['transit_score']
        
        # User preference weighting
        transport_preferences = user_preferences.get('transportation', {})
        has_car = transport_preferences.get('has_car', True)
        prefers_transit = transport_preferences.get('prefers_transit', False)
        
        if prefers_transit:
            final_score = (distance_score * 0.3 + time_score * 0.2 + transit_score * 0.5)
        elif has_car:
            final_score = (distance_score * 0.5 + time_score * 0.4 + transit_score * 0.1)
        else:
            # No car, transit is important
            final_score = (distance_score * 0.3 + time_score * 0.3 + transit_score * 0.4)
        
        # Generate explanation
        reasons = []
        if driving_info['distance_km'] < 5:
            reasons.append("Very close to your location")
        elif driving_info['distance_km'] < 15:
            reasons.append("Conveniently located within the area")
        
        if driving_info['duration_minutes'] < 20:
            reasons.append("Short travel time by car")
        
        if transit_score > 0.7:
            reasons.append("Good public transit access")
        elif transit_score > 0.4:
            reasons.append("Moderate public transit access")
        
        if not reasons:
            reasons.append("Accessible location for volunteering")
        
        return {
            "score": round(final_score, 3),
            "travel_options": travel_options,
            "reasons": reasons,
            "best_option": self._get_best_travel_option(travel_options, user_preferences)
        }
    
    def _get_best_travel_option(self, travel_options: List[Dict], 
                               user_preferences: Dict) -> Dict:
        """Determine the best travel option for a user"""
        transport_prefs = user_preferences.get('transportation', {})
        has_car = transport_prefs.get('has_car', True)
        prefers_transit = transport_prefs.get('prefers_transit', False)
        
        if prefers_transit:
            # Find best transit option
            transit_opts = [t for t in travel_options if t['mode'] == 'transit']
            if transit_opts:
                return min(transit_opts, key=lambda x: x['duration_minutes'])
        
        if has_car:
            # Find driving option
            driving_opts = [t for t in travel_options if t['mode'] == 'driving']
            if driving_opts:
                return driving_opts[0]
        
        # Fallback to shortest duration
        return min(travel_options, key=lambda x: x['duration_minutes'])
    
    def enhance_project_matches(self, matches: List[Dict], user_location: str,
                              user_preferences: Dict) -> List[Dict]:
        """Enhance existing project matches with proximity scoring"""
        
        enhanced_matches = []
        
        for match in matches:
            enhanced_match = match.copy()
            branch_name = match.get('branch', '')
            
            if branch_name and user_location:
                proximity_info = self.calculate_proximity_score(
                    user_location, branch_name, user_preferences
                )
                
                # Integrate proximity score with existing match score
                original_score = match.get('score', 0.5)
                proximity_score = proximity_info['score']
                
                # Weight: 70% original matching, 30% proximity
                enhanced_score = (original_score * 0.7) + (proximity_score * 0.3)
                
                enhanced_match.update({
                    'score': round(enhanced_score, 3),
                    'proximity_info': proximity_info,
                    'travel_time': proximity_info['best_option']['duration_minutes'],
                    'travel_distance': proximity_info['best_option']['distance_km'],
                    'recommended_transport': proximity_info['best_option']['mode']
                })
                
                # Add proximity reasons to existing reasons
                proximity_reasons = proximity_info['reasons']
                existing_reasons = match.get('reasons', [])
                enhanced_match['reasons'] = existing_reasons + proximity_reasons
            
            enhanced_matches.append(enhanced_match)
        
        # Re-sort by enhanced score
        enhanced_matches.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return enhanced_matches
    
    def get_branch_accessibility_report(self) -> Dict[str, Any]:
        """Generate accessibility report for all branches"""
        
        report = {
            "branches": {},
            "transit_summary": {
                "high_transit_access": [],
                "moderate_transit_access": [],
                "low_transit_access": []
            }
        }
        
        for branch_name, location in self.branch_locations.items():
            transit_score = self.transit_accessibility[branch_name]
            
            branch_info = {
                "location": location.address,
                "transit_score": transit_score,
                "coordinates": {"lat": location.lat, "lng": location.lng}
            }
            
            # Categorize transit access
            if transit_score >= 0.7:
                report["transit_summary"]["high_transit_access"].append(branch_name)
                branch_info["transit_level"] = "High"
            elif transit_score >= 0.4:
                report["transit_summary"]["moderate_transit_access"].append(branch_name)
                branch_info["transit_level"] = "Moderate"
            else:
                report["transit_summary"]["low_transit_access"].append(branch_name)
                branch_info["transit_level"] = "Low"
            
            report["branches"][branch_name] = branch_info
        
        return report

# Example usage and testing
if __name__ == "__main__":
    # Initialize proximity matcher
    matcher = ProximityMatcher()
    
    # Test proximity scoring
    user_prefs = {
        'interests': 'youth development fitness',
        'transportation': {
            'has_car': True,
            'prefers_transit': False
        }
    }
    
    # Test with different locations
    test_locations = ['downtown cincinnati', 'blue ash', 'newport ky']
    
    for location in test_locations:
        print(f"\n=== Proximity Analysis for {location.title()} ===")
        
        for branch in matcher.branch_locations.keys():
            proximity_info = matcher.calculate_proximity_score(location, branch, user_prefs)
            print(f"\n{branch}:")
            print(f"  Score: {proximity_info['score']}")
            print(f"  Best travel: {proximity_info['best_option']['mode']} "
                  f"({proximity_info['best_option']['duration_minutes']} min)")
            print(f"  Reasons: {', '.join(proximity_info['reasons'])}")
    
    # Test branch accessibility report
    print("\n=== Branch Accessibility Report ===")
    report = matcher.get_branch_accessibility_report()
    
    for category, branches in report["transit_summary"].items():
        print(f"\n{category.replace('_', ' ').title()}: {', '.join(branches)}")