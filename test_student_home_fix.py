#!/usr/bin/env python3
"""
Quick test to check if student_home.html is working properly
"""

import sys
import os

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

try:
    from main import app
    
    with app.test_client() as client:
        with app.app_context():
            try:
                # Try to render the template
                from flask import render_template
                
                template_content = render_template('student_home.html')
                
                # Check if CSS is rendered as text (corrupted) or properly in head
                if 'min-height: 100vh;' in template_content and '<style>' not in template_content:
                    print("❌ CORRUPTED: CSS is showing as text instead of being in <style> tags")
                    print("📄 The file needs to be fixed - CSS is being displayed on the page")
                    return False
                elif '<style>' in template_content and 'min-height: 100vh;' in template_content:
                    print("✅ GOOD: CSS is properly enclosed in <style> tags")
                    print("🎯 Student home page should now display buttons correctly")
                    return True
                else:
                    print("⚠️  UNKNOWN: Cannot determine CSS status")
                    return False
                    
            except Exception as e:
                print(f"❌ Template error: {str(e)}")
                return False
                
except Exception as e:
    print(f"❌ Import error: {str(e)}")
    return False

if __name__ == "__main__":
    print("🔧 Testing Student Home Page Fix")
    print("=" * 40)
    
    success = False
    
    print("\n📝 Note: Start the Flask app with 'python main.py' and navigate to student home page to verify buttons are visible.")
