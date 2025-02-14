import asyncio
from bleak import BleakScanner

async def main():
    devices = await BleakScanner.discover(timeout=5)
    for d in devices:
        print(f"Device: {d.name} - Mac: ({d.address}) - RSSI: ({d.rssi})")

asyncio.run(main())