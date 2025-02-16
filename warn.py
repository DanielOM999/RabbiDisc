# Importerer nødvendige bibloteker
import asyncio
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import subprocess

# Setter opp nødvendige variabler
TARGET = "90:B1:44:BC:FE:AA"
RSSI_THRESHOLD = -70
SCAN_INTERVAL = 5

# Setter opp en alert funksjon
def sendAlert(message):
    subprocess.run([
        "notify-send",
        "Phone Proximity Alert",
        message,
        "-u", "critical"
        "-i", "phone-symbolic"
    ])

# Lager main async funksjonen for å coble til å få rssi til telefonen
async def main():
    target_found = False
    
    # Funkjsonen sjekker om enheten er målet, og varsler hvis RSSI er over terskelen.
    def detectionCallback(device: BLEDevice, advertismentData: AdvertisementData):
        nonlocal target_found
        if device.address.upper() == TARGET.upper():
            rssi = advertismentData.rssi
            print(f"{device.name} found: MAC - ({device.address}) - RSSI: {rssi} dBm")

            if rssi >= RSSI_THRESHOLD and not target_found:
                print(f"Phone is too close! RSSI: {rssi} dBm")
                target_found = True
            elif rssi < RSSI_THRESHOLD and target_found:
                target_found = False

    # scanner etter bluetooth devices og i while loopen wenter for scan_interval tiden (5sek)
    async with BleakScanner(detectionCallback):
        while True:
            await asyncio.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    try:
        print(f"Starting proximity monitor for device: {TARGET}")
        print("Press CTRL+C to stop...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitoring stopped!")
