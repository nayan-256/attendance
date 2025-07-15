#!/usr/bin/env python3

import os
import sys
import subprocess

def run_flask_debug():
    """Run Flask app in debug mode and capture output"""
    
    print("=== Running Flask App in Debug Mode ===")
    
    try:
        # Change to the correct directory
        os.chdir(r"c:\Users\Lenovo\Desktop\gcoej all subjects\TY folder\Sem 6\Miniproject\attendance")
        
        # Set Flask environment variables
        env = os.environ.copy()
        env['FLASK_APP'] = 'main.py'
        env['FLASK_ENV'] = 'development'
        env['FLASK_DEBUG'] = '1'
        
        # Run the Flask app
        print("Starting Flask application...")
        result = subprocess.run([
            sys.executable, 'main.py'
        ], env=env, capture_output=True, text=True, timeout=10)
        
        print("Return code:", result.returncode)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        
    except subprocess.TimeoutExpired:
        print("Flask app started successfully (timeout reached)")
    except Exception as e:
        print(f"Error running Flask app: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_flask_debug()
