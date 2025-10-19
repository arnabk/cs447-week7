#!/usr/bin/env python3
"""
Test script to verify the Theme Evolution System functionality.
"""

import sys
import os
import yaml
import requests
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_services():
    """Test that all services are running"""
    print("🔍 Testing services...")
    
    # Test Streamlit
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit UI is accessible")
        else:
            print(f"❌ Streamlit UI returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Streamlit UI not accessible: {e}")
        return False
    
    # Test Ollama
    try:
        response = requests.get("http://ollama:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            if 'llama3.1:latest' in model_names and 'nomic-embed-text:latest' in model_names:
                print("✅ Ollama with required models is accessible")
            else:
                print(f"❌ Required models not found. Available: {model_names}")
                return False
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama not accessible: {e}")
        return False
    
    return True

def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from models import SurveyResponse, Theme, ThemeAssignment
        print("✅ Models imported successfully")
    except Exception as e:
        print(f"❌ Failed to import models: {e}")
        return False
    
    try:
        from utils import generate_synthetic_responses, generate_survey_questions
        print("✅ Utils imported successfully")
    except Exception as e:
        print(f"❌ Failed to import utils: {e}")
        return False
    
    try:
        from theme_processor import ThemeProcessor
        print("✅ ThemeProcessor imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ThemeProcessor: {e}")
        return False
    
    return True

def test_config():
    """Test that config can be loaded"""
    print("🔍 Testing config...")
    
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        required_sections = ['database', 'ollama', 'thresholds', 'processing', 'ngrams']
        for section in required_sections:
            if section not in config:
                print(f"❌ Missing config section: {section}")
                return False
        
        print("✅ Config loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False

def test_synthetic_data():
    """Test synthetic data generation"""
    print("🔍 Testing synthetic data generation...")
    
    try:
        from utils import generate_survey_questions, generate_synthetic_responses
        
        # Test question generation
        questions = generate_survey_questions(1)
        if not questions or len(questions) == 0:
            print("❌ Failed to generate questions")
            return False
        
        # Test response generation
        responses = generate_synthetic_responses(questions[0], 10)
        if not responses or len(responses) != 10:
            print(f"❌ Failed to generate responses. Got {len(responses) if responses else 0} responses")
            return False
        
        # Test response structure
        response = responses[0]
        required_fields = ['id', 'question', 'response_text', 'batch_id']
        for field in required_fields:
            if not hasattr(response, field):
                print(f"❌ Response missing field: {field}")
                return False
        
        print("✅ Synthetic data generation working")
        return True
    except Exception as e:
        print(f"❌ Synthetic data generation failed: {e}")
        return False

def test_theme_processor():
    """Test ThemeProcessor initialization"""
    print("🔍 Testing ThemeProcessor initialization...")
    
    try:
        from theme_processor import ThemeProcessor
        
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        processor = ThemeProcessor(config)
        print("✅ ThemeProcessor initialized successfully")
        return True
    except Exception as e:
        print(f"❌ ThemeProcessor initialization failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Theme Evolution System Test Suite")
    print("=" * 50)
    
    tests = [
        test_services,
        test_imports,
        test_config,
        test_synthetic_data,
        test_theme_processor
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for use.")
        print("\n🌐 Open http://localhost:8501 in your browser to test the UI")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
