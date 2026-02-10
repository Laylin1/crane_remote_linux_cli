from utils.logger import setup_logger
import asyncio 
from bleak import BleakClient, BleakError
from src.config.settings import CRANE_SERVICE_UUID, CRANE_WRITE_CHAR_UUID

logger = setup_logger("zhiyun_crane")

class DeviceInterface:
    def __init__(self, address: str):
        self.address = address
        self._connection = None
        self.client: BleakClient | None = None
        self.write_char = None
        self._lock = asyncio.Lock()
        
        
        
    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected
    
    
    
    async def connect(self):
        if self.is_connected:
            logger.info("Already connected")
            return

        async with self._lock:
            logger.info(f"Connecting to {self.address}...")
            self._client = BleakClient(self.address, timeout=20.0)

            try:
                
                async with self._client:   
                    logger.info(f"Connected to {self.address}")

                    service = self._client.services.get_service(CRANE_SERVICE_UUID)
                    if not service:
                        services_list = [str(s.uuid) for s in self._client.services]
                        logger.error(f"CRANE_SERVICE_UUID not found. Available: {services_list}")
                        raise BleakError(f"Service {CRANE_SERVICE_UUID} not found")

                    self._write_char = self._client.services.get_characteristic(CRANE_WRITE_CHAR_UUID)
                    if not self._write_char:
                        raise BleakError(f"Write char {CRANE_WRITE_CHAR_UUID} not found")

                    logger.info("Successfully initialized Zhiyun Crane interface")
                    

            except Exception as e:
                logger.error(f"Connection failed: {e}", exc_info=True)
                self._client = None
                self._write_char = None
                raise
        
    
    async def disconnect(self):
        if self.client and self.client.is_conected:
            await self.client.disconnect()
            logger.info(f"Disconnected from device {self.mac}")
        self.client = None
        self.write_char = None
        
    async def ensure_connected(self):
        if not self.is_connected:
            await self.connect()
    
    
    
    async def send_command(self, data: bytes): 
        await self.ensure_connected()
            
        try:
            await self.client.write_gatt_char(self.write_char, data)
            logger.debug(f"Sent command: {data.hex()}")
        except BleakError as e:
            logger.error(f"BLE write failed: {e}")
            await self.disconnect()
            await self.connect()
            await self.client.write_gatt_char(self.write_char, data)
            logger.info(f"Sent command after reconnect: {data.hex()}")
        except Exception as e:    
            logger.error(f"Unexpected error during send_command: {e}", exc_info=True)
            raise