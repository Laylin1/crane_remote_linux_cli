import logging
from bleak import BleakClient, BleakError
from config import CRANE_SERVICE_UUID, CRANE_WRITE_CHAR_UUID

logger = logging.getLogger(__name__)

class ZhiyunCraneBLE:
    def __init__(self, mac: str):
        self.mac = mac
        self.client: BleakClient | None = None
        self.write_char = None

    async def connect(self):
        if self.client and self.client.is_connected:
            logger.info("Already connected")
            return

        logger.info(f"Connecting to {self.mac}...")
        self.client = BleakClient(self.mac)

        try:
            await self.client.connect(timeout=30.0)

            if not self.client.services:
                raise BleakError("Service doesn't find after connection")

            service = self.client.services.get_service(CRANE_SERVICE_UUID)
            if not service:
                available = [str(s.uuid) for s in self.client.services]
                raise BleakError(f"Service {CRANE_SERVICE_UUID} doesn't find. Availaible: {available}")

            self.write_char = self.client.services.get_characteristic(CRANE_WRITE_CHAR_UUID)
            if not self.write_char:
                raise BleakError(f"Parametr {CRANE_WRITE_CHAR_UUID} doesn't find")

            logger.info("Successfull connected to Zhiyun Crane V2")
        except Exception as e:
            logger.error(f"Connection error: {e}")
            if self.client and self.client.is_connected:
                await self.client.disconnect()
            self.client = None
            raise

    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            logger.info("Disconnected from stabilizer")
        self.client = None
        self.write_char = None

    async def send_command(self, data: bytes):
        if not self.client or not self.client.is_connected:
            await self.connect()
        if not self.write_char:
            raise RuntimeError("Parametr doesn't find — can't connect")

        try:
            await self.client.write_gatt_char(self.write_char, data)
            logger.debug(f"Sent: {data.hex()}")
        except Exception as e:
            logger.error(f"Sending error: {e}")
            await self.disconnect()
            raise
