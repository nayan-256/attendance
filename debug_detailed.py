import sys
import traceback
import os

# Redirect stdout to a log file for debugging
log_file = open("debug_log.txt", "w")
sys.stdout = log_file
sys.stderr = log_file

try:
    print("=== STARTING DEBUG TEST ===")
    print("Current directory:", os.getcwd())
    print("Python path:", sys.path[0])
    
    print("\n1. Importing main module...")
    import main
    print("   ✅ main.py imported successfully")
    
    print("\n2. Checking Flask app...")
    print(f"   App name: {main.app.name}")
    print(f"   App routes: {[str(rule) for rule in main.app.url_map.iter_rules()]}")
    
    print("\n3. Testing student_home route...")
    with main.app.app_context():
        print("   App context created")
    
    print("\n4. Testing with test client...")
    with main.app.test_client() as client:
        print("   Test client created")
        
        # Test student_home route
        print("   Testing GET /student_home...")
        response = client.get('/student_home')
        print(f"     Status: {response.status_code}")
        print(f"     Headers: {dict(response.headers)}")
        
        # Test student_login route
        print("   Testing GET /student_login...")
        response = client.get('/student_login')
        print(f"     Status: {response.status_code}")
    
    print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    
except Exception as e:
    print(f"\n❌ ERROR OCCURRED: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    
finally:
    log_file.close()
    # Restore stdout
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    
    # Print the log file contents
    with open("debug_log.txt", "r") as f:
        print(f.read())
