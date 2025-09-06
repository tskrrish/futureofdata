#!/usr/bin/env python3
"""
Branch-Aware Data Seeder
Advanced synthetic data generation with branch-specific characteristics and database integration
"""

import sys
import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from synthetic_data_generator import SyntheticDataGenerator, BRANCHES, PROJECT_CATEGORIES

# Add the database module path
sys.path.append('3')
try:
    from database import VolunteerDatabase
except ImportError:
    print("⚠️  Database module not available. Some features will be limited.")
    VolunteerDatabase = None

class BranchAwareSeeder:
    """Advanced seeding with branch-specific characteristics and database integration"""
    
    def __init__(self):
        self.generator = SyntheticDataGenerator()
        self.db = VolunteerDatabase() if VolunteerDatabase else None
        
        # Branch-specific characteristics
        self.branch_profiles = {
            "Blue Ash YMCA": {
                "region": "North",
                "size": "Large",
                "demographics": {"age_range": (25, 65), "member_ratio": 0.7},
                "popular_programs": ["Youth Sports", "Fitness Classes", "Summer Camps"],
                "volunteer_multiplier": 1.2
            },
            "Central Parkway YMCA": {
                "region": "Central", 
                "size": "Medium",
                "demographics": {"age_range": (20, 70), "member_ratio": 0.6},
                "popular_programs": ["Community Services", "Senior Programs", "Health Education"],
                "volunteer_multiplier": 1.0
            },
            "Clippard YMCA": {
                "region": "West",
                "size": "Medium",
                "demographics": {"age_range": (18, 55), "member_ratio": 0.65},
                "popular_programs": ["Teen Engagement", "After School Programs", "Youth Development"],
                "volunteer_multiplier": 0.9
            },
            "M.E. Lyons YMCA": {
                "region": "South",
                "size": "Small",
                "demographics": {"age_range": (30, 75), "member_ratio": 0.8},
                "popular_programs": ["Senior Programs", "Community Outreach", "Health & Wellness"],
                "volunteer_multiplier": 0.8
            },
            "R.C. Durre YMCA": {
                "region": "East",
                "size": "Large", 
                "demographics": {"age_range": (22, 60), "member_ratio": 0.65},
                "popular_programs": ["Youth Development", "Aquatics", "Family Programs"],
                "volunteer_multiplier": 1.1
            },
            "Campbell County YMCA": {
                "region": "North",
                "size": "Medium",
                "demographics": {"age_range": (25, 65), "member_ratio": 0.5},
                "popular_programs": ["Community Services", "Educational Support", "Food Service"],
                "volunteer_multiplier": 0.7
            },
            "Powel Crosley YMCA": {
                "region": "West",
                "size": "Large",
                "demographics": {"age_range": (20, 70), "member_ratio": 0.75},
                "popular_programs": ["Fundraising", "Event Support", "Corporate Partnerships"],
                "volunteer_multiplier": 1.3
            },
            "Gamble-Nippert YMCA": {
                "region": "Central",
                "size": "Small",
                "demographics": {"age_range": (18, 50), "member_ratio": 0.45},
                "popular_programs": ["Youth Sports", "Teen Engagement", "Community Services"],
                "volunteer_multiplier": 0.6
            }
        }
    
    def generate_branch_realistic_data(self, branch_name: str, volunteer_count: int, 
                                     start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """Generate realistic data based on branch characteristics"""
        
        if start_date is None:
            start_date = datetime(2025, 1, 1)
        if end_date is None:
            end_date = datetime(2025, 12, 31)
        
        # Get branch profile
        profile = self.branch_profiles.get(branch_name, {
            "demographics": {"age_range": (18, 70), "member_ratio": 0.6},
            "popular_programs": list(PROJECT_CATEGORIES.keys())[:3],
            "volunteer_multiplier": 1.0
        })
        
        print(f"🏢 Generating {volunteer_count} volunteers for {branch_name}")
        print(f"   📊 Profile: {profile.get('size', 'Medium')} branch in {profile.get('region', 'Unknown')} region")
        print(f"   👥 Member ratio: {profile['demographics']['member_ratio']*100:.0f}%")
        
        # Create custom generator for this branch
        branch_generator = BranchSpecificGenerator(branch_name, profile)
        volunteers = []
        
        total_days = (end_date - start_date).days
        
        for i in range(volunteer_count):
            # Generate date
            random_days = branch_generator.weighted_date_selection(total_days)
            volunteer_date = start_date + timedelta(days=random_days)
            
            # Generate volunteer with branch-specific characteristics
            volunteer = branch_generator.generate_branch_volunteer(volunteer_date)
            volunteers.append(volunteer)
            
            if (i + 1) % 100 == 0:
                print(f"   ✨ Generated {i + 1}/{volunteer_count} volunteers")
        
        # Sort by date
        volunteers.sort(key=lambda x: x["Date"])
        
        return volunteers
    
    async def seed_database(self, volunteers: List[Dict[str, Any]], clear_existing: bool = False) -> bool:
        """Seed the Supabase database with volunteer data"""
        
        if not self.db or not self.db._is_available():
            print("❌ Database not available for seeding")
            return False
        
        print(f"🗄️  Seeding database with {len(volunteers)} volunteer records...")
        
        try:
            # Clear existing data if requested
            if clear_existing:
                print("🗑️  Clearing existing volunteer data...")
                # This would require additional database methods to clear tables
                
            success_count = 0
            error_count = 0
            
            for i, vol in enumerate(volunteers):
                try:
                    # Convert volunteer data to database format
                    user_data = {
                        "email": vol["Email"],
                        "first_name": vol["First Name"],
                        "last_name": vol["Last Name"],
                        "phone": str(vol["Mobile"]) if vol["Mobile"] else None,
                        "age": vol["Age"],
                        "gender": vol["Gender"],
                        "city": vol["Home City"],
                        "state": vol["Home State"],
                        "zip_code": vol["Home Postal Code"],
                        "is_ymca_member": vol["Are you a YMCA member?"] == "Yes",
                        "member_branch": vol["Member Branch"] if vol["Member Branch"] else None
                    }
                    
                    # Create user
                    user = await self.db.create_user(user_data)
                    
                    if user:
                        # Save volunteer preferences
                        preferences = {
                            "interests": vol["Project Tags"],
                            "availability": {"weekday": True, "weekend": True},
                            "time_commitment": 2,  # Medium
                            "location_preference": vol["Branch"],
                            "experience_level": 2,  # Some experience
                            "volunteer_type": "regular"
                        }
                        
                        await self.db.save_user_preferences(user["id"], preferences)
                        
                        # Create volunteer match record
                        match_data = [{
                            "project_name": vol["Project"],
                            "branch": vol["Branch"],
                            "category": vol["Project Tags"],
                            "score": 0.85,  # High match score
                            "reasons": [f"Location match: {vol['Branch']}", f"Interest in: {vol['Project Tags']}"]
                        }]
                        
                        await self.db.save_volunteer_matches(user["id"], match_data)
                        
                        success_count += 1
                    else:
                        error_count += 1
                        
                    if (i + 1) % 50 == 0:
                        print(f"   💾 Processed {i + 1}/{len(volunteers)} records")
                        
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:  # Only show first few errors
                        print(f"   ⚠️  Error processing volunteer {i+1}: {str(e)[:100]}")
            
            print(f"\n✅ Database seeding complete!")
            print(f"   📊 Success: {success_count} records")
            print(f"   ⚠️  Errors: {error_count} records")
            
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Database seeding failed: {e}")
            return False
    
    def generate_multi_branch_scenario(self, scenario_name: str) -> List[Dict[str, Any]]:
        """Generate data for specific multi-branch scenarios"""
        
        scenarios = {
            "regional_comparison": {
                "description": "Compare volunteer engagement across regions",
                "branches": {
                    "Blue Ash YMCA": 300,      # North - High engagement
                    "Central Parkway YMCA": 250,  # Central - Medium 
                    "Clippard YMCA": 200,      # West - Medium
                    "M.E. Lyons YMCA": 150,   # South - Lower
                }
            },
            "size_analysis": {
                "description": "Analyze volunteer patterns by branch size",
                "branches": {
                    "Blue Ash YMCA": 400,      # Large
                    "Powel Crosley YMCA": 350,  # Large
                    "Central Parkway YMCA": 250,  # Medium
                    "Clippard YMCA": 200,      # Medium
                    "M.E. Lyons YMCA": 100,   # Small
                    "Gamble-Nippert YMCA": 80   # Small
                }
            },
            "program_focus": {
                "description": "Different branches with specialized program focus",
                "branches": {
                    "Blue Ash YMCA": 300,      # Youth programs
                    "Central Parkway YMCA": 250,  # Senior services
                    "Powel Crosley YMCA": 200,    # Fundraising
                    "R.C. Durre YMCA": 250,      # Family programs
                }
            },
            "seasonal_trends": {
                "description": "Show seasonal volunteer trends across branches",
                "branches": {
                    "Blue Ash YMCA": 200,
                    "Central Parkway YMCA": 200,
                    "Clippard YMCA": 200,
                    "M.E. Lyons YMCA": 150,
                    "R.C. Durre YMCA": 150,
                }
            }
        }
        
        if scenario_name not in scenarios:
            print(f"❌ Unknown scenario: {scenario_name}")
            print(f"Available scenarios: {', '.join(scenarios.keys())}")
            return []
        
        scenario = scenarios[scenario_name]
        print(f"🎬 Generating scenario: {scenario_name}")
        print(f"📋 {scenario['description']}")
        
        all_volunteers = []
        
        for branch_name, volunteer_count in scenario["branches"].items():
            branch_volunteers = self.generate_branch_realistic_data(branch_name, volunteer_count)
            all_volunteers.extend(branch_volunteers)
        
        # Sort by date
        all_volunteers.sort(key=lambda x: x["Date"])
        
        print(f"\n🎯 Scenario '{scenario_name}' generated!")
        print(f"   📊 Total volunteers: {len(all_volunteers)}")
        print(f"   🏢 Branches: {len(scenario['branches'])}")
        
        return all_volunteers
    
    def export_scenario(self, volunteers: List[Dict[str, Any]], scenario_name: str):
        """Export scenario data in multiple formats"""
        
        # Create scenario directory
        scenario_dir = f"generated_data/scenarios/{scenario_name}"
        os.makedirs(scenario_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export CSV
        csv_file = os.path.join(scenario_dir, f"{scenario_name}_{timestamp}.csv")
        json_file = os.path.join(scenario_dir, f"{scenario_name}_{timestamp}.json")
        
        self.generator.export_csv(volunteers, csv_file)
        self.generator.export_json(volunteers, json_file)
        
        # Export branch statistics
        stats_file = os.path.join(scenario_dir, f"{scenario_name}_stats_{timestamp}.json")
        stats = self.calculate_scenario_stats(volunteers)
        
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        # Export dashboard data
        dashboard_file = os.path.join(scenario_dir, f"{scenario_name}_dashboard.js")
        self.export_scenario_dashboard(volunteers, dashboard_file)
        
        print(f"\n📁 Scenario files exported to: {scenario_dir}")
        
        return scenario_dir
    
    def calculate_scenario_stats(self, volunteers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate detailed statistics for scenario"""
        
        branch_stats = {}
        total_hours = 0
        date_range_stats = {}
        
        for vol in volunteers:
            branch = vol["Branch"]
            hours = vol["Hours"]
            date = vol["Date"]
            month = date[:7]  # YYYY-MM
            
            # Branch stats
            if branch not in branch_stats:
                branch_stats[branch] = {
                    "volunteer_count": 0,
                    "total_hours": 0,
                    "avg_age": 0,
                    "member_ratio": 0,
                    "gender_split": {"Male": 0, "Female": 0},
                    "programs": {}
                }
            
            branch_stats[branch]["volunteer_count"] += 1
            branch_stats[branch]["total_hours"] += hours
            branch_stats[branch]["gender_split"][vol["Gender"]] += 1
            
            program = vol["Project Tags"]
            if program not in branch_stats[branch]["programs"]:
                branch_stats[branch]["programs"][program] = 0
            branch_stats[branch]["programs"][program] += 1
            
            # Date range stats
            if month not in date_range_stats:
                date_range_stats[month] = {"volunteers": 0, "hours": 0}
            date_range_stats[month]["volunteers"] += 1
            date_range_stats[month]["hours"] += hours
            
            total_hours += hours
        
        # Calculate averages and ratios
        for branch, stats in branch_stats.items():
            if stats["volunteer_count"] > 0:
                stats["avg_hours_per_volunteer"] = stats["total_hours"] / stats["volunteer_count"]
                stats["member_ratio"] = sum(1 for vol in volunteers if vol["Branch"] == branch and vol["Are you a YMCA member?"] == "Yes") / stats["volunteer_count"]
        
        return {
            "summary": {
                "total_volunteers": len(volunteers),
                "total_hours": total_hours,
                "avg_hours_per_volunteer": total_hours / len(volunteers),
                "total_branches": len(branch_stats),
                "date_range": f"{volunteers[0]['Date']} to {volunteers[-1]['Date']}"
            },
            "branch_breakdown": branch_stats,
            "monthly_trends": date_range_stats,
            "generated_at": datetime.now().isoformat()
        }
    
    def export_scenario_dashboard(self, volunteers: List[Dict[str, Any]], filepath: str):
        """Export scenario data for React dashboard"""
        
        dashboard_data = []
        
        for vol in volunteers:
            dashboard_record = {
                "branch": vol["Branch"].replace(" YMCA", ""),
                "hours": vol["Hours"],
                "assignee": f"{vol['First Name']} {vol['Last Name']}",
                "is_member": vol["Are you a YMCA member?"] == "Yes",
                "date": vol["Date"],
                "member_branch": vol["Member Branch"].replace(" YMCA", "") if vol["Member Branch"] else "",
                "project_tag": vol["Project Tags"],
                "project_catalog": vol["Need"].split(" - ")[0] if " - " in vol["Need"] else vol["Need"],
                "project": vol["Project"].split(" - ")[1] if " - " in vol["Project"] else vol["Project"],
                "category": vol["Project Tags"].split()[0] if vol["Project Tags"] else "General",
                "department": vol["Project Tags"]
            }
            dashboard_data.append(dashboard_record)
        
        js_content = f"""// Generated scenario data for dashboard
export const SCENARIO_DATA = {json.dumps(dashboard_data, indent=2)};

// Scenario statistics
export const SCENARIO_STATS = {json.dumps(self.calculate_scenario_stats(volunteers), indent=2, default=str)};
"""
        
        with open(filepath, 'w', encoding='utf-8') as jsfile:
            jsfile.write(js_content)

class BranchSpecificGenerator:
    """Generate volunteers with branch-specific characteristics"""
    
    def __init__(self, branch_name: str, profile: Dict[str, Any]):
        self.branch_name = branch_name
        self.profile = profile
        self.base_generator = SyntheticDataGenerator()
    
    def weighted_date_selection(self, total_days: int) -> int:
        """Select dates with realistic distribution (more recent activity)"""
        import random
        
        # Weight recent dates higher
        weights = [1.0 + (i / total_days) for i in range(total_days)]
        
        # Add seasonal patterns (summer camps in summer, etc.)
        for i in range(total_days):
            day_of_year = i % 365
            
            # Summer peak (days 150-240, roughly June-August)
            if 150 <= day_of_year <= 240:
                weights[i] *= 1.3
            
            # Holiday season low (days 330-365, late November-December)  
            elif 330 <= day_of_year <= 365:
                weights[i] *= 0.7
            
            # Spring activity (days 60-120, March-April)
            elif 60 <= day_of_year <= 120:
                weights[i] *= 1.2
        
        return random.choices(range(total_days), weights=weights)[0]
    
    def generate_branch_volunteer(self, volunteer_date: datetime) -> Dict[str, Any]:
        """Generate volunteer with branch-specific characteristics"""
        import random
        
        # Use branch profile to influence generation
        demographics = self.profile["demographics"]
        popular_programs = self.profile["popular_programs"]
        
        # Select program based on branch preferences
        if random.random() < 0.7:  # 70% chance of popular program
            category = random.choice(popular_programs)
        else:
            category = random.choice(list(PROJECT_CATEGORIES.keys()))
        
        project_type = random.choice(PROJECT_CATEGORIES[category])
        
        # Find branch object
        branch = next(b for b in BRANCHES if b["name"] == self.branch_name)
        
        # Generate base volunteer
        volunteer = self.base_generator.generate_volunteer(branch, category, project_type, volunteer_date)
        
        # Apply branch-specific modifications
        age_min, age_max = demographics["age_range"]
        volunteer["Age"] = random.randint(age_min, age_max)
        
        # Adjust member ratio
        is_member = random.random() < demographics["member_ratio"]
        volunteer["Are you a YMCA member?"] = "Yes" if is_member else "No"
        volunteer["Member Branch"] = self.branch_name if is_member else ""
        
        # Recalculate birth date based on new age
        birth_year = volunteer_date.year - volunteer["Age"]
        birth_date = datetime(birth_year, random.randint(1, 12), random.randint(1, 28))
        volunteer["Birth Date"] = birth_date.strftime("%Y-%m-%d")
        
        return volunteer

async def main():
    """CLI interface for branch-aware seeding"""
    
    print("🏢 Branch-Aware Data Seeder")
    print("=" * 50)
    
    seeder = BranchAwareSeeder()
    
    # Show available scenarios
    print("\n📋 Available Scenarios:")
    print("  1. regional_comparison - Compare across regions")
    print("  2. size_analysis - Analyze by branch size")  
    print("  3. program_focus - Specialized program focus")
    print("  4. seasonal_trends - Seasonal volunteer patterns")
    
    scenario = input("\n🎬 Enter scenario name: ").strip()
    
    if scenario:
        volunteers = seeder.generate_multi_branch_scenario(scenario)
        
        if volunteers:
            scenario_dir = seeder.export_scenario(volunteers, scenario)
            
            # Ask about database seeding
            if seeder.db and seeder.db._is_available():
                seed_db = input("\n💾 Seed database with this data? (y/n): ").strip().lower()
                if seed_db == 'y':
                    await seeder.seed_database(volunteers)

if __name__ == "__main__":
    asyncio.run(main())