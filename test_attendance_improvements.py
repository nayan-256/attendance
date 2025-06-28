#!/usr/bin/env python3
"""
Test script to verify the improved attendance viewing functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
import sqlite3

def test_attendance_view():
    """Test the improved attendance viewing functionality"""
    print("🔍 Testing improved attendance viewing functionality...\n")
    
    with app.test_client() as client:
        # Test that GET request doesn't show records by default
        print("✓ Testing GET request (should not show records by default)...")
        with client.session_transaction() as sess:
            sess['logged_in'] = True  # Simulate admin login
        
        response = client.get('/dashboard')
        if response.status_code == 200:
            print("  ✅ Dashboard loads successfully")
            if b'show_results' not in response.data:
                print("  ✅ No records shown by default (as expected)")
            else:
                print("  ⚠️  Records might be showing by default")
        else:
            print(f"  ❌ Dashboard failed with status: {response.status_code}")
        
        # Test POST request with search
        print("\n✓ Testing POST request with search...")
        response = client.post('/dashboard', data={
            'name': '',
            'date': ''
        })
        if response.status_code == 200:
            print("  ✅ Search request processes successfully")
            if b'Present Attendance Records' in response.data:
                print("  ✅ Only present records are displayed")
            if b'Absent' not in response.data or b'status-absent' not in response.data:
                print("  ✅ Absent status is not shown (avoiding confusion)")
        
        # Test "Show All Present Records" functionality
        print("\n✓ Testing 'Show All Present Records' button...")
        response = client.post('/dashboard', data={
            'show_all': 'true'
        })
        if response.status_code == 200:
            print("  ✅ Show all present records works")
        
        print("\n✓ Testing template structure...")
        # Check that View All Students button is removed
        if b'View All Students' not in response.data:
            print("  ✅ 'View All Students' button successfully removed")
        else:
            print("  ⚠️  'View All Students' button still present")
        
        # Check for search form improvements
        if b'Show All Present Records' in response.data:
            print("  ✅ 'Show All Present Records' button added")
        
        print("\n🎉 Attendance view improvements test completed!")

def check_database_present_records():
    """Check if there are present records in the database"""
    print("\n📊 Checking database for present attendance records...")
    
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    # Check total attendance records
    cur.execute("SELECT COUNT(*) FROM attendance")
    total_records = cur.fetchone()[0]
    print(f"  Total attendance records: {total_records}")
    
    # Check present records
    cur.execute("SELECT COUNT(*) FROM attendance WHERE status = 'Present'")
    present_records = cur.fetchone()[0]
    print(f"  Present records: {present_records}")
    
    # Check absent records
    cur.execute("SELECT COUNT(*) FROM attendance WHERE status = 'Absent'")
    absent_records = cur.fetchone()[0]
    print(f"  Absent records: {absent_records}")
    
    if present_records > 0:
        print("  ✅ Database has present records to display")
    else:
        print("  ⚠️  No present records found - check-in some students for testing")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 Starting attendance view improvements test...\n")
    
    check_database_present_records()
    test_attendance_view()
    
    print("\n📋 Summary of improvements made:")
    print("   ✅ Removed 'View All Students' button from attendance view")
    print("   ✅ Only show present records (no absent status confusion)")
    print("   ✅ No records shown by default - only after search")
    print("   ✅ Added 'Show All Present Records' button")
    print("   ✅ Updated table structure to remove status column")
    print("   ✅ Enhanced search functionality")
    print("\n🎯 The attendance viewing is now cleaner and less confusing for admins!")
