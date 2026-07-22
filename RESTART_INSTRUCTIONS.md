# How to Restart Bloomberg Broker and Cloudflare Tunnel

## Quick Restart (Easiest)

### Step 1: Stop Everything
Double-click: **`stop_bloomberg_broker.bat`**

This will:
- Kill the Python broker process
- Kill the Cloudflare tunnel process
- Confirm port 8000 is free

### Step 2: Start Everything
Double-click: **`start_bloomberg_broker.bat`**

This will:
- Start the Bloomberg broker (main.py on port 8000)
- Start the Cloudflare tunnel (broker.dancing-ganesh.com)
- Start the status checker

### Step 3: Verify It's Working
A status window should open showing:
```
[OK] Bloomberg Terminal
[OK] Python broker running
[OK] API endpoints responding
[OK] Cloudflare tunnel active
```

---

## Manual Restart (If Batch Files Don't Work)

### Stop Processes Manually

1. **Open Task Manager** (Ctrl + Shift + Esc)
2. **End these processes:**
   - Any `python.exe` processes
   - Any `cloudflared.exe` processes

### Start Bloomberg Broker

1. **Open PowerShell** in the BloombergGPT folder
2. **Run:**
   ```powershell
   python main.py
   ```
3. **Wait for:** "Starting Bloomberg Data Broker on 0.0.0.0:8000"

### Start Cloudflare Tunnel (in separate window)

1. **Open another PowerShell** window
2. **Navigate to BloombergGPT folder:**
   ```powershell
   cd "\\mac\Dropbox-1\AAA Backup\A Working\BloombergGPT"
   ```
3. **Run:**
   ```powershell
   .\cloudflared.exe tunnel --config "C:\Users\macbook2024\Documents\cloudflared-broker.yml" run bloomberg-broker
   ```
4. **Wait for:** "Connection registered" message

### Verify Tunnel is Working

1. **Test locally:**
   ```powershell
   Invoke-WebRequest "http://localhost:8000/blp/fields?limit=1" -Headers @{"x-api-key"="Caeser00**"}
   ```

2. **Test via Cloudflare:**
   ```powershell
   Invoke-WebRequest "https://broker.dancing-ganesh.com/blp/fields?limit=1" -Headers @{"x-api-key"="Caeser00**"}
   ```

Both should return JSON data.

---

## Troubleshooting

### Problem: Broker won't start
**Error:** "Address already in use"
**Solution:**
```powershell
# Kill process on port 8000
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

### Problem: Tunnel won't connect
**Error:** "Cloudflared couldn't resolve the broker connection"
**Possible causes:**
1. **Broker not running** - Start broker first (main.py)
2. **Wrong config path** - Check cloudflared-broker.yml location
3. **Tunnel credentials expired** - Run `cloudflared tunnel login` again

**Solution:**
```powershell
# Verify tunnel config
.\cloudflared.exe tunnel info bloomberg-broker

# If issues, recreate tunnel route
.\cloudflared.exe tunnel route dns bloomberg-broker broker.dancing-ganesh.com
```

### Problem: Bloomberg Terminal not responding
**Error:** "Bloomberg API not available"
**Solution:**
1. Ensure Bloomberg Terminal is **fully logged in**
2. Test with: `SECF <GO>` in terminal
3. Restart terminal if necessary
4. Restart broker after terminal is ready

---

## Quick Health Check

After restarting, run:
```powershell
python check_status.py
```

This will verify:
- ✓ Bloomberg Terminal is running
- ✓ Python broker is active
- ✓ API endpoints are responding
- ✓ Cloudflare tunnel is connected

---

## Full System Restart (Nuclear Option)

If nothing works:

1. **Close everything:**
   - Close all PowerShell windows
   - End all python.exe and cloudflared.exe in Task Manager
   - Close Bloomberg Terminal

2. **Start fresh:**
   - Launch Bloomberg Terminal and log in completely
   - Wait for it to fully load
   - Double-click `start_bloomberg_broker.bat`
   - Wait for status window to show all [OK]

3. **Test:**
   ```powershell
   python test_field_service_quick.py
   ```

---

## Current Status Check

To see what's currently running:

```powershell
# Check for broker process
Get-Process python -ErrorAction SilentlyContinue

# Check for tunnel process
Get-Process cloudflared -ErrorAction SilentlyContinue

# Check port 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

# Check Bloomberg Terminal
Get-Process bloomberg -ErrorAction SilentlyContinue
```

---

## Cloudflare-Specific Troubleshooting

### If tunnel keeps disconnecting:

1. **Check Cloudflare dashboard:**
   - Go to https://dash.cloudflare.com
   - Navigate to your domain
   - Check DNS records for `broker.dancing-ganesh.com`
   - Should point to `<tunnel-id>.cfargotunnel.com`

2. **Regenerate tunnel credentials:**
   ```powershell
   .\cloudflared.exe tunnel login
   .\cloudflared.exe tunnel list
   .\cloudflared.exe tunnel route dns bloomberg-broker broker.dancing-ganesh.com
   ```

3. **Update cloudflared:**
   ```powershell
   .\cloudflared.exe update
   ```

---

## For ChatGPT to Test

Once everything is restarted, ChatGPT should be able to:

```bash
# Get Apple's current data
GET https://broker.dancing-ganesh.com/blp/refdata?ticker=AAPL&fields=LAST_PRICE,VOLUME,CUR_MKT_CAP,PE_RATIO
Headers: x-api-key: Caeser00**
```

If this works, the tunnel is fully operational!

---

**Recommended: Just double-click `stop_bloomberg_broker.bat` then `start_bloomberg_broker.bat`** 🚀

