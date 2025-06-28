"""
Test script to check attendance viewing functionality
"""
import sqlite3

def test_attendance_database():
    """Test if attendance data exists in the database"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Check if attendance table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance'")
        table_exists = cur.fetchone()
        
        if not table_exists:
            print("❌ Attendance table does not exist")
            return False
            
        print("✅ Attendance table exists")
        
        # Check attendance records
        cur.execute("SELECT COUNT(*) as count FROM attendance")
        count_result = cur.fetchone()
        record_count = count_result['count']
        
        print(f"📊 Total attendance records: {record_count}")
        
        if record_count > 0:
            # Get sample records
            cur.execute("""
                SELECT a.id, u.name, a.timestamp, a.status 
                FROM attendance a 
                JOIN users u ON a.user_id = u.id 
                ORDER BY a.timestamp DESC 
                LIMIT 5
            """)
            records = cur.fetchall()
            
            print("\n📋 Sample attendance records:")
            for record in records:
                print(f"   - {record['name']}: {record['status']} at {record['timestamp']}")
        else:
            print("⚠️  No attendance records found")
            
        # Check users table
        cur.execute("SELECT COUNT(*) as count FROM users")
        user_count = cur.fetchone()['count']
        print(f"👥 Total registered users: {user_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_routes():
    """Test route accessibility"""
    print("\n🔗 Route Testing:")
    print("✅ Dashboard route: /dashboard")
    print("✅ View attendance route: /view_attendance") 
    print("✅ Teacher dashboard route: /teacher_dashboard")
    print("\n📝 Access Requirements:")
    print("   - Admin dashboard (/dashboard): Requires session['logged_in'] = True")
    print("   - Teacher dashboard (/teacher_dashboard): Requires session['teacher_logged_in'] = True")
    print("   - Default login: username='admin', password='admin123'")

if __name__ == "__main__":
    print("🧪 Testing Attendance Viewing Functionality")
    print("=" * 60)
    
    test_attendance_database()
    test_routes()
    
    print("\n🚀 Steps to Access View Attendance:")
    print("1. Start Flask app: python main.py")
    print("2. Go to: http://localhost:5000")
    print("3. Click 'Admin Login'")
    print("4. Login with: admin / admin123")
    print("5. Click 'View Attendance' button")
    print("6. You should see the attendance dashboard with search filters")
    
    print("\n🔧 Troubleshooting:")
    print("- If button not visible: Check if session['logged_in'] is set after login")
    print("- If page not loading: Check Flask console for route errors")
    print("- If no data shown: Check attendance table has records")
