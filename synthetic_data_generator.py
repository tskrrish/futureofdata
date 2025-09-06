#!/usr/bin/env python3
"""
One-Click Demo Seeding: Realistic Synthetic Data Generator
Generates realistic synthetic volunteer data across branches for demo purposes.
"""

import random
import csv
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid
import os

# Seeded random for consistent results
random.seed(42)

# Branch data based on real YMCA branches
BRANCHES = [
    {"name": "Blue Ash YMCA", "code": "4805", "region": "North"},
    {"name": "Central Parkway YMCA", "code": "4807", "region": "Central"},
    {"name": "Clippard YMCA", "code": "4813", "region": "West"},
    {"name": "M.E. Lyons YMCA", "code": "4817", "region": "South"},
    {"name": "R.C. Durre YMCA", "code": "4820", "region": "East"},
    {"name": "Campbell County YMCA", "code": "4825", "region": "North"},
    {"name": "Powel Crosley YMCA", "code": "4830", "region": "West"},
    {"name": "Gamble-Nippert YMCA", "code": "4835", "region": "Central"},
]

# Project categories and types
PROJECT_CATEGORIES = {
    "Youth Development": [
        "Youth Sports", "After School Programs", "Summer Camps", 
        "Teen Engagement", "Childcare Support", "Educational Support"
    ],
    "Health & Wellness": [
        "Senior Programs", "Fitness Classes", "Aquatics", 
        "Health Education", "Wellness Coaching"
    ],
    "Community Services": [
        "Food Service", "Event Support", "Community Outreach",
        "Volunteer Coordination", "Administrative Support"
    ],
    "Fundraising": [
        "Special Events", "Donor Relations", "Grant Writing",
        "Corporate Partnerships", "Campaign Support"
    ],
    "Branch Support": [
        "Facility Maintenance", "Reception", "Technology Support",
        "Membership Services", "Program Assistance"
    ]
}

# Realistic volunteer demographics
FIRST_NAMES = {
    "Male": ["James", "Michael", "Robert", "John", "David", "William", "Richard", "Joseph", "Thomas", "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Steven", "Paul", "Andrew", "Joshua", "Kenneth", "Kevin"],
    "Female": ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty", "Helen", "Sandra", "Donna", "Carol", "Ruth", "Sharon", "Michelle"]
}

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"
]

CITIES = [
    "Cincinnati", "Blue Ash", "Loveland", "Mason", "West Chester", "Fairfield", 
    "Hamilton", "Springdale", "Forest Park", "Norwood", "Milford", "Deer Park"
]

ETHNICITIES = ["White", "Black or African American", "Asian", "Hispanic or Latino", "Two or more races", "American Indian", "Pacific Islander"]

# T-Shirt sizes
T_SHIRT_SIZES = ["Small", "Medium", "Large", "X-Large", "2X-Large", "3X-Large", "Youth S", "Youth M", "Youth L"]

class SyntheticDataGenerator:
    """Generate realistic synthetic volunteer data"""
    
    def __init__(self, branch_filter: Optional[str] = None):
        self.branch_filter = branch_filter
        self.generated_emails = set()
        self.generated_ids = set()
        
    def generate_contact_id(self) -> str:
        """Generate a unique contact ID"""
        while True:
            contact_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=22))
            if contact_id not in self.generated_ids:
                self.generated_ids.add(contact_id)
                return contact_id
    
    def generate_email(self, first_name: str, last_name: str) -> str:
        """Generate a realistic email address"""
        domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "email.com"]
        
        # Different email patterns
        patterns = [
            f"{first_name.lower()}.{last_name.lower()}",
            f"{first_name.lower()}{last_name.lower()}",
            f"{first_name[0].lower()}{last_name.lower()}",
            f"{first_name.lower()}{random.randint(10, 99)}",
            f"{first_name.lower()}_{last_name.lower()}"
        ]
        
        while True:
            pattern = random.choice(patterns)
            domain = random.choice(domains)
            email = f"{pattern}@{domain}"
            
            if email not in self.generated_emails:
                self.generated_emails.add(email)
                return email
    
    def generate_volunteer(self, branch: Dict[str, str], project_category: str, project_type: str, date: datetime) -> Dict[str, Any]:
        """Generate a single volunteer record"""
        
        # Demographics
        gender = random.choice(["Male", "Female"])
        first_name = random.choice(FIRST_NAMES[gender])
        last_name = random.choice(LAST_NAMES)
        age = random.randint(16, 85)
        
        # Birth date calculation
        birth_year = date.year - age
        birth_date = datetime(birth_year, random.randint(1, 12), random.randint(1, 28))
        
        # Generate addresses in Cincinnati area
        address = f"{random.randint(1000, 9999)} {random.choice(['Oak', 'Main', 'Cedar', 'Pine', 'Elm', 'Maple', 'Park'])} {random.choice(['St', 'Ave', 'Dr', 'Ln', 'Ct', 'Way'])}"
        city = random.choice(CITIES)
        postal_code = f"45{random.randint(200, 299)}"
        
        # Contact info
        email = self.generate_email(first_name, last_name)
        mobile = f"1513{random.randint(2000000, 9999999)}"
        
        # YMCA membership
        is_member = random.choice([True, True, False])  # 2/3 chance of being a member
        member_branch = random.choice(BRANCHES)["name"] if is_member else ""
        
        # Volunteer assignment
        hours = round(random.uniform(0.5, 25.0), 1)
        assignment_id = random.randint(20000, 30000)
        
        # Project details
        project_name = f"{branch['name'].split()[0]} - {project_type} {random.choice(['Volunteer', 'Assistant', 'Coordinator', 'Support'])}"
        project_id = random.randint(700, 2000)
        
        # Credentials (realistic combinations)
        base_credentials = ["Volunteer Relationship Agreement*", "Liability Waiver*"]
        additional_credentials = []
        
        if project_category in ["Youth Development", "Community Services"]:
            additional_credentials.extend(["Child Protection Policy*", "Background Check"])
        
        if random.random() < 0.3:  # 30% chance
            additional_credentials.append("Interview")
            
        if random.random() < 0.2:  # 20% chance
            additional_credentials.extend(["Child Abuse Prevention Training for Volunteers", "Child Abuse Reporting Procedure"])
        
        credentials = ",".join(base_credentials + additional_credentials)
        
        return {
            "Date": date.strftime("%Y-%m-%d"),
            "Project": project_name,
            "Project ID": project_id,
            "Branch": branch["name"],
            "Branch Code": branch["code"],
            "Project Tags": project_category,
            "Type": "Position",
            "Need": f"{project_type} - Assigned {date.year}",
            "Assignment ID": assignment_id,
            "Assignee": f"{last_name}, {first_name}",
            "Contact ID": self.generate_contact_id(),
            "Last Name": last_name,
            "First Name": first_name,
            "Pledged": 1,
            "Fulfilled": 1,
            "Hours": hours,
            "Comments/Description": "",
            "Manually Reported": False,
            "Manually Reported By": "",
            "Email": email,
            "Active Credentials": credentials,
            "Home Address": address,
            "Home City": city,
            "Home State": "Ohio",
            "Home Postal Code": postal_code,
            "Home Country": "US",
            "Mobile": mobile,
            "Telephone": mobile if random.random() < 0.3 else "",  # 30% also have home phone
            "Organization": random.choice(["", "UC Health", "P&G", "Kroger", "Cincinnati Children's"]) if random.random() < 0.2 else "",
            "Age": age,
            "Birth Date": birth_date.strftime("%Y-%m-%d"),
            "Status": "Active",
            "Are you a YMCA member?": "Yes" if is_member else "No",
            "Member Branch": member_branch,
            "Primary Volunteering Branch/Site": branch["name"],
            "T-Shirt Size": random.choice(T_SHIRT_SIZES),
            "Are you a YMCA Employee?": "Yes" if random.random() < 0.05 else "No",  # 5% are employees
            "Race/Ethnicity": random.choice(ETHNICITIES),
            "Gender": gender
        }
    
    def generate_branch_data(self, branch: Dict[str, str], start_date: datetime, end_date: datetime, volunteers_per_branch: int) -> List[Dict[str, Any]]:
        """Generate volunteer data for a specific branch"""
        volunteers = []
        
        # Generate date range
        total_days = (end_date - start_date).days
        
        for _ in range(volunteers_per_branch):
            # Random date within range
            random_days = random.randint(0, total_days)
            volunteer_date = start_date + timedelta(days=random_days)
            
            # Choose project category and type based on branch characteristics
            category = random.choice(list(PROJECT_CATEGORIES.keys()))
            project_type = random.choice(PROJECT_CATEGORIES[category])
            
            volunteer = self.generate_volunteer(branch, category, project_type, volunteer_date)
            volunteers.append(volunteer)
        
        return volunteers
    
    def generate_dataset(self, total_volunteers: int = 1000, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """Generate complete synthetic dataset"""
        
        if start_date is None:
            start_date = datetime(2025, 1, 1)
        if end_date is None:
            end_date = datetime(2025, 12, 31)
        
        # Filter branches if specified
        branches_to_use = BRANCHES
        if self.branch_filter:
            branches_to_use = [b for b in BRANCHES if self.branch_filter.lower() in b["name"].lower()]
        
        volunteers_per_branch = total_volunteers // len(branches_to_use)
        all_volunteers = []
        
        print(f"🎯 Generating {total_volunteers} volunteers across {len(branches_to_use)} branches")
        print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        for branch in branches_to_use:
            print(f"📍 Generating {volunteers_per_branch} volunteers for {branch['name']}")
            branch_volunteers = self.generate_branch_data(branch, start_date, end_date, volunteers_per_branch)
            all_volunteers.extend(branch_volunteers)
        
        # Add some extra volunteers to reach exact total
        remaining = total_volunteers - len(all_volunteers)
        if remaining > 0:
            for _ in range(remaining):
                branch = random.choice(branches_to_use)
                random_days = random.randint(0, (end_date - start_date).days)
                volunteer_date = start_date + timedelta(days=random_days)
                category = random.choice(list(PROJECT_CATEGORIES.keys()))
                project_type = random.choice(PROJECT_CATEGORIES[category])
                volunteer = self.generate_volunteer(branch, category, project_type, volunteer_date)
                all_volunteers.append(volunteer)
        
        # Sort by date
        all_volunteers.sort(key=lambda x: x["Date"])
        
        return all_volunteers
    
    def export_csv(self, volunteers: List[Dict[str, Any]], filename: str = None) -> str:
        """Export volunteers to CSV file"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"synthetic_volunteer_data_{timestamp}.csv"
        
        # Ensure the file is in the data directory
        os.makedirs("generated_data", exist_ok=True)
        filepath = os.path.join("generated_data", filename)
        
        if volunteers:
            fieldnames = volunteers[0].keys()
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(volunteers)
        
        print(f"✅ Exported {len(volunteers)} volunteer records to {filepath}")
        return filepath
    
    def export_json(self, volunteers: List[Dict[str, Any]], filename: str = None) -> str:
        """Export volunteers to JSON file"""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"synthetic_volunteer_data_{timestamp}.json"
        
        os.makedirs("generated_data", exist_ok=True)
        filepath = os.path.join("generated_data", filename)
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(volunteers, jsonfile, indent=2, default=str)
        
        print(f"✅ Exported {len(volunteers)} volunteer records to {filepath}")
        return filepath
    
    def generate_dashboard_sample_data(self, volunteers: List[Dict[str, Any]]) -> str:
        """Generate sample data file for React dashboard"""
        
        # Convert to dashboard format
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
        
        # Generate JavaScript sample data file
        js_content = f"""export const SAMPLE_DATA = {json.dumps(dashboard_data, indent=2)};
"""
        
        filepath = "1/src/data/sampleData.js"
        with open(filepath, 'w', encoding='utf-8') as jsfile:
            jsfile.write(js_content)
        
        print(f"✅ Updated React dashboard sample data: {filepath}")
        return filepath

def main():
    """Main CLI interface for one-click demo seeding"""
    
    parser = argparse.ArgumentParser(description="One-Click Demo Seeding: Generate Synthetic Volunteer Data")
    parser.add_argument("--volunteers", "-v", type=int, default=500, help="Total number of volunteers to generate (default: 500)")
    parser.add_argument("--branch", "-b", type=str, help="Filter to specific branch (partial name match)")
    parser.add_argument("--start-date", "-s", type=str, help="Start date (YYYY-MM-DD, default: 2025-01-01)")
    parser.add_argument("--end-date", "-e", type=str, help="End date (YYYY-MM-DD, default: 2025-12-31)")
    parser.add_argument("--format", "-f", choices=["csv", "json", "both"], default="both", help="Export format (default: both)")
    parser.add_argument("--update-dashboard", "-d", action="store_true", help="Update React dashboard sample data")
    parser.add_argument("--output", "-o", type=str, help="Output filename (without extension)")
    
    args = parser.parse_args()
    
    print("🎭 One-Click Demo Seeding: Synthetic Volunteer Data Generator")
    print("=" * 60)
    
    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d") if args.start_date else datetime(2025, 1, 1)
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else datetime(2025, 12, 31)
    
    # Initialize generator
    generator = SyntheticDataGenerator(branch_filter=args.branch)
    
    # Generate data
    volunteers = generator.generate_dataset(
        total_volunteers=args.volunteers,
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"\n📊 Generated {len(volunteers)} volunteer records")
    
    # Export data
    exported_files = []
    
    if args.format in ["csv", "both"]:
        csv_filename = f"{args.output}.csv" if args.output else None
        csv_file = generator.export_csv(volunteers, csv_filename)
        exported_files.append(csv_file)
    
    if args.format in ["json", "both"]:
        json_filename = f"{args.output}.json" if args.output else None
        json_file = generator.export_json(volunteers, json_filename)
        exported_files.append(json_file)
    
    # Update dashboard if requested
    if args.update_dashboard:
        dashboard_file = generator.generate_dashboard_sample_data(volunteers)
        exported_files.append(dashboard_file)
    
    print("\n🎉 One-click demo seeding complete!")
    print(f"📁 Files generated: {len(exported_files)}")
    for file in exported_files:
        print(f"   - {file}")
    
    # Show sample statistics
    branch_stats = {}
    total_hours = 0
    
    for vol in volunteers:
        branch = vol["Branch"]
        hours = vol["Hours"]
        
        if branch not in branch_stats:
            branch_stats[branch] = {"count": 0, "hours": 0}
        
        branch_stats[branch]["count"] += 1
        branch_stats[branch]["hours"] += hours
        total_hours += hours
    
    print(f"\n📈 Statistics:")
    print(f"   Total Volunteers: {len(volunteers)}")
    print(f"   Total Hours: {total_hours:,.1f}")
    print(f"   Average Hours per Volunteer: {total_hours/len(volunteers):.1f}")
    
    print(f"\n🏢 By Branch:")
    for branch, stats in sorted(branch_stats.items()):
        print(f"   {branch}: {stats['count']} volunteers, {stats['hours']:.1f} hours")

if __name__ == "__main__":
    main()