#!/usr/bin/env python3
"""
One-Click Demo Seeder
Interactive script to quickly seed realistic volunteer data across branches
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
from synthetic_data_generator import SyntheticDataGenerator

class DemoSeeder:
    """One-click demo seeding interface"""
    
    def __init__(self):
        self.generator = SyntheticDataGenerator()
        
    def print_header(self):
        """Print welcome header"""
        print("🎭" + "=" * 60)
        print("     ONE-CLICK DEMO SEEDING: SYNTHETIC VOLUNTEER DATA")
        print("=" * 62)
        print("  Generate realistic volunteer data across YMCA branches")
        print("  Perfect for demos, testing, and development")
        print("=" * 62)
    
    def show_menu(self):
        """Show main menu options"""
        print("\n🚀 Quick Actions:")
        print("  1. 🎯 Generate Demo Dataset (500 volunteers)")
        print("  2. 📊 Generate Large Dataset (2000+ volunteers)")
        print("  3. 🏢 Generate Branch-Specific Data")
        print("  4. ⚡ Quick Dashboard Update (100 volunteers)")
        print("  5. 🔧 Custom Generation")
        print("  6. 📈 View Available Branches")
        print("  7. 🔍 Show Sample Data")
        print("  0. ❌ Exit")
        
    def show_branches(self):
        """Display available branches"""
        print("\n🏢 Available YMCA Branches:")
        from synthetic_data_generator import BRANCHES
        
        for i, branch in enumerate(BRANCHES, 1):
            print(f"  {i}. {branch['name']} (Code: {branch['code']}) - {branch['region']} Region")
    
    def show_sample_data(self):
        """Show sample generated data"""
        print("\n🔍 Generating sample data preview...")
        
        # Generate 5 sample volunteers
        volunteers = self.generator.generate_dataset(total_volunteers=5)
        
        print("\n📋 Sample Volunteer Records:")
        print("-" * 80)
        
        for i, vol in enumerate(volunteers[:3], 1):
            print(f"\n{i}. {vol['First Name']} {vol['Last Name']} ({vol['Age']} years old)")
            print(f"   📧 {vol['Email']}")
            print(f"   🏢 Branch: {vol['Branch']}")
            print(f"   🎯 Project: {vol['Project']}")
            print(f"   ⏰ Hours: {vol['Hours']}")
            print(f"   👥 YMCA Member: {vol['Are you a YMCA member?']}")
            print(f"   📅 Date: {vol['Date']}")
    
    def generate_demo_dataset(self):
        """Generate standard demo dataset"""
        print("\n🎯 Generating Demo Dataset (500 volunteers)...")
        
        volunteers = self.generator.generate_dataset(total_volunteers=500)
        
        # Export in multiple formats
        csv_file = self.generator.export_csv(volunteers, "demo_volunteer_data.csv")
        json_file = self.generator.export_json(volunteers, "demo_volunteer_data.json")
        
        # Update dashboard
        dashboard_file = self.generator.generate_dashboard_sample_data(volunteers)
        
        print(f"\n✅ Demo dataset generated successfully!")
        print(f"📁 Files created:")
        print(f"   • {csv_file}")
        print(f"   • {json_file}")
        print(f"   • {dashboard_file}")
        
        self.show_statistics(volunteers)
    
    def generate_large_dataset(self):
        """Generate large dataset for testing"""
        print("\n📊 How many volunteers would you like to generate?")
        print("  Recommended options:")
        print("    • 1000 - Small test dataset")
        print("    • 2500 - Medium dataset")
        print("    • 5000 - Large dataset")
        print("    • 10000 - Enterprise scale")
        
        while True:
            try:
                count = int(input("\n🔢 Enter number of volunteers: "))
                if count > 0:
                    break
                else:
                    print("❌ Please enter a positive number")
            except ValueError:
                print("❌ Please enter a valid number")
        
        print(f"\n📊 Generating Large Dataset ({count:,} volunteers)...")
        print("⏳ This may take a moment...")
        
        volunteers = self.generator.generate_dataset(total_volunteers=count)
        
        # Export files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = self.generator.export_csv(volunteers, f"large_dataset_{count}_{timestamp}.csv")
        json_file = self.generator.export_json(volunteers, f"large_dataset_{count}_{timestamp}.json")
        
        print(f"\n✅ Large dataset generated successfully!")
        print(f"📁 Files created:")
        print(f"   • {csv_file}")
        print(f"   • {json_file}")
        
        self.show_statistics(volunteers)
    
    def generate_branch_specific(self):
        """Generate data for specific branch"""
        self.show_branches()
        
        while True:
            branch_input = input("\n🏢 Enter branch name or number (or 'all' for all branches): ").strip()
            
            if branch_input.lower() == 'all':
                branch_filter = None
                break
            
            # Try as number first
            try:
                from synthetic_data_generator import BRANCHES
                branch_num = int(branch_input)
                if 1 <= branch_num <= len(BRANCHES):
                    branch_filter = BRANCHES[branch_num - 1]["name"].split()[0]
                    break
                else:
                    print(f"❌ Please enter a number between 1 and {len(BRANCHES)}")
                    continue
            except ValueError:
                # Try as name
                branch_filter = branch_input
                break
        
        while True:
            try:
                count = int(input("\n🔢 Number of volunteers to generate (default: 200): ") or "200")
                if count > 0:
                    break
                else:
                    print("❌ Please enter a positive number")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Create generator with branch filter
        branch_generator = SyntheticDataGenerator(branch_filter=branch_filter)
        
        print(f"\n🏢 Generating {count} volunteers for branch filter: {branch_filter or 'All branches'}")
        
        volunteers = branch_generator.generate_dataset(total_volunteers=count)
        
        # Export files
        branch_name = branch_filter.replace(" ", "_") if branch_filter else "all_branches"
        csv_file = branch_generator.export_csv(volunteers, f"branch_{branch_name}_data.csv")
        json_file = branch_generator.export_json(volunteers, f"branch_{branch_name}_data.json")
        
        print(f"\n✅ Branch-specific dataset generated!")
        print(f"📁 Files created:")
        print(f"   • {csv_file}")
        print(f"   • {json_file}")
        
        self.show_statistics(volunteers)
    
    def quick_dashboard_update(self):
        """Quick update for dashboard with minimal data"""
        print("\n⚡ Quick Dashboard Update (100 volunteers)...")
        
        volunteers = self.generator.generate_dataset(total_volunteers=100)
        
        # Only update dashboard
        dashboard_file = self.generator.generate_dashboard_sample_data(volunteers)
        
        print(f"\n✅ Dashboard updated successfully!")
        print(f"📁 File updated: {dashboard_file}")
        print("\n🚀 You can now run the React dashboard to see the new data:")
        print("   cd 1 && npm run dev")
        
        self.show_statistics(volunteers)
    
    def custom_generation(self):
        """Custom generation with all options"""
        print("\n🔧 Custom Generation Options")
        
        # Number of volunteers
        while True:
            try:
                count = int(input("\n🔢 Number of volunteers (default: 500): ") or "500")
                if count > 0:
                    break
                else:
                    print("❌ Please enter a positive number")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Date range
        print("\n📅 Date Range (press Enter for defaults)")
        start_date_str = input("Start date (YYYY-MM-DD, default: 2025-01-01): ").strip()
        end_date_str = input("End date (YYYY-MM-DD, default: 2025-12-31): ").strip()
        
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else datetime(2025, 1, 1)
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else datetime(2025, 12, 31)
        except ValueError:
            print("❌ Invalid date format, using defaults")
            start_date = datetime(2025, 1, 1)
            end_date = datetime(2025, 12, 31)
        
        # Branch filter
        branch_filter = input("\n🏢 Branch filter (partial name, or Enter for all): ").strip() or None
        
        # Export format
        print("\n📁 Export Format:")
        print("  1. CSV only")
        print("  2. JSON only")
        print("  3. Both CSV and JSON")
        print("  4. All formats + Dashboard update")
        
        while True:
            try:
                format_choice = int(input("Choose format (1-4, default: 4): ") or "4")
                if 1 <= format_choice <= 4:
                    break
                else:
                    print("❌ Please enter 1, 2, 3, or 4")
            except ValueError:
                print("❌ Please enter a valid number")
        
        # Output filename
        output_name = input("\n📝 Output filename prefix (optional): ").strip() or None
        
        print(f"\n🔧 Generating custom dataset...")
        print(f"   Volunteers: {count:,}")
        print(f"   Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"   Branch Filter: {branch_filter or 'None (all branches)'}")
        
        # Create generator
        custom_generator = SyntheticDataGenerator(branch_filter=branch_filter)
        volunteers = custom_generator.generate_dataset(
            total_volunteers=count,
            start_date=start_date,
            end_date=end_date
        )
        
        # Export based on format choice
        files_created = []
        
        if format_choice in [1, 3, 4]:  # CSV
            csv_file = custom_generator.export_csv(volunteers, f"{output_name}.csv" if output_name else None)
            files_created.append(csv_file)
        
        if format_choice in [2, 3, 4]:  # JSON
            json_file = custom_generator.export_json(volunteers, f"{output_name}.json" if output_name else None)
            files_created.append(json_file)
        
        if format_choice == 4:  # Dashboard update
            dashboard_file = custom_generator.generate_dashboard_sample_data(volunteers)
            files_created.append(dashboard_file)
        
        print(f"\n✅ Custom dataset generated!")
        print(f"📁 Files created: {len(files_created)}")
        for file in files_created:
            print(f"   • {file}")
        
        self.show_statistics(volunteers)
    
    def show_statistics(self, volunteers):
        """Show dataset statistics"""
        if not volunteers:
            return
        
        # Calculate stats
        total_hours = sum(vol["Hours"] for vol in volunteers)
        branch_stats = {}
        gender_stats = {"Male": 0, "Female": 0}
        member_stats = {"Yes": 0, "No": 0}
        
        for vol in volunteers:
            branch = vol["Branch"]
            if branch not in branch_stats:
                branch_stats[branch] = 0
            branch_stats[branch] += 1
            
            gender_stats[vol["Gender"]] += 1
            member_stats[vol["Are you a YMCA member?"]] += 1
        
        print(f"\n📈 Dataset Statistics:")
        print(f"   📊 Total Volunteers: {len(volunteers):,}")
        print(f"   ⏰ Total Hours: {total_hours:,.1f}")
        print(f"   📅 Date Range: {volunteers[0]['Date']} to {volunteers[-1]['Date']}")
        print(f"   🏢 Branches: {len(branch_stats)}")
        print(f"   👨👩 Gender Split: {gender_stats['Male']} Male, {gender_stats['Female']} Female")
        print(f"   👥 Members: {member_stats['Yes']} ({member_stats['Yes']/len(volunteers)*100:.1f}%)")
    
    def run(self):
        """Main interactive loop"""
        self.print_header()
        
        while True:
            self.show_menu()
            
            try:
                choice = input("\n🎯 Select an option (0-7): ").strip()
                
                if choice == "0":
                    print("\n👋 Thanks for using One-Click Demo Seeding!")
                    print("🎭 Happy volunteering! 🎭")
                    break
                elif choice == "1":
                    self.generate_demo_dataset()
                elif choice == "2":
                    self.generate_large_dataset()
                elif choice == "3":
                    self.generate_branch_specific()
                elif choice == "4":
                    self.quick_dashboard_update()
                elif choice == "5":
                    self.custom_generation()
                elif choice == "6":
                    self.show_branches()
                elif choice == "7":
                    self.show_sample_data()
                else:
                    print("❌ Invalid option. Please choose 0-7.")
                
                # Pause before showing menu again
                if choice != "0" and choice in ["1", "2", "3", "4", "5"]:
                    input("\n⏸️  Press Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ An error occurred: {e}")
                input("⏸️  Press Enter to continue...")

def main():
    """Entry point for one-click demo seeding"""
    
    # Check if running from correct directory
    if not os.path.exists("1") or not os.path.exists("2") or not os.path.exists("3"):
        print("⚠️  Please run this script from the root directory of the repository")
        return
    
    # Create demo seeder and run
    seeder = DemoSeeder()
    seeder.run()

if __name__ == "__main__":
    main()