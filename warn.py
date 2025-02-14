import asyncio
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import subprocess

TARGET = "90:B1:44:BC:FE:AA"

RSSI_THRESHOLD = -70
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
            rssi = advertismentData.rssi
            print(f"{device.name} found: MAC - ({device.address}) - RSSI: {rssi} dBm")

            if rssi >= RSSI_THRESHOLD and not target_found:
                print(f"Phone is too close! RSSI: {rssi} dBm")
                target_found = True
            elif rssi < RSSI_THRESHOLD and target_found:
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