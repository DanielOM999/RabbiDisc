import asyncio
import math
from collections import deque
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import subprocess

TARGET = "90:B1:44:BC:FE:AA"
REFRENCE_RSSI = -69
PATH_LOSS_EXPONENT = 4.0
DISTANCE_TRESHOLD = 10.0
SCAN_INTERVAL = 5

def calculateDistance(rssi):
    return round(10 ** ((REFRENCE_RSSI - (int(rssi)))/(10 * PATH_LOSS_EXPONENT)),2)

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
    distanceReadings = deque(maxlen=3)

    def detectionCallback(device: BLEDevice, advertismentData: AdvertisementData):
        if device.address.upper() == TARGET.upper():
            rssi = advertismentData.rssi
            if rssi is not None:
                distance = calculateDistance(rssi)
                distanceReadings.append(distance)
                print(f"Raw: {distance:.2f}m (RSSI: {rssi})")

    async def cheakAV():
        while True:
            await asyncio.sleep(SCAN_INTERVAL)

            if not distanceReadings:
                print("No recent measurments found")
                continue

            avg_distance = sum(distanceReadings) / len(distanceReadings)
            print(f"\n-- Avrage distance ({len(distanceReadings)} samples): {avg_distance:.2f}m ---")

            if avg_distance < DISTANCE_TRESHOLD:
                print(f"Rabbi phone detected within {DISTANCE_TRESHOLD}m!\nAvrage distance {avg_distance:.2f}m")

    async with BleakScanner(detectionCallback):
        await cheakAV()

if __name__ == "__main__":
    try:
        print(f"Starting proximity monitor for device: {TARGET}")
        print("Press CTRL+C to stop...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitoring stopped!")
