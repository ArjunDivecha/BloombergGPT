#!/usr/bin/env python3
"""
=============================================================================
SCRIPT NAME: test_groq_kimi.py
=============================================================================

DESCRIPTION:
    Tests the Groq API with the Llama 3.3 70B model
    (llama-3.3-70b-versatile) using the OpenAI-compatible chat completions
    endpoint. Sends a simple prompt and displays the model's response.

    Was originally written against moonshotai/kimi-k2-instruct-0905, which
    Groq retired - it now 404s as model_not_found.

INPUT FILES:
    (none — no file I/O)

OUTPUT FILES:
    (none — no file I/O)

VERSION: 1.0
LAST UPDATED: 2026-06-05
AUTHOR: Arjun Divecha

DEPENDENCIES:
    - requests

USAGE:
    python test_groq_kimi.py

NOTES:
    - API key is read from the GROQ_API_KEY environment variable, falling
      back to /Users/arjundivecha/Dropbox/AAA Backup/.env.txt. It is never
      hardcoded (this repo is public).
    - Requires internet access to api.groq.com
=============================================================================
"""

import os
import requests
import json

ENV_FILE = "/Users/arjundivecha/Dropbox/AAA Backup/.env.txt"


def load_groq_api_key():
    """Return GROQ_API_KEY from the environment, falling back to ENV_FILE.

    The key is deliberately NOT hardcoded: this repo is public, and GitHub's
    secret scanning blocks any push containing a literal Groq key.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key and os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line.startswith("GROQ_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    if not api_key:
        raise RuntimeError(
            f"GROQ_API_KEY not set. Export it, or add it to {ENV_FILE}.")
    return api_key


def test_groq_api():
    """Test the Groq API with Llama 3.3 70B using OpenAI-compatible endpoint"""

    # Configuration from the Factory config
    base_url = "https://api.groq.com/openai/v1"
    api_key = load_groq_api_key()
    model = "llama-3.3-70b-versatile"
    
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
                "content": "Say 'Hello! Llama 3.3 70B on Groq is working!' if you can respond."
            }
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    print(f"Testing Groq API with Llama 3.3 70B model...")
    print(f"URL: {url}")
    print(f"Model: {model}")
    print("-" * 50)
    
    try:
        # Make the API call
        response = requests.post(url, headers=headers, json=data)
        
        # Check response status
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! API call worked!")
            print("\nResponse from Llama 3.3 70B:")
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                print(content)
            print("\nFull response structure:")
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ ERROR: Status code {response.status_code}")
            print(f"Response: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                if "error" in error_data:
                    print(f"\nError details: {error_data['error']}")
            except:
                pass
                
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_groq_api()
