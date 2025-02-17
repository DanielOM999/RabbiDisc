# Importerer nødvendige bibloteker
import asyncio
import math
from collections import deque
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import subprocess

# Setter opp nødvendige variabler
TARGET = "90:B1:44:BC:FE:AA"
REFRENCE_RSSI = -69
PATH_LOSS_EXPONENT = 4.0
DISTANCE_TRESHOLD = 10.0
SCAN_INTERVAL = 5

# funksjon til å beregne avstand basert på RSSI
def calculateDistance(rssi):
    return round(10 ** ((REFRENCE_RSSI - (int(rssi)))/(10 * PATH_LOSS_EXPONENT)),2)

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
    distanceReadings = deque(maxlen=3)

    def detectionCallback(device: BLEDevice, advertismentData: AdvertisementData):
        if device.address.upper() == TARGET.upper():
            rssi = advertismentData.rssi
            if rssi is not None:
                distance = calculateDistance(rssi)
                distanceReadings.append(distance)
                print(f"Raw: {distance:.2f}m (RSSI: {rssi})")

    # setter opp funksjonen med main loopen
    async def cheakAV():
        while True:
            # wenter for tiden til variablen SCAN_INTERVAL
            await asyncio.sleep(SCAN_INTERVAL)
            
            # hvis det ikke er distance readings så printes det og programet forsettes
            if not distanceReadings:
                print("No recent measurments found")
                continue
            
            # regner avrage distance og printer det
            avg_distance = sum(distanceReadings) / len(distanceReadings)
            print(f"\n-- Avrage distance ({len(distanceReadings)} samples): {avg_distance:.2f}m ---")

            # Hvis avstanden er under treshold-en sp printes det
            if avg_distance < DISTANCE_TRESHOLD:
                print(f"Rabbi phone detected within {DISTANCE_TRESHOLD}m!\nAvrage distance {avg_distance:.2f}m")

    # scanner etter bluetooth devices og runner cheakAV() funksjonen
    async with BleakScanner(detectionCallback):
        await cheakAV()

# hvis dette runnes som main så printer den at den starter prosjectet og hoved funksjonen kjøres
# I tillegg hvis CRTL + C trykkes printes det at prosjectet stopper og det vil stoppe
if __name__ == "__main__":
    try:
        print(f"Starting proximity monitor for device: {TARGET}")
        print("Press CTRL+C to stop...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitoring stopped!")
