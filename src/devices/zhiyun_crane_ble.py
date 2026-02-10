import asyncio
from bleak import BleakClient, BleakError, BleakGATTCharacteristic
from typing import Optional

from src.interfaces.device import DeviceInterface
from utils.logger import setup_logger
from src.config.settings import (
    CRANE_SERVICE_UUID,
    CRANE_WRITE_CHAR_UUID,          
)

logger = setup_logger("zhiyun_crane_ble")


class ZhiyunCraneBLE(DeviceInterface):
    def __init__(self, device_address: str, command_handler=None):
        super().__init__(command_handler)  
        self.device_address = device_address
        self.client: Optional[BleakClient] = None
        self.write_char: Optional[BleakGATTCharacteristic] = None
        self.notify_char: Optional[BleakGATTCharacteristic] = None
        self.running = False
        self._lock = asyncio.Lock()        
        self._reconnect_task: Optional[asyncio.Task] = None

    @property
    def is_connected(self) -> bool:
        return self.client is not None and self.client.is_connected

    async def connect(self) -> None:
        """Подключается к устройству и находит нужные характеристики"""
        if self.is_connected:
            logger.info("Already connected")
            return

        async with self._lock:
            logger.info(f"Connecting to Zhiyun Crane at {self.device_address}...")
            self.client = BleakClient(self.device_address, timeout=15.0)

            try:
                await self.client.connect()
                logger.info("BLE connection established")

                # Получаем сервисы
                services = self.client.services
                crane_service = services.get_service(CRANE_SERVICE_UUID)
                if not crane_service:
                    available = [str(s.uuid) for s in services]
                    logger.error(f"Service {CRANE_SERVICE_UUID} not found. Available: {available}")
                    raise BleakError("Required service not found")

                # Находим характеристику для записи команд
                self.write_char = crane_service.get_characteristic(CRANE_WRITE_CHAR_UUID)
                if not self.write_char:
                    raise BleakError(f"Write characteristic {CRANE_WRITE_CHAR_UUID} not found")

                self.running = True
                logger.info("Zhiyun Crane BLE initialized successfully")

            except Exception as e:
                logger.error(f"Connection failed: {e}", exc_info=True)
                await self.disconnect()
                raise

    async def disconnect(self) -> None:
        if self.client and self.client.is_connected:
            if self.notify_char:
                try:
                    await self.client.stop_notify(self.notify_char)
                except:
                    pass
            await self.client.disconnect()
            logger.info(f"Disconnected from {self.device_address}")
        self.client = None
        self.write_char = None
        self.notify_char = None
        self.running = False

    async def send_command(self, command: bytes) -> None:
        """Отправляет байтовую команду на гимбал"""
        if not self.is_connected:
            await self.connect()

        if not self.write_char:
            raise RuntimeError("Write characteristic not initialized")

        try:
            
            await self.client.write_gatt_char(self.write_char, command, response=False)
            logger.debug(f"Sent BLE command: {command.hex()}")
        except BleakError as e:
            logger.warning(f"Write failed: {e}. Attempting reconnect...")
            await self.ble_reconnect()
           
            await self.client.write_gatt_char(self.write_char, command, response=False)
            logger.info("Command resent after reconnect")
        except Exception as e:
            logger.error(f"Unexpected error sending command: {e}")
            raise

    async def ble_reconnect(self) -> None:
        """Пытается переподключиться при потере связи"""
        logger.info("Starting BLE reconnect sequence...")
        await self.disconnect()

        for attempt in range(1, 4):  # 3 попытки
            try:
                logger.info(f"Reconnect attempt {attempt}/3")
                await asyncio.sleep(1.5)  # небольшая задержка
                await self.connect()
                logger.info("Reconnect successful")
                return
            except Exception as e:
                logger.warning(f"Reconnect attempt {attempt} failed: {e}")
                await asyncio.sleep(2 ** attempt)  # backoff: 2s, 4s, 8s...

        logger.error("All reconnect attempts failed")
        raise ConnectionError("Failed to reconnect to Zhiyun Crane")

    def _notification_handler(self, sender: BleakGATTCharacteristic, data: bytearray):
        """Обработчик входящих уведомлений от гимбала (положение, ошибки и т.д.)"""
        logger.debug(f"Notification from {sender.uuid}: {data.hex()}")
        


    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()