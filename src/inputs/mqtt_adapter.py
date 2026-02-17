import asyncio
from paho.mqtt import client as mqtt_client
from typing import List, Tuple

from src.interfaces.input import CommandInputInterface  
from src.config.settings import BROKER, PORT, MQTT_TOPICS, COMMAND_MAP, CAMERA_COMMANDS
from utils.logger import setup_logger

logger = setup_logger("mqtt_adapter")


class MQTTAdapter(CommandInputInterface):
    def __init__(
        self,
        broker: str = BROKER,
        port: int = PORT,
        topics: List[Tuple[str, int]] = MQTT_TOPICS,
        command_handler=None,
        camera_command_handler=None
    ):
        super().__init__(command_handler)
        self.camera_command_handler = camera_command_handler
        self.broker = broker
        self.port = port
        self.topics = topics
        self.client = mqtt_client.Client(
            client_id="crane_controller_mqtt",
            clean_session=True,
        )
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.enable_logger(logger)

        
        self._loop = asyncio.get_running_loop()  

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT broker")
            for topic, qos in self.topics:
                client.subscribe(topic, qos=qos)
                logger.info(f"Subscribed to {topic} (QoS {qos})")
        else:
            logger.error(f"Connection failed, code = {rc}")

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning(f"Disconnected unexpectedly (rc={rc})")

    def on_message(self, client, userdata, msg):
        try:
            command = msg.payload.decode("utf-8").strip().lower()
            logger.info(f"Получено MQTT: {command!r} на топике {msg.topic}")

            if command in COMMAND_MAP or command == "stop":
                asyncio.run_coroutine_threadsafe(
                    self._emit_command(command),
                    self._loop
                )
            elif command in CAMERA_COMMANDS:
                if self.camera_command_handler:
                    self.camera_command_handler(command)
                else:
                    logger.warning("Camera command handler not set")
            else:
                logger.warning(f"Неизвестная команда: {command!r}")

        except UnicodeDecodeError:
            logger.error(f"Невалидный UTF-8: {msg.payload!r}")
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}", exc_info=True)
        

    async def start(self) -> None:
        if self.running:
            logger.warning("MQTT adapter already running")
            return

        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()  
            self.running = True
            logger.info("MQTT adapter started")
        except Exception as e:
            logger.error(f"Failed to start MQTT: {e}")
            self.running = False
            raise

    async def stop(self) -> None:
        if not self.running:
            return

        logger.info("Stopping MQTT adapter...")
        self.client.loop_stop()
        self.client.disconnect()
        self.running = False
        logger.info("MQTT adapter stopped")

    
    async def ensure_connected(self):
        if not self.running:
            await self.start()