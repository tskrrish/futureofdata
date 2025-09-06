#!/bin/bash

# One-Click Demo Seeding Setup Script
# Sets up the synthetic data generation environment

echo "🎭 One-Click Demo Seeding Setup"
echo "=============================="

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p generated_data
mkdir -p generated_data/scenarios

# Make scripts executable
echo "🔧 Setting permissions..."
chmod +x synthetic_data_generator.py
chmod +x demo_seeder.py
chmod +x branch_seeder.py

# Check Python environment
echo "🐍 Checking Python environment..."
if command -v python3 &> /dev/null; then
    echo "✅ Python 3 found: $(python3 --version)"
else
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

# Check required modules
echo "📦 Checking required modules..."
python3 -c "import random, csv, json, datetime, uuid, os, argparse" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ All required modules available"
else
    echo "❌ Some required modules missing"
    exit 1
fi

# Test the generators
echo "🧪 Testing generators..."
python3 synthetic_data_generator.py --volunteers 5 --output setup_test --format csv > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Synthetic data generator working"
    rm -f generated_data/setup_test.csv
else
    echo "❌ Synthetic data generator failed"
    exit 1
fi

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "🚀 Quick Start Options:"
echo "  1. Interactive demo seeder:    python3 demo_seeder.py"
echo "  2. Command line generator:     python3 synthetic_data_generator.py --help"
echo "  3. Branch-aware seeder:        python3 branch_seeder.py"
echo ""
echo "📚 Documentation: README_DEMO_SEEDING.md"
echo ""
echo "🎯 Try this to get started:"
echo "     python3 demo_seeder.py"
echo ""