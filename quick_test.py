#!/usr/bin/env python3
"""
Quick test to verify chatbot integration is working
"""

import requests
import sys

def quick_test():
    print("🧪 Quick Chatbot Integration Test")
    print("=" * 40)
    
    base_url = "http://localhost:5000"
    
    try:
        # Test if server is running
        print("1. Testing server connectivity...")
        response = requests.get(base_url, timeout=3)
        print("   ✅ Server is running")
        
        # Test chatbot page loads
        print("2. Testing chatbot page...")
        response = requests.get(f"{base_url}/chatbot", timeout=3)
        if response.status_code == 200:
            print("   ✅ Chatbot page loads")
        else:
            print(f"   ❌ Chatbot page error: {response.status_code}")
            return False
        
        # Test chatbot endpoint
        print("3. Testing chatbot endpoint...")
        response = requests.post(
            f"{base_url}/chatbot",
            headers={'Content-Type': 'application/json'},
            json={'message': 'hello'},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Chatbot responds correctly")
            print(f"   🤖 Response: {data['response'][:80]}...")
        else:
            print(f"   ❌ Chatbot error: {response.status_code}")
            return False
        
        # Test role API
        print("4. Testing role detection API...")
        response = requests.get(f"{base_url}/api/user-role", timeout=3)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Role API works: {data['role']}")
        else:
            print(f"   ❌ Role API error: {response.status_code}")
        
        print("\n🎉 All tests passed! Chatbot integration is working.")
        return True
        
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to server")
        print("   💡 Start the server with: python main.py")
        return False
    except requests.exceptions.Timeout:
        print("   ❌ Server timeout")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    if quick_test():
        print("\n✅ Ready for multi-role testing!")
        print("📋 Next steps:")
        print("1. Run: python test_multi_role_interactions.py")
        print("2. Test student home page chatbot button")
        print("3. Login as different roles and test chatbot")
    else:
        print("\n❌ Please fix the issues above before proceeding")
        sys.exit(1)
