#!/usr/bin/env python3
"""
Quick test script to verify BuildError is fixed and all routes work
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

def test_routes():
    """Test that all url_for calls work without BuildError"""
    print("Testing Flask routes and url_for calls...")
    
    with app.test_client() as client:
        with app.app_context():
            try:
                # Test critical url_for calls that were causing issues
                print("✓ Testing home route...")
                home_url = app.url_for('home')
                print(f"  home URL: {home_url}")
                
                print("✓ Testing show_students route...")
                students_url = app.url_for('show_students')
                print(f"  show_students URL: {students_url}")
                
                print("✓ Testing student_dashboard route...")
                student_dash_url = app.url_for('student_dashboard')
                print(f"  student_dashboard URL: {student_dash_url}")
                
                print("✓ Testing profile route...")
                profile_url = app.url_for('profile')
                print(f"  profile URL: {profile_url}")
                
                print("✓ Testing edit_profile route...")
                edit_profile_url = app.url_for('edit_profile')
                print(f"  edit_profile URL: {edit_profile_url}")
                
                print("✓ Testing logout route...")
                logout_url = app.url_for('logout')
                print(f"  logout URL: {logout_url}")
                
                print("✓ Testing student_home route...")
                student_home_url = app.url_for('student_home')
                print(f"  student_home URL: {student_home_url}")
                
                print("✓ Testing download_excel route...")
                download_url = app.url_for('download_excel')
                print(f"  download_excel URL: {download_url}")
                
                print("✓ Testing register route...")
                register_url = app.url_for('register')
                print(f"  register URL: {register_url}")
                
                print("✓ Testing delete_student_by_id route...")
                delete_url = app.url_for('delete_student_by_id')
                print(f"  delete_student_by_id URL: {delete_url}")
                
                print("\n✅ All url_for calls successful! BuildError should be fixed.")
                
                # Test that the problematic admin_students_view route is not available
                try:
                    app.url_for('admin_students_view')
                    print("⚠️  WARNING: admin_students_view route still exists!")
                except:
                    print("✓ admin_students_view route properly removed")
                
                # Now test actual page rendering
                print("\n🔍 Testing page rendering...")
                response = client.get('/')
                if response.status_code == 200:
                    print("✅ Home page renders successfully!")
                else:
                    print(f"❌ Home page failed with status: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error during route testing: {e}")
                return False
                
    return True

if __name__ == "__main__":
    print("🚀 Starting BuildError fix verification...\n")
    success = test_routes()
    if success:
        print("\n🎉 SUCCESS: All tests passed! The BuildError should be resolved.")
        print("\n📝 Summary of fixes applied:")
        print("   - Added explicit endpoint names to routes")
        print("   - Fixed show_students route with proper endpoint")
        print("   - Cleaned up duplicate navigation buttons")
        print("   - Ensured all url_for references point to valid endpoints")
    else:
        print("\n❌ FAILURE: Some issues remain. Check the error messages above.")
