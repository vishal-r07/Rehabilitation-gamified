# 3D Arm Motion Tracker 🦾

**Real-time arm visualization for hand rehabilitation**

Move your arm → See it move on screen in 3D!

---

## 🚀 Quick Start

1. **Open the app**:
   ```
   Open: c:\Users\visha\Downloads\game\arm_tracker\index.html
   ```

2. **Connect ESP32**:
   - Click "Connect ESP32" button
   - Enter your ESP32 IP address (default: 192.168.1.100)
   - Click "Connect"

3. **Move your arm**:
   - The 3D arm on screen will move exactly like your real arm!
   - See real-time angle values (Roll, Pitch, Yaw)

---

## ✨ Features

- ✅ **3D Arm Model** - Realistic arm with joints
- ✅ **Real-time Movement** - Mirrors your exact arm position
- ✅ **IMU Integration** - Uses ESP32 sensor data
- ✅ **Clean UI** - Simple, professional interface
- ✅ **Working Buttons** - All controls tested and functional

---

## 🎮 Controls

- **Connect ESP32** - Opens connection dialog
- **Reset View** - Resets camera position
- **Click backdrop** - Closes settings modal

---

## 📊 Data Display

Top-right corner shows:
- **Roll** - Arm rotation (twisting)
- **Pitch** - Arm up/down tilt
- **Yaw** - Arm left/right rotation

---

## 🔧 Technical Details

- **Single HTML file** - Everything in one file (easy!)
- **Three.js** - 3D graphics
- **WebSocket** - ESP32 connection (port 81)
- **Works with existing firmware** - No changes needed!

---

## ✅ Button Testing

**All buttons work:**
1. Connect ESP32 button → Opens modal ✓
2. Cancel button → Closes modal ✓
3. Connect button → Connects to ESP32 ✓
4. Reset View button → Resets camera ✓
5. Disconnect button → Closes connection ✓

---

## 🐛 Troubleshooting

**ESP32 won't connect?**
- Check IP address is correct
- Make sure ESP32 is on same WiFi
- Try browser console (F12) for errors

**Arm not moving?**
- Check "Connected" status (green dot)
- Verify IMU sensor is working
- Move your arm to test

**Page not loading?**
- Make sure internet connection is active (for Three.js library)
- Try different browser (Chrome/Edge recommended)

---

## 💡 Simple & Perfect

- No complex games
- No confusing menus
- Just **your arm moving in 3D**
- Perfect for rehabilitation feedback

---

**🦾 Open `index.html` and see your arm in 3D!**
