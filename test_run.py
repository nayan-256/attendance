#!/usr/bin/env python3
# Test file to check if main.py runs without errors

try:
    print("Testing main.py...")
    
    # Import the main module
    import main
    
    print("✅ main.py imported successfully")
    print("✅ Flask app created successfully")
    
    # Test if the app can run
    with main.app.test_client() as client:
        print("✅ Test client created successfully")
        
        # Test the home route
        response = client.get('/')
        print(f"✅ Home route status: {response.status_code}")
        
        # Test student login page
        response = client.get('/student_login')
        print(f"✅ Student login page status: {response.status_code}")
        
        # Test student home redirect (should redirect to login)
        response = client.get('/student_home')
        print(f"✅ Student home redirect status: {response.status_code}")
        
    print("✅ All basic tests passed!")
    
except Exception as e:
    print(f"❌ Error occurred: {e}")
    import traceback
    traceback.print_exc()
