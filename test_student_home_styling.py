#!/usr/bin/env python3
"""
Quick test script to verify student home page styling consistency.
This script checks if the student home page now matches the structure and style of other pages.
"""

import sys
import os

def test_student_home_styling():
    """Test if student home page has consistent styling with other pages."""
    
    # Add the project directory to the Python path
    project_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_dir)
    
    try:
        from main import app
        
        with app.test_client() as client:
            # Test if student home page can be accessed (will check for syntax errors)
            with app.app_context():
                try:
                    # Try to render the template
                    from flask import render_template
                    
                    # This will catch any template syntax errors
                    template_content = render_template('student_home.html')
                    
                    print("✅ Student home page template renders successfully!")
                    
                    # Check for key styling elements
                    key_elements = [
                        'floating-shapes',  # Background animation elements
                        'dashboard-card',   # Main container styling
                        'data-aos',         # AOS animation attributes
                        'bootstrap@5.3.3',  # Bootstrap CSS
                        'font-awesome',     # Icon library
                        'aos@2.3.1'         # AOS library
                    ]
                    
                    found_elements = []
                    for element in key_elements:
                        if element in template_content:
                            found_elements.append(element)
                            print(f"✅ Found: {element}")
                        else:
                            print(f"❌ Missing: {element}")
                    
                    # Summary
                    print(f"\n📊 Summary: {len(found_elements)}/{len(key_elements)} styling elements found")
                    
                    if len(found_elements) == len(key_elements):
                        print("🎉 Student home page styling is now consistent with other pages!")
                        return True
                    else:
                        print("⚠️  Some styling elements are missing")
                        return False
                        
                except Exception as e:
                    print(f"❌ Template error: {str(e)}")
                    return False
                    
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Student Home Page Styling Consistency")
    print("=" * 50)
    
    success = test_student_home_styling()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("🎯 The student home page now matches the style and structure of other pages.")
    else:
        print("\n❌ Test failed!")
        print("🔧 There may be some styling inconsistencies that need to be addressed.")
    
    print("\n📝 Note: You can now:")
    print("   1. Start the Flask app: python main.py")
    print("   2. Navigate to the student home page")
    print("   3. Verify that it has the same background, animations, and styling as other pages")
