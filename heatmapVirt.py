# Importerer nødvendige biblioteker og setter matplotlib til å ikke plotte i sannti
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

# Setter opp viktige variabler som brukes i programmet
TARGET = "90:B1:44:BC:FE:AA"
REFERENCE_RSSI = -69 # Hvis du bruker prosjektet selv burde denne endres etter testing
PATH_LOSS_EXPONENT = 4.0 # Hvis du er åpen som ute burde denne være 2.0
MAX_DISTANCE = 10
GRID_RES = 1.0
SCAN_INTERVAL = 5
DISTANCE_THRESHOLD = 10.0
DENSITY_DECAY = 0.9

# Funksjon for å beregne avstand basert på RSSI
def calculate_distance(rssi):
    return round(10 ** ((REFERENCE_RSSI - rssi) / (10 * PATH_LOSS_EXPONENT)), 2)

# Klasse for å lage og oppdatere heatmap
class HeatMap:
    # Konstruktøren som initialiserer HeatMap
    def __init__(self):
        self.distance_readings = deque(maxlen=3)
        self.heatmap_setup()
        

    # Funksjon for å sette opp heatmapet
    def heatmap_setup(self):
	# Lager en figur og akse for plotting
        self.fig, self.ax = plt.subplots()
        grid_size = int(MAX_DISTANCE * 2 / GRID_RES)
        self.grid = np.zeros((grid_size, grid_size))
        
	# Setter opp visningens utstrekning og farger
        extent = [-MAX_DISTANCE, MAX_DISTANCE, -MAX_DISTANCE, MAX_DISTANCE]
        self.im = self.ax.imshow(
            self.grid.T,
            origin='lower',
            extent=extent,
            cmap='hot',
            vmin=0,
            vmax=10
        )
        
	# Setter tittel og etiketter for aksene
        self.ax.set_title("Device Presence Density Around Computer")
        self.ax.set_xlabel("X Distance from Computer (m)")
        self.ax.set_ylabel("Y Distance from Computer (m)")
        plt.colorbar(self.im, label="Detection Density")

    # Funksjon for å legge til nye målinger i heatmapet
    def add_reading(self, distance):
        angle = np.random.uniform(0, 2 * np.pi)
        x = distance * math.cos(angle)
        y = distance * math.sin(angle)
        
	# Beregner hvilke grid-koordinater x og y tilsvarer
        xi = int((x + MAX_DISTANCE) / GRID_RES)
        yi = int((y + MAX_DISTANCE) / GRID_RES)
        
	# Sjekker om koordinatene er innenfor gridets dimensjoner
        if 0 <= xi < self.grid.shape[1] and 0 <= yi < self.grid.shape[0]:
            self.grid[yi, xi] += 1
        
	# Reduserer verdiene i gridet over tid (simulerer at signalet mister styrken)
        self.grid *= DENSITY_DECAY
        self.im.set_data(self.grid.T)
        self.im.autoscale()
        self.fig.canvas.draw_idle()

    # Funksjon for å lagre det siste bildet av heatmapet
    def save_last_frame(self):
        plt.savefig("heatmap.png")
        print("Heatmap saved as 'heatmap.png'")

# Hovedfunksjonen som starter prosessen
async def main():
    visualizer = HeatMap()
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    # Funksjon for å håndtere når brukeren stopper programmet (CTRL+C)
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

    # Funksjon som behandler målinger
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

    # Start scanning etter enheter
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

# Sjekker om programet er blit kjørt som main og så runner main() async
if __name__ == "__main__":
    asyncio.run(main())
