import logging
import asyncio
from bleak import BleakClient, BleakError
from config import CRANE_SERVICE_UUID, CRANE_WRITE_CHAR_UUID

logger = logging.getLogger(__name__)

class ZhiyunCraneBLE:
    def __init__(self, mac: str, auto_reconnect: bool = True):
        self.mac = mac
        self.client: BleakClient | None = None
        self.write_char = None
        self.auto_reconnect = auto_reconnect
        self._monitor_task: asyncio.Task | None = None

    async def connect(self):
        if self.client and self.client.is_connected:
            logger.info("Already connected")
            return

        logger.info(f"Connecting to {self.mac}...")
        self.client = BleakClient(self.mac, timeout=30.0)

        try:
            await self.client.connect()
            logger.info(f"Connected to device {self.mac}")

            if not self.client.services:
                raise BleakError("Service doesn't find after connection")

            service = self.client.services.get_service(CRANE_SERVICE_UUID)
            if not service:
                available = [str(s.uuid) for s in self.client.services]
                logger.error(f"Available services: {available}")
                raise BleakError(f"Service {CRANE_SERVICE_UUID} doesn't find. Availaible: {available}")

            self.write_char = self.client.services.get_characteristic(CRANE_WRITE_CHAR_UUID)
            if not self.write_char:
                raise BleakError(f"Parametr {CRANE_WRITE_CHAR_UUID} doesn't find")

            logger.info("Successfull connected to Zhiyun Crane V2")
        except FileNotFoundError as e:
            logger.error(f"BLE device not found: {self.mac} - {e}")
            if self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
            self.client = None
            raise
        except BleakError as e:
            logger.error(f"BLE error: {e}")
            if self.client and self.client.is_connected:
                await self.client.disconnect()
            self.client = None
            raise
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

    def is_connected(self) -> bool:
        return self.client is not None and self.client.is_connected

    async def _auto_reconnect_monitor(self):
        check_interval = 5
        max_retries = 3
        
        logger.info("BLE auto-reconnect monitor started")
        
        while True:
            try:
                if not self.is_connected():
                    logger.warning("BLE connection lost, attempting to reconnect...")
                    retry_count = 0
                    
                    while retry_count < max_retries and not self.is_connected():
                        try:
                            await self.connect()
                            logger.info(" BLE reconnected successfully")
                            break
                        except Exception as e:
                            retry_count += 1
                            logger.error(f" Reconnect attempt {retry_count}/{max_retries} failed: {e}")
                            if retry_count < max_retries:
                                await asyncio.sleep(2)
                    
                    if not self.is_connected():
                        logger.error("Failed to reconnect to BLE, will retry in next cycle")
                
                await asyncio.sleep(check_interval)
            
            except asyncio.CancelledError:
                logger.info("BLE auto-reconnect monitor stopped")
                break
            except Exception as e:
                logger.error(f"BLE monitor error: {e}")
                await asyncio.sleep(check_interval)

    def start_auto_reconnect(self) -> asyncio.Task:
        if self._monitor_task and not self._monitor_task.done():
            logger.warning("Auto-reconnect monitor already running")
            return self._monitor_task
        
        self._monitor_task = asyncio.create_task(self._auto_reconnect_monitor())
        return self._monitor_task

    async def stop_auto_reconnect(self):
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def send_command(self, data: bytes):
        if not self.is_connected():
            await self.connect()
        
        if not self.write_char:
            raise RuntimeError("Characteristic not found — can't send command")

        try:
            await self.client.write_gatt_char(self.write_char, data)
            logger.info(f"Command sent: {data.hex()}")
        except Exception as e:
            logger.error(f"Send failed: {e}")
            await self.disconnect()
            raise
