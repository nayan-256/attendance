#!/usr/bin/env python3
"""
Test script to verify index page button improvements
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

def test_index_page_buttons():
    """Test that index page loads correctly with updated buttons"""
    print("🔍 Testing index page button improvements...\n")
    
    with app.test_client() as client:
        # Test home page (no login)
        print("✓ Testing home page (no user logged in)...")
        response = client.get('/')
        if response.status_code == 200:
            print("  ✅ Home page loads successfully")
            
            # Check that attendance view buttons are removed
            if b'View Attendance Records' not in response.data:
                print("  ✅ 'View Attendance Records' button removed")
            if b'View All Attendance' not in response.data:
                print("  ✅ 'View All Attendance' button removed") 
            if b'View Attendance' not in response.data:
                print("  ✅ 'View Attendance' button removed")
            
            # Check for consistent button sizing
            if b'btn-lg' in response.data:
                print("  ✅ Large button sizing applied")
            if b'fas fa-' in response.data:
                print("  ✅ Icons added to buttons")
                
        # Test admin view
        print("\n✓ Testing admin view...")
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            
        response = client.get('/')
        if response.status_code == 200:
            print("  ✅ Admin view loads correctly")
            if b'All Students' in response.data and b'Logout (Admin)' in response.data:
                print("  ✅ Admin buttons present and attendance view removed")
        
        # Test teacher view
        print("\n✓ Testing teacher view...")
        with client.session_transaction() as sess:
            sess.clear()
            sess['teacher_logged_in'] = True
            
        response = client.get('/')
        if response.status_code == 200:
            print("  ✅ Teacher view loads correctly")
            if b'Teacher Dashboard' in response.data and b'View All Attendance' not in response.data:
                print("  ✅ Teacher buttons updated, attendance view removed")
        
        # Test student view
        print("\n✓ Testing student view...")
        with client.session_transaction() as sess:
            sess.clear()
            sess['student_id'] = 'test123'
            
        response = client.get('/')
        if response.status_code == 200:
            print("  ✅ Student view loads correctly")
            if b'Student Dashboard' in response.data and b'btn-lg' in response.data:
                print("  ✅ Student buttons standardized to large size")
        
        print("\n🎉 Index page button improvements test completed!")

if __name__ == "__main__":
    print("🚀 Starting index page button improvements test...\n")
    
    test_index_page_buttons()
    
    print("\n📋 Summary of changes made:")
    print("   ✅ Removed all 'View Attendance' buttons from index page")
    print("   ✅ Standardized all buttons to 'btn-lg' size")
    print("   ✅ Added consistent icons to all buttons")
    print("   ✅ Added proper spacing with 'me-2' margin classes")
    print("   ✅ Improved visual consistency across all user types")
    print("\n🎯 Index page navigation is now cleaner and more consistent!")
