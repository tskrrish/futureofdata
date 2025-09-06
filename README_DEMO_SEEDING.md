# 🎭 One-Click Demo Seeding: Synthetic Volunteer Data Generator

Generate realistic synthetic volunteer data across YMCA branches for demos, testing, and development.

## 🚀 Quick Start

### Interactive One-Click Demo Seeder
```bash
python3 demo_seeder.py
```

### Command Line Generator
```bash
# Generate 500 volunteers with dashboard update
python3 synthetic_data_generator.py --volunteers 500 --update-dashboard

# Generate branch-specific data
python3 synthetic_data_generator.py --branch "Blue Ash" --volunteers 200

# Generate large dataset
python3 synthetic_data_generator.py --volunteers 2000 --format both
```

### Branch-Aware Advanced Seeding
```bash
python3 branch_seeder.py
```

## 📋 Features

### ✨ One-Click Demo Seeding
- **Interactive Menu**: Easy-to-use CLI interface
- **Quick Actions**: Pre-configured options for common scenarios
- **Dashboard Integration**: Automatic React dashboard updates
- **Multiple Export Formats**: CSV, JSON, and JavaScript

### 🎯 Realistic Data Generation
- **8 YMCA Branches**: Blue Ash, Central Parkway, Clippard, M.E. Lyons, R.C. Durre, Campbell County, Powel Crosley, Gamble-Nippert
- **Authentic Demographics**: Realistic names, ages, addresses, and contact info
- **Project Categories**: Youth Development, Health & Wellness, Community Services, Fundraising, Branch Support
- **Volunteer Characteristics**: Member status, credentials, hours, assignments
- **Date Distribution**: Weighted seasonal patterns and realistic timing

### 🏢 Branch-Aware Features
- **Regional Characteristics**: Different volunteer patterns per region
- **Branch Profiles**: Size-based volunteer distributions
- **Member Ratios**: Realistic membership percentages per branch
- **Program Focus**: Branch-specific popular programs
- **Demographic Weighting**: Age ranges and characteristics per branch

### 📊 Export & Integration
- **Multiple Formats**: CSV, JSON export
- **React Dashboard**: Automatic `sampleData.js` updates
- **Database Integration**: Supabase seeding support
- **Statistics**: Detailed analytics and breakdowns
- **Scenarios**: Pre-built multi-branch comparison datasets

## 🎬 Available Scenarios

### Regional Comparison
Compare volunteer engagement across different regions:
- **North**: Blue Ash (300 volunteers), Campbell County (200 volunteers)
- **Central**: Central Parkway (250 volunteers)
- **West**: Clippard (200 volunteers)  
- **South**: M.E. Lyons (150 volunteers)

### Size Analysis
Analyze patterns by branch size:
- **Large**: Blue Ash (400), Powel Crosley (350)
- **Medium**: Central Parkway (250), Clippard (200)
- **Small**: M.E. Lyons (100), Gamble-Nippert (80)

### Program Focus
Specialized program concentrations:
- **Youth Programs**: Blue Ash focus
- **Senior Services**: Central Parkway focus
- **Fundraising**: Powel Crosley focus
- **Family Programs**: R.C. Durre focus

### Seasonal Trends
Realistic seasonal volunteer distribution patterns across all branches.

## 📁 Generated Files

### Data Files
- `generated_data/` - Main export directory
- `*.csv` - Volunteer data in CSV format
- `*.json` - Volunteer data in JSON format
- `scenarios/` - Scenario-specific datasets

### Dashboard Files
- `1/src/data/sampleData.js` - React dashboard data
- Dashboard-compatible format with branch, hours, member status, projects

### Statistics Files
- `*_stats.json` - Detailed analytics and breakdowns
- Branch comparisons, demographic splits, program distributions

## 🔧 Command Line Options

```bash
python3 synthetic_data_generator.py [OPTIONS]

Options:
  -v, --volunteers NUM     Number of volunteers (default: 500)
  -b, --branch NAME        Filter to specific branch
  -s, --start-date DATE    Start date (YYYY-MM-DD)
  -e, --end-date DATE      End date (YYYY-MM-DD)  
  -f, --format FORMAT      Export format: csv, json, both
  -d, --update-dashboard   Update React dashboard
  -o, --output NAME        Output filename prefix
```

## 📈 Sample Statistics

Generated datasets include:
- **Realistic Demographics**: 16-85 age range, balanced gender split
- **Member Distribution**: ~65% YMCA members across branches
- **Volunteer Hours**: 0.5-25 hours per assignment
- **Program Diversity**: 5 major categories, 20+ project types
- **Geographic Spread**: Cincinnati metro area addresses
- **Temporal Distribution**: Year-long activity with seasonal patterns

## 🎯 Use Cases

### Demo & Presentation
- **Sales Demos**: Realistic data for prospect presentations
- **Feature Showcases**: Dashboard and analytics demonstrations
- **Training**: Staff onboarding with representative data

### Development & Testing
- **Frontend Testing**: Rich datasets for UI/UX development
- **Performance Testing**: Large datasets for load testing
- **Integration Testing**: Multi-format export validation

### Analytics & Reporting
- **Dashboard Development**: Chart and graph testing data
- **Report Generation**: Template and layout development
- **Comparative Analysis**: Multi-branch scenario testing

## 🗄️ Database Integration

### Supabase Integration
The system includes built-in Supabase database seeding:

```python
# Seed database with generated volunteers
await seeder.seed_database(volunteers)
```

### Database Schema Support
- **Users Table**: Basic volunteer demographics
- **Preferences Table**: Volunteer interests and availability
- **Matches Table**: Volunteer-project assignments
- **Analytics Table**: Event tracking and metrics

## 🎨 Customization

### Branch Profiles
Modify `branch_profiles` in `branch_seeder.py` to adjust:
- Age ranges per branch
- Member ratios
- Popular programs
- Volunteer multipliers

### Project Categories  
Update `PROJECT_CATEGORIES` in `synthetic_data_generator.py` to add:
- New program types
- Project categories
- Assignment roles

### Demographics
Customize volunteer characteristics:
- Name distributions
- Geographic areas  
- Ethnicity ratios
- Contact patterns

## 🚀 Integration Examples

### React Dashboard Update
```bash
python3 synthetic_data_generator.py --volunteers 100 --update-dashboard
cd 1 && npm run dev
```

### Large Dataset Generation
```bash
python3 synthetic_data_generator.py --volunteers 5000 --format both --output enterprise_demo
```

### Branch Comparison
```bash
python3 branch_seeder.py  # Select "regional_comparison"
```

## 📊 Output Examples

### CSV Output
Standard volunteer CSV with all demographic and assignment fields compatible with existing data formats.

### JSON Output
Structured JSON for API integration and data processing.

### Dashboard JavaScript
React-compatible sample data with proper field mapping:
```javascript
{
  branch: "Blue Ash",
  hours: 15.5,
  assignee: "John Smith", 
  is_member: true,
  project_tag: "Youth Development"
}
```

---

## 🎉 Getting Started

1. **Quick Demo**: Run `python3 demo_seeder.py` and select option 1
2. **Dashboard Test**: Run option 4 for quick dashboard update
3. **Custom Data**: Run option 5 for full customization options

**Happy volunteering! 🎭**