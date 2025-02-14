import matplotlib
matplotlib.use('Agg')
import asyncio
import math
import numpy as np
import matplotlib.pyplot as plt
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from collections import deque
import subprocess
import signal

TARGET = "90:B1:44:BC:FE:AA"
REFERENCE_RSSI = -69
PATH_LOSS_EXPONENT = 4.0
MAX_DISTANCE = 10
GRID_RES = 1.0
SCAN_INTERVAL = 5
DISTANCE_THRESHOLD = 10.0
DENSITY_DECAY = 0.9

def calculate_distance(rssi):
    return round(10 ** ((REFERENCE_RSSI - rssi) / (10 * PATH_LOSS_EXPONENT)), 2)

class HeatMap:
    def __init__(self):
        self.distance_readings = deque(maxlen=3)
        self.heatmap_setup()
        
    def heatmap_setup(self):
        self.fig, self.ax = plt.subplots()
        grid_size = int(MAX_DISTANCE * 2 / GRID_RES)
        self.grid = np.zeros((grid_size, grid_size))
        
        extent = [-MAX_DISTANCE, MAX_DISTANCE, -MAX_DISTANCE, MAX_DISTANCE]
        self.im = self.ax.imshow(
            self.grid.T,
            origin='lower',
            extent=extent,
            cmap='hot',
            vmin=0,
            vmax=10
        )
        
        self.ax.set_title("Device Presence Density Around Computer")
        self.ax.set_xlabel("X Distance from Computer (m)")
        self.ax.set_ylabel("Y Distance from Computer (m)")
        plt.colorbar(self.im, label="Detection Density")

    def add_reading(self, distance):
        angle = np.random.uniform(0, 2 * np.pi)
        x = distance * math.cos(angle)
        y = distance * math.sin(angle)
        
        xi = int((x + MAX_DISTANCE) / GRID_RES)
        yi = int((y + MAX_DISTANCE) / GRID_RES)
        
        if 0 <= xi < self.grid.shape[1] and 0 <= yi < self.grid.shape[0]:
            self.grid[yi, xi] += 1
            
        self.grid *= DENSITY_DECAY
        self.im.set_data(self.grid.T)
        self.im.autoscale()
        self.fig.canvas.draw_idle()

    def save_last_frame(self):
        plt.savefig("heatmap.png")
        print("Heatmap saved as 'heatmap.png'")

async def main():
    visualizer = HeatMap()
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def signal_handler():
        print("\nMonitoring stopped..")
        visualizer.save_last_frame()
        stop_event.set()

    loop.add_signal_handler(signal.SIGINT, signal_handler)

    def detection_callback(device: BLEDevice, adv: AdvertisementData):
        if device.address.upper() == TARGET.upper() and adv.rssi is not None:
            distance = calculate_distance(adv.rssi)
            visualizer.distance_readings.append(distance)
            print(f"New RSSI: {adv.rssi} dBm | Calculated distance: {distance}m")

    async def process_readings():
        while True:
            await asyncio.sleep(SCAN_INTERVAL)
            
            if not visualizer.distance_readings:
                print("No recent measurements found")
                continue
                
            avg_distance = sum(visualizer.distance_readings) / len(visualizer.distance_readings)
            clamped_distance = min(avg_distance, MAX_DISTANCE)
            
            print(f"Average distance ({len(visualizer.distance_readings)} samples): {avg_distance:.2f}m")
            visualizer.add_reading(clamped_distance)

    async with BleakScanner(detection_callback):
        print(f"Monitoring device {TARGET}")
        print(f"Tracking radius: {MAX_DISTANCE}m around computer")
        
        processing_task = asyncio.create_task(process_readings())
        await stop_event.wait()
        processing_task.cancel()
        
        try:
            await processing_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main())
