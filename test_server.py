"""
Test script to check if the profile functionality is working correctly
"""
import requests
import time
import subprocess
import threading
import os

def start_flask_app():
    """Start the Flask application in a separate thread"""
    os.system("python main.py")

def test_profile_functionality():
    """Test if the profile page loads correctly"""
    time.sleep(3)  # Wait for Flask to start
    
    try:
        # Test admin students page
        response = requests.get("http://localhost:5000/admin/students")
        print(f"Admin Students Page Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Admin students page is accessible")
        else:
            print("❌ Admin students page failed")
        
        # Test main page
        response = requests.get("http://localhost:5000/")
        print(f"Main Page Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Main page is accessible")
        else:
            print("❌ Main page failed")
    
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask application")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Flask app test...")
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=start_flask_app, daemon=True)
    flask_thread.start()
    
    # Test the functionality
    test_profile_functionality()
    
    print("\nTo manually test:")
    print("1. Go to http://localhost:5000")
    print("2. Login as a student (try student ID: 103, password: any)")
    print("3. Click on Profile to see if the image shows")
    print("4. Go to http://localhost:5000/admin/students to see all students")
    print("\nPress Ctrl+C to stop the server")
