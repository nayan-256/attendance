from flask import Flask
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting Flask application test...")

try:
    # Try to import the main module
    print("1. Importing main module...")
    import main
    
    print("2. Flask app imported successfully")
    
    # Check if app is properly initialized
    print(f"3. App name: {main.app.name}")
    print(f"4. App config: {main.app.config.get('DEBUG', 'Not set')}")
    
    print("5. Testing routes...")
    
    # Test the student_home route specifically
    with main.app.test_client() as client:
        print("6. Testing student_home route (should redirect)...")
        response = client.get('/student_home')
        print(f"   Status: {response.status_code}")
        print(f"   Location: {response.headers.get('Location', 'No redirect')}")
        
        print("7. Testing student_login route...")
        response = client.get('/student_login')
        print(f"   Status: {response.status_code}")
        
        print("8. Testing POST to student_login...")
        response = client.post('/student_login', data={
            'student_id': 'test123',
            'password': 'testpass'
        })
        print(f"   Status: {response.status_code}")
    
    print("✅ All tests completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
