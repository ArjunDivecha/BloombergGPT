# TUNNEL CHECKLIST - Secure Tunnel Setup for Bloomberg Data Broker

## Overview
This checklist provides step-by-step instructions to set up a secure tunnel to expose your local Bloomberg Data Broker over HTTPS. This allows ChatGPT to access the broker securely from the internet.

## Prerequisites
- Bloomberg Data Broker (main.py) running successfully on localhost:8000
- Internet connection for tunnel service
- Ngrok account (free tier available) or similar tunneling service

## Step 1: Install Ngrok
1. Download Ngrok from https://ngrok.com/download
2. Unzip and install on your system
3. Sign up for a free account at https://ngrok.com
4. Get your authtoken from the dashboard

## Step 2: Configure Ngrok
1. Add your authtoken:
   ```
   ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
   ```

## Step 3: Start the Tunnel
1. Run the broker server (if not already running):
   ```
   python main.py
   ```
2. In a new terminal, start ngrok tunnel:
   ```
   ngrok http 8000
   ```

## Step 4: Verify the Tunnel
1. Check the ngrok output for your HTTPS URL (e.g., https://abc123.ngrok.io)
2. Test the tunnel by accessing the endpoints with your API key:
   ```
   curl -H "x-api-key: your-secret-key" https://abc123.ngrok.io/blp/fields
   ```
3. Ensure all responses work correctly

## Step 5: Configure ChatGPT Action
1. In your ChatGPT Custom GPT configuration, set the base URL to your ngrok HTTPS URL
2. Ensure the API key is configured correctly
3. Test the integration

## Security Notes
- Use HTTPS URLs only
- Monitor ngrok usage for rate limits
- Consider upgrading to ngrok paid plan for custom domains if needed
- Rotate API keys regularly

## Troubleshooting
- If tunnel fails, check firewall settings
- Ensure Bloomberg Terminal is running
- Verify API key matches in both broker and ChatGPT configuration
