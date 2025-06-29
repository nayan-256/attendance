#!/usr/bin/env python3
"""
Test script to verify chatbot functionality
"""

import requests
import json
import sys
import time

def test_chatbot_endpoint():
    """Test the chatbot endpoint"""
    base_url = "http://localhost:5000"
    chatbot_url = f"{base_url}/chatbot"
    
    # Test messages
    test_messages = [
        "Hello",
        "What is my attendance percentage?",
        "How do I apply for leave?",
        "Show recent attendance",
        "Help me navigate the system"
    ]
    
    print("Testing Chatbot Endpoint...")
    print("=" * 50)
    
    for message in test_messages:
        try:
            print(f"\n🧪 Testing: '{message}'")
            
            response = requests.post(
                chatbot_url,
                headers={'Content-Type': 'application/json'},
                json={'message': message},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"🤖 Response: {data.get('response', 'No response')}")
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"📄 Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection Error: Could not connect to {base_url}")
            print("Make sure the Flask app is running on localhost:5000")
            break
        except requests.exceptions.Timeout:
            print("❌ Timeout: Request took too long")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            
        time.sleep(1)  # Brief pause between requests

def test_chatbot_page():
    """Test if the chatbot page loads"""
    try:
        response = requests.get("http://localhost:5000/chatbot", timeout=5)
        if response.status_code == 200:
            print("\n✅ Chatbot page loads successfully")
            if "Attendance Assistant" in response.text:
                print("✅ Page contains expected content")
            else:
                print("⚠️  Page loaded but may not contain expected content")
        else:
            print(f"\n❌ Chatbot page error: {response.status_code}")
    except Exception as e:
        print(f"\n❌ Error loading chatbot page: {str(e)}")

if __name__ == "__main__":
    print("Chatbot Functionality Test")
    print("=" * 50)
    
    # Test chatbot page
    test_chatbot_page()
    
    # Test chatbot endpoint
    test_chatbot_endpoint()
    
    print("\n" + "=" * 50)
    print("Test completed!")
