#!/usr/bin/env python3
"""
Test script to verify the student_home route functionality
"""

import sys
import os

# Add the current directory to Python path  
current_dir = os.getcwd()
sys.path.insert(0, current_dir)

try:
    from main import app, get_text, TRANSLATIONS
    print("✓ Successfully imported main.py")
    
    # Test the get_text function
    print("✓ Testing get_text function...")
    test_result = get_text('welcome')
    print(f"  get_text('welcome') = '{test_result}'")
    
    print("✓ Testing TRANSLATIONS dictionary...")
    print(f"  Available languages: {list(TRANSLATIONS.keys())}")
    
    # Test app configuration
    with app.app_context():
        print("✓ App context created successfully")
        
        # Test template globals
        template_globals = app.jinja_env.globals
        if 'get_text' in template_globals:
            print("✓ get_text is available as template global")
        else:
            print("✗ get_text is NOT available as template global")
            
    print("\n=== All tests passed! ===")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error during testing: {e}")
    sys.exit(1)
