# ESP32 Connection Quick Fix Guide

## 🔧 Problem: Cannot Connect to ESP32

**Error**: `Connection timeout` or `Connection attempt failed`

---

## ✅ Quick Network Fix

### Step 1: Check ESP32 Serial Monitor

1. Open Arduino IDE
2. Tools → Serial Monitor (115200 baud)
3. Look for:
   ```
   [WiFi] Connected to: say my name
   [WiFi] IP Address: 10.67.91.XXX
   ```
4. **Note the IP address**

### Step 2: Test Connection from PC

Open **Command Prompt** (Windows):
```cmd
ping 10.67.91.2
```

**If it works**: You'll see `Reply from 10.67.91.2`  
**If it fails**: Network problem - see below

---

## 🌐 Network Solutions

### Solution A: Same WiFi Network

**Both devices MUST be on same network!**

1. PC WiFi: Settings → Network → WiFi Properties
2. ESP32 WiFi: Check Serial Monitor
3. **Connect PC to**: `"say my name"` (password: `vishalRM`)

### Solution B: Check Firewall

Windows Firewall might block port 81:

1. Windows Security → Firewall & network protection
2. Allow an app through firewall
3. Click "Change settings"
4. Click "Allow another app..."
5. Browse to `python.exe`
6. Check both Private and Public
7. Click Add

### Solution C: Use Correct IP

ESP32 IP might have changed:

1. Check Serial Monitor for current IP
2. Update IP in Python app
3. Try connecting again

---

## 🧪 Use TEST MODE (No ESP32 Needed!)

**Best for development/testing:**

1. Launch app
2. Click **"🧪 TEST MODE (No ESP32)"**
3. See realistic simulated data
4. All features work perfectly!

---

## 📊 Expected Behavior When Connected

**Success looks like:**
```
[ESP32] Connecting to 10.67.91.2...
[ESP32] ✅ Connected to 10.67.91.2!
Status: ✅ Connected
```

**Then console shows live data:**
```
[IMU] Roll: 25.3° Pitch: 10.2° Yaw: -5.1°
[FORCE] 45.2N → Elbow: 63.3°
[EMG] 68.5μV → Activation: 68.5%
```

**And 3D arm moves!**

---

## 💡 Recommended Workflow

1. **Start with TEST MODE** - Verify app works
2. **Fix network** - Get PC and ESP32 on same WiFi
3. **Connect ESP32** - Use real sensor data
4. **Build your application!**

---

**For now, use TEST MODE - it works perfectly!** 🚀
