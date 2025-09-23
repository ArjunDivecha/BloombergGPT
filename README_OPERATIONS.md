# Bloomberg Data Broker - Operations Guide

## 🚀 Quick Start

### One-Time Setup (First Use)
1. **Run setup**: Double-click `setup_environment.bat`
2. **Set ngrok authtoken**: Get your token from [ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken)
3. **Configure ngrok**: Run `ngrok config add-authtoken YOUR_TOKEN`

### Daily Use (Single Click!)
1. **Start Bloomberg Terminal** and log in
2. **Double-click** `Start Bloomberg Broker.lnk` on your desktop
3. **Use your Bloomberg ChatGPT!**

## 📁 File Structure

```
Bloomberg-Data-Broker/
├── main.py                     # Bloomberg API broker server
├── requirements.txt            # Python dependencies
├── start_bloomberg_broker.bat  # 🟢 START - Single click startup
├── stop_bloomberg_broker.bat   # 🔴 STOP - Single click shutdown  
├── check_status.bat           # ℹ️ STATUS - Check system health
├── setup_environment.bat      # ⚙️ SETUP - One-time environment setup
└── README_OPERATIONS.md       # This file
```

## 🎯 Operation Commands

| Action | File | Description |
|--------|------|-------------|
| **Start System** | `start_bloomberg_broker.bat` | Starts broker + ngrok tunnel |
| **Stop System** | `stop_bloomberg_broker.bat` | Stops all processes |
| **Check Status** | `check_status.bat` | Verify system health |
| **First Setup** | `setup_environment.bat` | Install dependencies + shortcuts |

## 🔧 System Components

### 1. Bloomberg Data Broker
- **Port**: 8000
- **API Key**: `Caeser00**`
- **Endpoints**: `/blp/fields`, `/blp/coverage`, `/blp/refdata`, `/blp/historical`

### 2. ngrok Tunnel
- **Purpose**: Exposes local broker via HTTPS for ChatGPT
- **URL**: Changes each restart (displayed in ngrok window)
- **Config**: Requires authtoken from ngrok.com

### 3. Bloomberg Terminal
- **Requirement**: Must be running and logged in
- **Connection**: Local API via port 8194
- **Data**: Real-time and historical market data

## 🏥 Health Checks

### Quick Status Check
```bash
check_status.bat
```

### Manual Verification
1. **Broker Health**: Visit `http://localhost:8000/blp/fields`
2. **ngrok Status**: Check ngrok window for HTTPS URL
3. **Bloomberg**: Verify Terminal is logged in

## 🐛 Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| Port 8000 in use | Run `stop_bloomberg_broker.bat` |
| ngrok not found | Check ngrok path in start script |
| Bloomberg API error | Verify Terminal is running and logged in |
| ChatGPT can't connect | Update ChatGPT with new ngrok URL |

### Error Messages

**"Failed to start Bloomberg session"**
- ✅ Bloomberg Terminal running?
- ✅ Logged into Bloomberg?
- ✅ Bloomberg API installed?

**"Authentication failed: Usage of ngrok requires authtoken"**
- ✅ Get authtoken from [ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken)
- ✅ Run: `ngrok config add-authtoken YOUR_TOKEN`

**"Port 8000 already in use"**
- ✅ Run `stop_bloomberg_broker.bat`
- ✅ Kill process: `taskkill /F /IM python.exe`

## 🔄 Daily Workflow

### Morning Startup
1. Open Bloomberg Terminal → Log in
2. Double-click `Start Bloomberg Broker` desktop shortcut
3. Copy ngrok HTTPS URL from tunnel window
4. Update ChatGPT Custom GPT if URL changed
5. Start using Bloomberg ChatGPT!

### Evening Shutdown
1. Double-click `Stop Bloomberg Broker` desktop shortcut
2. Close Bloomberg Terminal (optional)

## 🔐 Security Notes

- **API Key**: `Caeser00**` - Change if needed in `main.py`
- **Local Only**: Broker only accepts connections from localhost
- **HTTPS**: All ChatGPT communication via secure ngrok tunnel
- **Authentication**: Bloomberg Terminal handles user authentication

## 📊 System Requirements

- **Python**: 3.8+
- **Bloomberg Terminal**: Active subscription and login
- **Internet**: For ngrok tunnel
- **Ports**: 8000 (broker), 8194 (Bloomberg API)

## 🆘 Support

### Log Files
- **Broker logs**: Displayed in broker window
- **ngrok logs**: Displayed in ngrok window
- **System logs**: Check Windows Event Viewer

### Reset Everything
1. Run `stop_bloomberg_broker.bat`
2. Restart Bloomberg Terminal
3. Run `start_bloomberg_broker.bat`

---

## 🎉 Success Indicators

When everything is working:
- ✅ Bloomberg Terminal: Logged in and responsive
- ✅ Broker Window: "Uvicorn running on http://0.0.0.0:8000"
- ✅ ngrok Window: Shows HTTPS URL (e.g., `https://abc123.ngrok.io`)
- ✅ ChatGPT: Returns real Bloomberg data with charts

**Your Bloomberg AI Assistant is ready!** 🚀





