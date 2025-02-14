import asyncio
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import subprocess

TARGET = "90:B1:44:BC:FE:AA"

RSSI_THRESHOLD = 10
SCAN_INTERVAL = 5

def sendAlert(message):
    """Sends desktop"""
    subprocess.run([
        "notify-send",
        "Phone Proximity Alert",
        message,
        "-u", "critical"
        "-i", "phone-symbolic"
    ])

async def main():
    target_found = False

    def detectionCallback(device: BLEDevice, advertismentData: AdvertisementData):
        nonlocal target_found
        if device.address.upper() == TARGET.upper():
            n=2
            mp=-69
            rssi = advertismentData.rssi
            distanceCal = round(10 ** ((mp - (int(rssi)))/(10 * n)),2)
            print(f"{device.name} found: MAC - ({device.address}) - RSSI: {rssi} dBm - distance: {distanceCal} m")
            if distanceCal <= RSSI_THRESHOLD and not target_found:
                print(f"Phone is too close! RSSI: {rssi} dBm - distance: {distanceCal} m")
                target_found = True
            elif distanceCal > RSSI_THRESHOLD and target_found:
                target_found = False

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
