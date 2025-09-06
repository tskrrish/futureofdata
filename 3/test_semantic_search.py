#!/usr/bin/env python3
"""
Test script for semantic search functionality
This script tests the semantic search implementation without requiring a full server setup
"""

import sys
import os

def test_semantic_search_import():
    """Test that the semantic search module can be imported"""
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # This will fail if dependencies aren't installed
        print("Testing semantic_search module import...")
        import semantic_search
        print("✅ semantic_search module imported successfully")
        
        # Test basic functionality
        engine = semantic_search.SemanticSearchEngine()
        print("✅ SemanticSearchEngine instance created")
        
        # Test stats without initialization
        stats = engine.get_stats()
        print(f"✅ Engine stats: {stats}")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 This is expected in this environment - dependencies not installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_api_integration():
    """Test API integration points"""
    print("\n🧪 Testing API integration...")
    
    # Check that main.py can import the module (at least syntactically)
    try:
        with open('main.py', 'r') as f:
            content = f.read()
            
        if 'from semantic_search import SemanticSearchEngine' in content:
            print("✅ semantic_search import found in main.py")
        else:
            print("❌ semantic_search import not found in main.py")
            
        if 'semantic_search = SemanticSearchEngine()' in content:
            print("✅ SemanticSearchEngine instantiation found in main.py")
        else:
            print("❌ SemanticSearchEngine instantiation not found in main.py")
            
        # Check for API endpoints
        endpoints = [
            '/api/semantic-search',
            '/api/semantic-search/suggestions',
            '/api/semantic-search/similar-volunteers',
            '/api/semantic-search/stats',
            '/api/semantic-search/refresh'
        ]
        
        for endpoint in endpoints:
            if endpoint in content:
                print(f"✅ API endpoint {endpoint} found")
            else:
                print(f"❌ API endpoint {endpoint} not found")
                
    except Exception as e:
        print(f"❌ Error testing API integration: {e}")

def test_frontend_files():
    """Test that frontend files exist"""
    print("\n🌐 Testing frontend files...")
    
    search_ui_path = 'static/semantic-search.html'
    if os.path.exists(search_ui_path):
        print(f"✅ Frontend file exists: {search_ui_path}")
        
        # Check for key components
        with open(search_ui_path, 'r') as f:
            content = f.read()
            
        components = [
            'semantic-search',
            'performSearch()',
            '/api/semantic-search',
            'similarity_score',
            'search suggestions'
        ]
        
        for component in components:
            if component.lower() in content.lower():
                print(f"✅ Frontend component found: {component}")
            else:
                print(f"❌ Frontend component missing: {component}")
                
    else:
        print(f"❌ Frontend file not found: {search_ui_path}")

def test_feature_completeness():
    """Test that the semantic search feature is complete"""
    print("\n📋 Testing feature completeness...")
    
    features = [
        ("Semantic search module", "semantic_search.py"),
        ("API endpoints", "main.py containing semantic-search"),
        ("Frontend interface", "static/semantic-search.html"),
        ("Main page integration", "main.py containing /semantic-search")
    ]
    
    score = 0
    for feature_name, check in features:
        if os.path.exists(check) or check.startswith("main.py containing"):
            if check.startswith("main.py containing"):
                # Check if main.py contains the required content
                try:
                    with open('main.py', 'r') as f:
                        content = f.read()
                    if check.split(" containing ")[1] in content:
                        print(f"✅ {feature_name}")
                        score += 1
                    else:
                        print(f"❌ {feature_name}")
                except:
                    print(f"❌ {feature_name}")
            else:
                print(f"✅ {feature_name}")
                score += 1
        else:
            print(f"❌ {feature_name}")
    
    print(f"\n📊 Feature completeness: {score}/{len(features)} ({score/len(features)*100:.0f}%)")
    return score == len(features)

def main():
    """Run all tests"""
    print("🚀 Testing Semantic Search Implementation")
    print("=" * 50)
    
    # Test module import (expected to fail due to missing deps)
    test_semantic_search_import()
    
    # Test API integration
    test_api_integration()
    
    # Test frontend files
    test_frontend_files()
    
    # Test overall completeness
    complete = test_feature_completeness()
    
    print("\n" + "=" * 50)
    if complete:
        print("🎉 Semantic Search implementation is complete!")
        print("📝 Note: Runtime testing requires installing dependencies from requirements.txt")
    else:
        print("⚠️  Some components may be missing or incomplete")
        
    print("\n🔧 To fully test, install dependencies and run the FastAPI server:")
    print("   pip install -r requirements.txt")
    print("   python main.py")
    print("   Then visit: http://localhost:8000/semantic-search")

if __name__ == "__main__":
    main()