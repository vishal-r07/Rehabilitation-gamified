# RehabiHand - 3D Hand Rehabilitation Game 🤚

An advanced **3D hand rehabilitation game** that integrates real-time sensor data from ESP32 (IMU, Force Sensor, EMG) to drive a realistic hand model with gamified physiotherapy exercises.

![RehabiHand](https://img.shields.io/badge/Status-Ready%20to%20Play-brightgreen) ![Three.js](https://img.shields.io/badge/Three.js-r158-blue) ![WebSocket](https://img.shields.io/badge/WebSocket-Realtime-orange)

## ✨ Features

### 🎮 5 Rehabilitation Game Modes
1. **Range of Motion (ROM) Trainer** - Match target finger positions
2. **Grip Strength Challenge** - Maintain specific EMG levels
3. **Finger Coordination** - Simon Says with hand gestures
4. **Object Manipulation** - Pick & place virtual objects
5. **Endurance Mode** - Sustained repetitive exercises

### 🏆 Gamification System
- **Achievements** - 7 unlockable achievements
- **Level Progression** - Score-based leveling
- **Progress Tracking** - Daily stats and streaks
- **Leaderboards** - Personal bests

### 🖐️ Realistic 3D Hand Model
- Anatomically accurate (20+ bones/joints)
- Smooth IK-based finger bending
- Real-time sensor-driven animation
- EMG visualization on hand
- Form feedback (color changes)

### 📡 Real-Time Sensor Integration
- **WebSocket** connection to ESP32
- **IMU** (BNO08x) for hand orientation
- **Force Sensor** for finger flex simulation
- **EMG** for muscle activity
- **<100ms latency** for responsive control

### 🎨 Premium UI/UX
- **Glassmorphism** dark theme
- **Smooth animations** with GSAP
- **Dynamic lighting** (cyan, purple gradients)
- **Particle effects** for celebrations
- **Accessibility** - keyboard shortcuts

---

## 🚀 Quick Start

### Prerequisites
- **ESP32** with sensors (IMU, Force, EMG)
- **Modern browser** (Chrome/Edge recommended)
- **WiFi network** for ESP32 connection

### Installation

1. **Upload ESP firmware** (if not already done):
   ```bash
   # In Arduino IDE, upload:
   # ../esp32_firmware/bicep_curl_counter/bicep_curl_counter.ino
   ```

2. **Open the game**:
   ```bash
   # Simply open in browser:
   file:///c:/Users/visha/Downloads/game/hand_rehab/index.html
   
   # OR use Live Server in VS Code
   ```

3. **Connect to ESP32**:
   - Enter ESP32 IP address in settings (default: 192.168.1.100)
   - Click "Connect ESP32" button
   - Wait for green "Connected" status

4. **Start playing!**:
   - Select a game mode from the grid
   - Follow on-screen instructions
   - Track your progress and achievements

---

## 🎯 How to Play

### Game 1: Range of Motion
- **Goal**: Match the target finger bend percentages
- **Controls**: Flex your fingers naturally
- **Scoring**: 100 points per perfect match
- **Tips**: Green = perfect, Yellow = close, Red = adjust

### Game 2: Grip Strength
- **Goal**: Maintain target muscle activation (EMG)
- **Controls**: Squeeze to activate muscles
- **Scoring**: 10 points/second while holding
- **Tips**: Steady pressure is better than bursts

### Game 3: Coordination
- **Goal**: Match the displayed hand gesture
- **Available Gestures**: Fist, Open, Point, Peace, Thumbs Up, Pinch
- **Scoring**: 200 + time bonus (faster = more points)
- **Tips**: Practice gestures before starting

### Game 4: Object Manipulation
- **Goal**: Grab virtual cube and move to target zone
- **Controls**: Close fist to grab, move hand to place
- **Scoring**: 300 points per successful placement
- **Tips**: Smooth movements work best

### Game 5: Endurance Mode
- **Goal**: Perform repetitive open/close hand exercises
- **Controls**: Open and close hand repeatedly
- **Scoring**: 50 points per rep
- **Tips**: Maintain steady rhythm for best results

---

## ⌨️ Keyboard Shortcuts

- **C** - Connect/Disconnect ESP32
- **R** - Reset hand to neutral pose
- **ESC** - Exit current game
- **⚙️ Button** - Open settings panel

---

## 🔧 Configuration

### ESP32 IP Address
1. Click the ⚙️ settings button
2. Enter your ESP32's IP address
3. IP is auto-saved for next session

### Difficulty Levels
- **Easy** - Relaxed targets, more tolerance
- **Medium** - Balanced challenge (default)
- **Hard** - Precise targets, strict timing

### Visual Quality
- **Low** - 1x pixel ratio (better performance)
- **Medium** - 1.5x
- **High** - 2x (default)
- **Ultra** - 2.5x (best quality, requires GPU)

---

## 📊 Progress Tracking

All progress is **automatically saved** in browser localStorage:
- Total score and level
- Total reps performed
- Perfect form reps
- Games played count
- Daily statistics
- Achievement unlocks
- Training streaks

**To reset progress**: Open browser console and run:
```javascript
app.gamificationSystem.resetProgress();
```

---

## 🏆 Achievements

| Icon | Name | Description |
|------|------|-------------|
| 🎯 | First Step | Complete your first repetition |
| 💪 | Getting Started | Complete 10 repetitions |
| 🏆 | Century Club | Complete 100 repetitions |
| ✨ | Perfection | 10 perfect form reps in a row |
| 🎮 | High Roller | Score 10,000 points |
| 🌟 | Complete Collection | Play all 5 game modes |
| 🔥 | Week Warrior | Train for 7 days in a row |

---

## 🛠️ Technical Details

### Technology Stack
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **3D Engine**: Three.js r158
- **Animation**: Custom IK solver + LERP smoothing
- **Networking**: WebSocket (native API)
- **Storage**: localStorage
- **Audio**: Web Audio API (procedural sounds)

### Architecture
```
RehabiHand App
├── Scene Manager (Three.js setup, lighting, particles)
├── Hand Model (3D hand with IK, gestures, animations)
├── WebSocket Client (ESP32 communication, auto-reconnect)
├── Animation Controller (Sensor → hand mapping)
├── Game Engine (5 game modes, scoring)
├── Gamification System (achievements, levels, progress)
└── Feedback System (audio, visual, form indicators)
```

### Performance
- **Target**: 60 FPS on modern hardware
- **3D Rendering**: Hardware-accelerated WebGL
- **Sensor Latency**: <100ms end-to-end
- **Memory**: ~50MB typical usage

---

## 🐛 Troubleshooting

### ESP32 Won't Connect
1. Check ESP32 is powered and running
2. Verify both devices on same WiFi network
3. Check IP address is correct
4. Try browser console (F12) for error messages

### Hand Not Moving
1. Verify "Connected" status is green
2. Check IMU status shows ✓
3. Ensure sensors are properly calibrated
4. Try "Calibrate Sensors" button in settings

### Low FPS / Laggy
1. Reduce visual quality in settings
2. Close other browser tabs
3. Update graphics drivers
4. Try Chrome/Edge instead of Firefox

### Sensors Reading Wrong Values
1. Click "Calibrate Sensors" in settings
2. Keep arm relaxed during baseline (2s)
3. Flex hard during max calibration (3s)
4. Repeat if values still off

---

## 🔮 Future Enhancements

- [ ] **Individual flex sensors** (5 sensors for each finger)
- [ ] **Multiplayer mode** (compete with friends)
- [ ] **Custom exercise creator** (design your own exercises)
- [ ] **Mobile app version** (Flutter WebView)
- [ ] **Cloud sync** (save progress across devices)
- [ ] **Physical therapy reports** (PDF export for doctors)
- [ ] **VR support** (Meta Quest integration)

---

## 📝 Credits

**Developed by**: RehabiHand Team  
**Built with**: Three.js, WebSocket, ESP32  
**Inspired by**: Modern gamified rehabilitation systems  

---

## 📄 License

This project is for educational and rehabilitation purposes.  
Feel free to modify and adapt for your needs!

---

## 💬 Support

Having issues? Want to contribute?  
- Check the troubleshooting section above
- Review ESP32 firmware in `../esp32_firmware/`
- Test with the included sensor monitoring tools

---

**🎉 Start your rehabilitation journey today!**  
*Making physiotherapy fun, one game at a time.*
