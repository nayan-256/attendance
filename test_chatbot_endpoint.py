import requests
import json

# Test the chatbot endpoint
url = "http://127.0.0.1:5000/chatbot"

# Test cases
test_messages = [
    {"message": "hello"},
    {"message": "help"},
    {"message": "what can you do"},
    {"message": "my attendance"},
]

print("=" * 60)
print("TESTING CHATBOT ENDPOINT")
print("=" * 60)

for i, test_data in enumerate(test_messages, 1):
    print(f"\n[Test {i}] Sending: {test_data['message']}")
    print("-" * 60)
    
    try:
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"Response: {data.get('response', 'No response field')}")
        else:
            print(f"❌ Error!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

print("\n" + "=" * 60)
print("TESTING COMPLETE")
print("=" * 60)
