#!/usr/bin/env python3
"""
Multi-Role Interaction Test Script
Tests student, teacher, and admin interactions from one laptop using different browser sessions
"""

import requests
import json
import time
import webbrowser
from urllib.parse import urljoin

class AttendanceSystemTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_login(self, username, password, login_type="student"):
        """Test login for different user types"""
        login_urls = {
            "student": "/student_login",
            "teacher": "/teacher_login", 
            "admin": "/login"
        }
        
        login_url = urljoin(self.base_url, login_urls[login_type])
        
        # Get login page first
        response = self.session.get(login_url)
        if response.status_code != 200:
            return False, f"Could not access login page: {response.status_code}"
        
        # Submit login credentials
        login_data = {
            "username" if login_type != "student" else "student_id": username,
            "password": password
        }
        
        response = self.session.post(login_url, data=login_data)
        
        # Check if login was successful (usually redirects on success)
        if response.status_code == 200 and "Invalid" not in response.text:
            return True, f"{login_type.title()} login successful"
        else:
            return False, f"{login_type.title()} login failed"
    
    def test_chatbot_interaction(self, message, expected_keywords=None):
        """Test chatbot interaction for current session"""
        chatbot_url = urljoin(self.base_url, "/chatbot")
        
        try:
            # Test chatbot response
            response = self.session.post(
                chatbot_url,
                headers={'Content-Type': 'application/json'},
                json={'message': message},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                bot_response = data.get('response', '')
                
                # Check for expected keywords if provided
                if expected_keywords:
                    found_keywords = [kw for kw in expected_keywords if kw.lower() in bot_response.lower()]
                    return True, {
                        'response': bot_response,
                        'found_keywords': found_keywords,
                        'all_keywords_found': len(found_keywords) == len(expected_keywords)
                    }
                else:
                    return True, {'response': bot_response}
            else:
                return False, f"Chatbot error: {response.status_code}"
                
        except Exception as e:
            return False, f"Chatbot error: {str(e)}"
    
    def test_user_role_api(self):
        """Test the user role API"""
        try:
            response = self.session.get(urljoin(self.base_url, "/api/user-role"))
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Role API error: {response.status_code}"
        except Exception as e:
            return False, f"Role API error: {str(e)}"
    
    def logout(self):
        """Logout current user"""
        logout_url = urljoin(self.base_url, "/logout")
        response = self.session.get(logout_url)
        return response.status_code == 200

def run_comprehensive_test():
    """Run comprehensive multi-role test"""
    print("🚀 Multi-Role Attendance System Test")
    print("=" * 60)
    
    tester = AttendanceSystemTester()
    
    # Test scenarios for different roles
    test_scenarios = [
        {
            "role": "student",
            "credentials": {"username": "test_student_id", "password": "test_password"},
            "test_messages": [
                ("Hello", ["attendance", "assistant"]),
                ("What is my attendance percentage?", ["attendance", "percentage"]),
                ("How do I apply for leave?", ["leave", "application"]),
                ("Show my profile information", ["profile", "information"])
            ]
        },
        {
            "role": "teacher", 
            "credentials": {"username": "teacher1", "password": "teacher123"},
            "test_messages": [
                ("Hello", ["teacher", "class"]),
                ("Show class attendance statistics", ["class", "statistics"]),
                ("Show all students", ["students", "list"]),
                ("How to use teacher dashboard?", ["dashboard", "teacher"])
            ]
        },
        {
            "role": "admin",
            "credentials": {"username": "admin", "password": "admin123"},
            "test_messages": [
                ("Hello", ["admin", "system"]),
                ("Show system overview", ["system", "overview"]),
                ("How to manage students?", ["manage", "students"]),
                ("System analytics", ["analytics", "system"])
            ]
        }
    ]
    
    results = {}
    
    for scenario in test_scenarios:
        role = scenario["role"]
        print(f"\n🎭 Testing {role.upper()} Role")
        print("-" * 40)
        
        # Test login
        success, message = tester.test_login(
            scenario["credentials"]["username"],
            scenario["credentials"]["password"],
            role
        )
        
        if not success:
            print(f"❌ Login failed: {message}")
            results[role] = {"login": False, "chatbot_tests": []}
            continue
        
        print(f"✅ {message}")
        
        # Test role API
        success, role_data = tester.test_user_role_api()
        if success:
            print(f"✅ Role detected: {role_data.get('role', 'unknown')}")
            if role_data.get('userInfo'):
                user_info = role_data['userInfo']
                if 'name' in user_info:
                    print(f"   User: {user_info['name']}")
                elif 'username' in user_info:
                    print(f"   User: {user_info['username']}")
        else:
            print(f"⚠️  Role API issue: {role_data}")
        
        # Test chatbot interactions
        chatbot_results = []
        for message, expected_keywords in scenario["test_messages"]:
            print(f"\n💬 Testing: '{message}'")
            
            success, result = tester.test_chatbot_interaction(message, expected_keywords)
            
            if success:
                response = result['response']
                print(f"✅ Response received ({len(response)} chars)")
                print(f"   Preview: {response[:100]}{'...' if len(response) > 100 else ''}")
                
                if 'found_keywords' in result:
                    found = result['found_keywords']
                    if found:
                        print(f"✅ Keywords found: {', '.join(found)}")
                    else:
                        print(f"⚠️  No expected keywords found")
                
                chatbot_results.append({
                    "message": message,
                    "success": True,
                    "response_length": len(response),
                    "keywords_found": result.get('found_keywords', [])
                })
            else:
                print(f"❌ Failed: {result}")
                chatbot_results.append({
                    "message": message,
                    "success": False,
                    "error": result
                })
            
            time.sleep(0.5)  # Brief pause between requests
        
        results[role] = {
            "login": True,
            "chatbot_tests": chatbot_results
        }
        
        # Logout
        tester.logout()
        print(f"\n✅ {role.title()} session logged out")
        time.sleep(1)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for role, result in results.items():
        print(f"\n{role.upper()} ROLE:")
        print(f"  Login: {'✅ Success' if result['login'] else '❌ Failed'}")
        
        if result['login']:
            successful_tests = sum(1 for test in result['chatbot_tests'] if test['success'])
            total_tests = len(result['chatbot_tests'])
            print(f"  Chatbot Tests: {successful_tests}/{total_tests} passed")
            
            for test in result['chatbot_tests']:
                status = "✅" if test['success'] else "❌"
                print(f"    {status} {test['message']}")
    
    return results

def open_multiple_browser_sessions():
    """Open multiple browser sessions for manual testing"""
    print("\n🌐 Opening Browser Sessions for Manual Testing")
    print("-" * 50)
    
    base_url = "http://localhost:5000"
    
    # URLs for different login pages
    urls = [
        (f"{base_url}/student_login", "Student Login"),
        (f"{base_url}/teacher_login", "Teacher Login"), 
        (f"{base_url}/login", "Admin Login"),
        (f"{base_url}/chatbot", "Chatbot (Guest)")
    ]
    
    print("Opening browser tabs for:")
    for url, description in urls:
        print(f"  • {description}: {url}")
        webbrowser.open_new_tab(url)
        time.sleep(1)
    
    print("\n💡 Manual Testing Instructions:")
    print("1. Use different browser tabs to log in as different roles")
    print("2. Test the chatbot from each logged-in session")
    print("3. Compare the responses and UI for each role")
    print("4. Verify role-specific features work correctly")
    
    print("\n🔐 Test Credentials:")
    print("Student: Use any registered student ID + password")
    print("Teacher: teacher1 / teacher123") 
    print("Admin: admin / admin123")

def test_single_role_interaction(role="student"):
    """Test interaction for a single role"""
    print(f"🎯 Testing {role.upper()} Role Interaction")
    print("-" * 40)
    
    tester = AttendanceSystemTester()
    
    # Role-specific credentials
    credentials = {
        "student": {"username": "test_student", "password": "password"},
        "teacher": {"username": "teacher1", "password": "teacher123"},
        "admin": {"username": "admin", "password": "admin123"}
    }
    
    if role not in credentials:
        print(f"❌ Unknown role: {role}")
        return
    
    # Test login
    success, message = tester.test_login(
        credentials[role]["username"],
        credentials[role]["password"],
        role
    )
    
    if success:
        print(f"✅ {message}")
        
        # Test a few chatbot interactions
        test_messages = [
            "Hello",
            "Help",
            "What can you do?"
        ]
        
        for msg in test_messages:
            success, result = tester.test_chatbot_interaction(msg)
            if success:
                print(f"✅ '{msg}' -> Response received")
            else:
                print(f"❌ '{msg}' -> {result}")
        
        tester.logout()
        print("✅ Logged out")
    else:
        print(f"❌ {message}")

if __name__ == "__main__":
    print("🤖 Attendance System Multi-Role Tester")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        print("✅ Server is running")
    except:
        print("❌ Server is not running. Please start with: python main.py")
        exit(1)
    
    print("\nChoose testing mode:")
    print("1. Comprehensive automated test (all roles)")
    print("2. Open multiple browser sessions (manual testing)")
    print("3. Test single role interaction")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        results = run_comprehensive_test()
        
        print(f"\n🎉 Testing completed!")
        print("Next steps:")
        print("1. Review any failed tests above")
        print("2. Test manually using browser sessions")
        print("3. Verify role-specific UI differences")
        
    elif choice == "2":
        open_multiple_browser_sessions()
        
    elif choice == "3":
        role = input("Enter role (student/teacher/admin): ").strip().lower()
        test_single_role_interaction(role)
        
    else:
        print("Invalid choice. Running comprehensive test...")
        run_comprehensive_test()
