#!/usr/bin/env python3
"""
Excel Data Analyzer for YMCA Volunteer Data
Analyzes the volunteer raw data to understand structure and content
"""

import pandas as pd
import sys
from pathlib import Path

def analyze_excel_file(file_path):
    """Analyze the Excel file and show its structure"""
    try:
        # Read the Excel file
        excel_file = pd.ExcelFile(file_path)
        
        print("🔍 Excel File Analysis")
        print("=" * 50)
        
        # Show all sheet names
        print(f"📋 Number of sheets: {len(excel_file.sheet_names)}")
        print(f"📋 Sheet names: {excel_file.sheet_names}")
        print()
        
        # Analyze each sheet
        for i, sheet_name in enumerate(excel_file.sheet_names):
            print(f"📊 Sheet {i+1}: '{sheet_name}'")
            print("-" * 30)
            
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                print(f"   Rows: {len(df)}")
                print(f"   Columns: {len(df.columns)}")
                print(f"   Column names: {list(df.columns)}")
                
                # Show first few rows (non-empty)
                print("   Sample data (first 3 rows):")
                for idx, row in df.head(3).iterrows():
                    print(f"     Row {idx + 1}: {dict(row)}")
                
                # Show data types
                print("   Data types:")
                for col, dtype in df.dtypes.items():
                    print(f"     {col}: {dtype}")
                
                print()
                
            except Exception as e:
                print(f"   ⚠️  Error reading sheet: {e}")
                print()
        
        return excel_file.sheet_names
        
    except Exception as e:
        print(f"❌ Error analyzing Excel file: {e}")
        return []

if __name__ == "__main__":
    file_path = "/Users/joshuajerin/Desktop/jarvis/murai/Y Volunteer Raw Data - Jan- August 2025.xlsx"
    
    if Path(file_path).exists():
        sheet_names = analyze_excel_file(file_path)
        print(f"✅ Analysis complete. Found {len(sheet_names)} sheets.")
    else:
        print(f"❌ File not found: {file_path}")
