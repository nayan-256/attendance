#!/usr/bin/env python3
"""
Simple test script to check if the Flask app can be imported and started
"""

try:
    print("Testing Flask app import...")
    import main
    print("✅ Flask app imported successfully!")
    
    # Test if the app is configured correctly
    print(f"✅ App secret key is set: {bool(main.app.secret_key)}")
    print(f"✅ Upload folder configured: {main.app.config.get('UPLOAD_FOLDER', 'Not set')}")
    
    # Test database initialization
    print("Testing database initialization...")
    main.init_db()
    print("✅ Database initialized successfully!")
    
    # Check if routes are registered
    print("\nRegistered routes:")
    for rule in main.app.url_map.iter_rules():
        print(f"  {rule.endpoint}: {rule.rule}")
    
    print("\n✅ All tests passed! The Flask app should work correctly.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
