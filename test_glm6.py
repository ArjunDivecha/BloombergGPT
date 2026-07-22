#!/usr/bin/env python3
"""
=============================================================================
SCRIPT NAME: test_glm6.py
=============================================================================

DESCRIPTION:
    Tests the GLM6 (glm-4.6) model API endpoint at z.aimodelapi.com.
    Sends a simple chat completion request with a system prompt and user
    message, and prints the response. Reads the API key from an inline
    default or from the GLM_API_KEY environment variable.

INPUT FILES:
    (none -- data is fetched via HTTP from the GLM6 API)

OUTPUT FILES:
    (none -- results are printed to stdout)

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - requests

USAGE:
    python test_glm6.py

NOTES:
    - The API key can be overridden by setting the GLM_API_KEY environment variable.
    - Default endpoint: https://api.z.ai/api/paas/v4/chat/completions
    - Model name: glm-4.6
    - Test sends a simple greeting request with max_tokens=50.
=============================================================================
"""

import requests
import json

def test_glm6_api():
    """Test the GLM6 model using the z.aimodelapi.com endpoint"""
    
    # Configuration from the Factory config
    base_url = "https://api.z.ai/api/paas/v4"
    api_key = "310e11dfdd2a49de994d179bdf6899e4.oAOWPT0gS7QXzgJr"
    model = "glm-4.6"
    
    # Construct the full URL for chat completions
    url = f"{base_url}/chat/completions"
    
    # Headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Simple test message
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user", 
                "content": "Say 'Hello! GLM6 is working!' if you can respond."
            }
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    print(f"Testing GLM6 (glm-4.6) API...")
    print(f"URL: {url}")
    print(f"Model: {model}")
    print("-" * 50)
    
    import os
    
    # If we have a different API key from config, use it
    config_key = os.environ.get('GLM_API_KEY')
    if config_key:
        api_key = config_key
    
    try:
        # Make the API call
        response = requests.post(url, headers=headers, json=data)
        
        # Check response status
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! GLM6 API call worked!")
            print("\nResponse from GLM6:")
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print(content)
            print("\nFull response structure:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"❌ ERROR: Status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_glm6_api()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")
