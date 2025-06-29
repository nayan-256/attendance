#!/usr/bin/env python3
"""
Test the Flask app focusing on teacher dashboard
"""

try:
    print("Testing Flask app import (minimal)...")
    
    # Set working directory
    import os
    os.chdir(r"c:\Users\Lenovo\Desktop\gcoej all subjects\TY folder\Sem 6\Miniproject\attendance")
    
    # Import with warnings suppressed for face_recognition
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import main
    
    print("✅ Flask app imported successfully!")
    
    # Test teacher dashboard route directly
    with main.app.test_client() as client:
        print("Testing teacher dashboard route...")
        
        # Test GET request (without login - should redirect)
        response = client.get('/teacher_dashboard')
        print(f"✅ Teacher dashboard GET (no login): {response.status_code}")
        
        # Test with session (simulate login)
        with client.session_transaction() as sess:
            sess['teacher_logged_in'] = True
        
        response = client.get('/teacher_dashboard')
        print(f"✅ Teacher dashboard GET (with login): {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Teacher dashboard loads successfully!")
        else:
            print(f"❌ Teacher dashboard error: {response.status_code}")
            
    print("\n✅ Teacher dashboard test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
