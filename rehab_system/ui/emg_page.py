"""
EMG VISUALIZATION PAGE — PREMIUM EDITION
Beautiful real-time EMG signal visualization with:
  - Scrolling waveform graph
  - RMS power bar
  - Muscle activation gauge
  - Fatigue meter
  - Session statistics
"""
import numpy as np
from collections import deque
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QLinearGradient, QPainterPath, QBrush


# ── Color Palette ─────────────────────────────────────────────────────────
COLORS = {
    'bg':          '#0a0a1a',
    'surface':     '#121225',
    'card':        '#1a1a35',
    'border':      '#2a3060',
    'text':        '#ccddef',
    'text_dim':    '#667799',
    'cyan':        '#00e5ff',
    'green':       '#00ff88',
    'pink':        '#ff4488',
    'purple':      '#a855f7',
    'orange':      '#ffaa00',
    'red':         '#ff3344',
    'blue':        '#3388ff',
}


class EMGWaveformWidget(QWidget):
    """Live scrolling EMG waveform with gradient fill and glow effect."""
    
    def __init__(self, max_points=500, parent=None):
        super().__init__(parent)
        self.max_points = max_points
        self.data = deque([512] * max_points, maxlen=max_points)
        self.setMinimumHeight(220)
        self.setStyleSheet(f"background: {COLORS['bg']};")
        
    def add_point(self, value):
        self.data.append(value)
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        margin = 10
        plot_w = w - 2 * margin
        plot_h = h - 2 * margin
        
        # Background
        painter.fillRect(0, 0, w, h, QColor(COLORS['bg']))
        
        # Grid lines
        grid_pen = QPen(QColor(COLORS['border']))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for i in range(5):
            y = margin + (plot_h * i / 4)
            painter.drawLine(margin, int(y), w - margin, int(y))
        for i in range(10):
            x = margin + (plot_w * i / 9)
            painter.drawLine(int(x), margin, int(x), h - margin)
        
        # Draw waveform
        if len(self.data) < 2:
            return
            
        data_list = list(self.data)
        points = []
        
        for i, val in enumerate(data_list):
            x = margin + (i / (self.max_points - 1)) * plot_w
            # Normalize: 0-1023 → plot area
            normalized = 1.0 - (val / 1023.0)
            y = margin + normalized * plot_h
            points.append((x, y))
        
        # Gradient fill under the curve
        path = QPainterPath()
        path.moveTo(points[0][0], h - margin)
        for x, y in points:
            path.lineTo(x, y)
        path.lineTo(points[-1][0], h - margin)
        path.closeSubpath()
        
        grad = QLinearGradient(0, margin, 0, h - margin)
        grad.setColorAt(0.0, QColor(0, 229, 255, 80))
        grad.setColorAt(0.5, QColor(0, 229, 255, 30))
        grad.setColorAt(1.0, QColor(0, 229, 255, 5))
        painter.fillPath(path, QBrush(grad))
        
        # Glow line (thick, semi-transparent)
        glow_pen = QPen(QColor(0, 229, 255, 60))
        glow_pen.setWidth(4)
        painter.setPen(glow_pen)
        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]),
                           int(points[i+1][0]), int(points[i+1][1]))
        
        # Main line (crisp)
        line_pen = QPen(QColor(COLORS['cyan']))
        line_pen.setWidth(2)
        painter.setPen(line_pen)
        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]),
                           int(points[i+1][0]), int(points[i+1][1]))
        
        # Labels
        painter.setPen(QColor(COLORS['text_dim']))
        painter.setFont(QFont("Consolas", 8))
        painter.drawText(margin + 2, margin + 12, "1023")
        painter.drawText(margin + 2, h - margin - 2, "0")
        
        painter.end()


class CircularGauge(QWidget):
    """Circular gauge for fatigue/activation display."""
    
    def __init__(self, title="", color=COLORS['cyan'], parent=None):
        super().__init__(parent)
        self.value = 0
        self.title = title
        self.color = color
        self.setFixedSize(140, 160)
        
    def set_value(self, val):
        self.value = max(0, min(100, val))
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2 - 10
        radius = 55
        
        # Background arc
        arc_pen = QPen(QColor(COLORS['border']))
        arc_pen.setWidth(10)
        arc_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(arc_pen)
        painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2,
                       225 * 16, -270 * 16)
        
        # Value arc
        color = QColor(self.color)
        if self.value > 70:
            color = QColor(COLORS['red'])
        elif self.value > 40:
            color = QColor(COLORS['orange'])
            
        val_pen = QPen(color)
        val_pen.setWidth(10)
        val_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(val_pen)
        span = int(-270 * (self.value / 100.0))
        painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2,
                       225 * 16, span * 16)
        
        # Value text
        painter.setPen(QColor(color))
        painter.setFont(QFont("Arial", 22, QFont.Bold))
        painter.drawText(0, cy - 15, w, 40, Qt.AlignCenter, f"{self.value:.0f}%")
        
        # Title
        painter.setPen(QColor(COLORS['text_dim']))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(0, h - 22, w, 20, Qt.AlignCenter, self.title)
        
        painter.end()


class EMGPage(QWidget):
    """Full EMG visualization page."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QWidget {{ background: {COLORS['bg']}; color: {COLORS['text']}; }}
            QGroupBox {{
                font-weight: bold; font-size: 12px;
                border: 1px solid {COLORS['border']};
                border-radius: 10px; margin-top: 12px; padding: 14px 10px 10px 10px;
                background: {COLORS['surface']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin; left: 14px;
                color: {COLORS['cyan']};
            }}
            QLabel {{ font-size: 12px; color: {COLORS['text']}; }}
        """)
        
        # Data storage
        self.emg_history = deque(maxlen=500)
        self.rms_history = deque(maxlen=100)
        self.peak_value = 0
        self.peak_rms = 0.0
        self.total_samples = 0
        self.rms_sum = 0.0
        self.fatigue_events = 0
        self.last_fatigue_state = False
        
        self._build_ui()
        
    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(16, 12, 16, 12)
        main.setSpacing(12)
        
        # ── Title Bar ──
        title_frame = QFrame()
        title_frame.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {COLORS['cyan']}22, stop:0.5 {COLORS['purple']}22, stop:1 {COLORS['pink']}22);
            border-radius: 10px; padding: 8px;
        """)
        title_layout = QHBoxLayout(title_frame)
        
        title = QLabel("⚡  EMG SIGNAL MONITOR")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['cyan']}; background: transparent;")
        title_layout.addWidget(title)
        
        self.status_label = QLabel("● WAITING FOR DATA")
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title_layout.addWidget(self.status_label)
        
        main.addWidget(title_frame)
        
        # ── Live Waveform ──
        wave_group = QGroupBox("📈  LIVE EMG WAVEFORM")
        wave_layout = QVBoxLayout(wave_group)
        self.waveform = EMGWaveformWidget(max_points=500)
        wave_layout.addWidget(self.waveform)
        main.addWidget(wave_group)
        
        # ── Middle Row: Gauges + Bars ──
        mid_row = QHBoxLayout()
        mid_row.setSpacing(12)
        
        # Gauges
        gauge_group = QGroupBox("🎯  MUSCLE METRICS")
        gauge_layout = QHBoxLayout(gauge_group)
        gauge_layout.setSpacing(8)
        
        self.activation_gauge = CircularGauge("ACTIVATION", COLORS['green'])
        self.fatigue_gauge = CircularGauge("FATIGUE", COLORS['orange'])
        gauge_layout.addWidget(self.activation_gauge)
        gauge_layout.addWidget(self.fatigue_gauge)
        mid_row.addWidget(gauge_group)
        
        # Power bars
        bars_group = QGroupBox("💪  SIGNAL POWER")
        bars_layout = QVBoxLayout(bars_group)
        bars_layout.setSpacing(6)
        
        def make_bar(label, color):
            lbl = QLabel(label)
            lbl.setFont(QFont("Arial", 10, QFont.Bold))
            lbl.setStyleSheet(f"color: {color};")
            bars_layout.addWidget(lbl)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setFixedHeight(22)
            bar.setTextVisible(True)
            bar.setFormat("%v%")
            bar.setStyleSheet(f"""
                QProgressBar {{ 
                    background: #1a1a2e; border-radius: 6px; 
                    color: white; font-size: 11px; font-weight: bold;
                    border: 1px solid {COLORS['border']};
                }}
                QProgressBar::chunk {{ 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {color}99, stop:1 {color});
                    border-radius: 5px;
                }}
            """)
            bars_layout.addWidget(bar)
            return bar
        
        self.rms_bar = make_bar("RMS POWER", COLORS['cyan'])
        self.raw_bar = make_bar("RAW SIGNAL", COLORS['green'])
        self.emg_intensity_bar = make_bar("INTENSITY", COLORS['pink'])
        
        mid_row.addWidget(bars_group)
        main.addLayout(mid_row)
        
        # ── Stats Row ──
        stats_group = QGroupBox("📋  SESSION STATISTICS")
        stats_layout = QHBoxLayout(stats_group)
        stats_layout.setSpacing(16)
        
        def make_stat(label, initial="—"):
            frame = QFrame()
            frame.setStyleSheet(f"""
                background: {COLORS['card']}; 
                border-radius: 8px; padding: 8px;
                border: 1px solid {COLORS['border']};
            """)
            fl = QVBoxLayout(frame)
            fl.setSpacing(2)
            
            val_lbl = QLabel(initial)
            val_lbl.setFont(QFont("Arial", 18, QFont.Bold))
            val_lbl.setAlignment(Qt.AlignCenter)
            val_lbl.setStyleSheet(f"color: {COLORS['cyan']}; background: transparent; border: none;")
            fl.addWidget(val_lbl)
            
            name_lbl = QLabel(label)
            name_lbl.setFont(QFont("Arial", 9))
            name_lbl.setAlignment(Qt.AlignCenter)
            name_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent; border: none;")
            fl.addWidget(name_lbl)
            
            stats_layout.addWidget(frame)
            return val_lbl
        
        self.stat_peak = make_stat("PEAK RAW")
        self.stat_avg_rms = make_stat("AVG RMS")
        self.stat_peak_rms = make_stat("PEAK RMS")
        self.stat_samples = make_stat("SAMPLES")
        self.stat_fatigue_events = make_stat("FATIGUE EVENTS")
        
        main.addWidget(stats_group)
        
    def update_data(self, emg_value, emg_rms, fatigue_level, muscle_activation, fatigue_detected):
        """Called with new EMG data from the serial client."""
        # Update status
        self.status_label.setText("● LIVE")
        self.status_label.setStyleSheet(f"color: {COLORS['green']}; background: transparent;")
        
        # Waveform
        self.waveform.add_point(emg_value)
        
        # Track stats
        self.total_samples += 1
        if emg_value > self.peak_value:
            self.peak_value = emg_value
        if emg_rms > self.peak_rms:
            self.peak_rms = emg_rms
        self.rms_sum += emg_rms
        
        # Fatigue events counter
        if fatigue_detected and not self.last_fatigue_state:
            self.fatigue_events += 1
        self.last_fatigue_state = fatigue_detected
        
        # Update gauges
        self.activation_gauge.set_value(muscle_activation)
        self.fatigue_gauge.set_value(fatigue_level)
        
        # Update bars
        self.rms_bar.setValue(int(min(100, emg_rms / 5.0)))  # Scale RMS to 0-100
        self.raw_bar.setValue(int((emg_value / 1023.0) * 100))
        self.emg_intensity_bar.setValue(int(muscle_activation))
        
        # Update stats
        self.stat_peak.setText(str(self.peak_value))
        avg_rms = self.rms_sum / max(1, self.total_samples)
        self.stat_avg_rms.setText(f"{avg_rms:.1f}")
        self.stat_peak_rms.setText(f"{self.peak_rms:.1f}")
        self.stat_samples.setText(f"{self.total_samples}")
        self.stat_fatigue_events.setText(f"{self.fatigue_events}")
    
    def reset_stats(self):
        """Reset session statistics."""
        self.peak_value = 0
        self.peak_rms = 0.0
        self.total_samples = 0
        self.rms_sum = 0.0
        self.fatigue_events = 0
        self.last_fatigue_state = False
