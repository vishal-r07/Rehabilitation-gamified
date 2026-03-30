"""
Real-Time Sensor Data Graphs
Live plotting of IMU, Force, and EMG signals
"""
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from collections import deque


class SensorGraphWidget(FigureCanvasQTAgg):
    """Real-time graph for sensor data"""
    def __init__(self, title, ylabel, max_points=200, parent=None):
        self.fig = Figure(figsize=(8, 3), facecolor='#1e1e1e')
        super().__init__(self.fig)
        self.setParent(parent)
        
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#2a2a2a')
        self.ax.set_title(title, color='white', fontsize=10)
        self.ax.set_ylabel(ylabel, color='white')
        self.ax.tick_params(colors='white')
        self.ax.grid(True, alpha=0.2)
        
        # Data storage
        self.max_points = max_points
        self.time_data = deque(maxlen=max_points)
        self.value_data = deque(maxlen=max_points)
        self.line = None
        self.start_time = 0
        
        self.fig.tight_layout()
        
    def update_data(self, value):
        """Add new data point"""
        if len(self.time_data) == 0:
            self.start_time = 0
            current_time = 0
        else:
            current_time = self.time_data[-1] + 0.05  # 50ms updates
            
        self.time_data.append(current_time)
        self.value_data.append(value)
        
        # Redraw
        self.ax.clear()
        self.ax.set_facecolor('#2a2a2a')
        self.ax.grid(True, alpha=0.2)
        self.ax.tick_params(colors='white')
        
        if len(self.time_data) > 0:
            self.ax.plot(list(self.time_data), list(self.value_data),
                        color='#00ffff', linewidth=2)
            self.ax.fill_between(list(self.time_data), 0, list(self.value_data),
                                alpha=0.3, color='#00ffff')
        
        self.draw()


class MultiSensorGraph(FigureCanvasQTAgg):
    """Combined graph for all three sensors"""
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(10, 6), facecolor='#1e1e1e')
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Create 3 subplots
        self.ax_imu = self.fig.add_subplot(311)
        self.ax_force = self.fig.add_subplot(312)
        self.ax_emg = self.fig.add_subplot(313)
        
        for ax, title in [(self.ax_imu, "IMU (deg)"),
                          (self.ax_force, "Force (N)"),
                          (self.ax_emg, "EMG (μV)")]:
            ax.set_facecolor('#2a2a2a')
            ax.set_title(title, color='white', fontsize=9)
            ax.tick_params(colors='white', labelsize=8)
            ax.grid(True, alpha=0.2)
            
        # Data storage
        self.max_points = 200
        self.time = deque(maxlen=self.max_points)
        self.roll = deque(maxlen=self.max_points)
        self.pitch = deque(maxlen=self.max_points)
        self.yaw = deque(maxlen=self.max_points)
        self.force = deque(maxlen=self.max_points)
        self.emg = deque(maxlen=self.max_points)
        
        self.fig.tight_layout()
        
    def update_all(self, imu_data, force_val, emg_val):
        """Update all graphs"""
        # Add data
        if len(self.time) == 0:
            t = 0
        else:
            t = self.time[-1] + 0.05
            
        self.time.append(t)
        self.roll.append(imu_data['roll'])
        self.pitch.append(imu_data['pitch'])
        self.yaw.append(imu_data['yaw'])
        self.force.append(force_val)
        self.emg.append(emg_val)
        
        # Redraw all
        for ax in [self.ax_imu, self.ax_force, self.ax_emg]:
            ax.clear()
            ax.set_facecolor('#2a2a2a')
            ax.grid(True, alpha=0.2)
            ax.tick_params(colors='white', labelsize=8)
            
        # IMU plot
        t_list = list(self.time)
        self.ax_imu.plot(t_list, list(self.roll), 'r-', label='Roll', linewidth=1.5)
        self.ax_imu.plot(t_list, list(self.pitch), 'g-', label='Pitch', linewidth=1.5)
        self.ax_imu.plot(t_list, list(self.yaw), 'b-', label='Yaw', linewidth=1.5)
        self.ax_imu.legend(loc='upper right', fontsize=7)
        self.ax_imu.set_ylabel('Degrees', color='white', fontsize=8)
        
        # Force plot
        self.ax_force.plot(t_list, list(self.force), color='#00ffff', linewidth=2)
        self.ax_force.fill_between(t_list, 0, list(self.force), alpha=0.3, color='#00ffff')
        self.ax_force.set_ylabel('Newtons', color='white', fontsize=8)
        
        # EMG plot
        self.ax_emg.plot(t_list, list(self.emg), color='#ff00ff', linewidth=2)
        self.ax_emg.fill_between(t_list, 0, list(self.emg), alpha=0.3, color='#ff00ff')
        self.ax_emg.set_ylabel('μV', color='white', fontsize=8)
        self.ax_emg.set_xlabel('Time (s)', color='white', fontsize=8)
        
        self.fig.tight_layout()
        self.draw()
