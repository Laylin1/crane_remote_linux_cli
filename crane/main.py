import asyncio
import logging
import threading
import socket
import time
from paho.mqtt.client import Client, MQTTv311

from crane_bt import ZhiyunCraneBLE
from config import BROKER, PORT, CLIENT_ID, MQTT_TOPICS, CRANE_MAC, COMMAND_MAP


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)


class CommandManager:
    def __init__(self, timeout: float = 0.5):
        self.current_direction: str | None = None
        self.command_start_time: float = 0.0
        self.timeout = timeout
        self.loop: asyncio.AbstractEventLoop | None = None
    
    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
    
    def receive_command(self, direction: str):
        if direction not in COMMAND_MAP and direction != "stop":
            logger.warning(f"Unknown command: {direction}")
            return
        
        if direction == "stop":
            self.current_direction = None
        else:
            self.current_direction = direction
            self.command_start_time = self.loop.time() if self.loop else 0.0
            logger.info(f"Command started: {direction}")
    
    def get_active_command(self) -> str | None:
        if not self.current_direction:
            return None
        
        if self.loop and self.loop.time() - self.command_start_time > self.timeout:
            logger.info(f"Command timeout: {self.current_direction}")
            self.current_direction = None
            return None
        
        return self.current_direction


crane = ZhiyunCraneBLE(CRANE_MAC)
cmd_manager = CommandManager(timeout=0.5)
loop = asyncio.new_event_loop()
mqtt_client = Client(client_id=CLIENT_ID, protocol=MQTTv311)
mqtt_thread_handle: threading.Thread | None = None


def on_connect(client: Client, userdata, flags, rc):
    if rc == 0:
        logger.info("MQTT connected successfully")
        client.subscribe(MQTT_TOPICS)
    else:
        logger.error(f"MQTT connection failed with code {rc}")


def on_message(client: Client, userdata, msg):
    payload = msg.payload.decode().strip().lower()
    logger.info(f"MQTT command: {msg.topic} → {payload}")
    cmd_manager.receive_command(payload)


def on_disconnect(client: Client, userdata, rc):
    if rc != 0:
        logger.warning(f"MQTT disconnected with code {rc}")


def mqtt_thread_func():
    global mqtt_client
    mqtt_client = Client(client_id=CLIENT_ID, protocol=MQTTv311)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect

    while True:
        try:
            logger.info(f"Connecting to MQTT broker {BROKER}:{PORT}...")
            mqtt_client.connect(BROKER, PORT, keepalive=60)
            break
        except socket.gaierror:
            logger.warning("DNS not ready, retrying MQTT in 2s...")
        except Exception as e:
            logger.warning(f"MQTT connection failed: {e}, retrying in 2s...")
        
        time.sleep(2)

    logger.info("MQTT loop started")
    mqtt_client.loop_forever()


async def crane_loop():
    send_interval = 0.05
    
    while True:
        try:
            if not crane.is_connected():
                logger.debug("BLE not connected, skipping command send")
                await asyncio.sleep(send_interval)
                continue
            
            active_cmd = cmd_manager.get_active_command()
            if active_cmd:
                cmd_bytes = bytes(COMMAND_MAP[active_cmd])
                await crane.send_command(cmd_bytes)
                logger.debug(f"Command sent: {active_cmd}")
        
        except Exception as e:
            logger.error(f"Send error: {e}")
        
        await asyncio.sleep(send_interval)



async def main_async():
    cmd_manager.set_loop(loop)
    
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            await crane.connect()
            logger.info(" BLE connected successfully")
            retry_count = 0
            break
        except Exception as e:
            retry_count += 1
            logger.error(f" BLE connection failed (attempt {retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                await asyncio.sleep(5)
            else:
                logger.critical("Failed to connect to BLE after all retries")
                return
    
    try:
        logger.info("Starting main loop (MQTT and BLE commands)...")
        
        send_task = asyncio.create_task(crane_loop())
        monitor_task = crane.start_auto_reconnect()
        
        done, pending = await asyncio.wait(
            [send_task, monitor_task],
            return_when=asyncio.FIRST_EXCEPTION
        )
        
        for task in pending:
            task.cancel()
        
        for task in done:
            exc = task.exception()
            if exc:
                raise exc
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        await crane.stop_auto_reconnect()
        await crane.disconnect()


def shutdown_handler(signum=None, frame=None):
    logger.info("Shutdown signal received")
    if mqtt_client:
        try:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            logger.info("MQTT disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting MQTT: {e}")
    if loop and loop.is_running():
        loop.call_soon_threadsafe(loop.stop)


if __name__ == "__main__":
    import signal
    
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    mqtt_thread_handle = threading.Thread(target=mqtt_thread_func, daemon=False)
    mqtt_thread_handle.start()
    
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main_async())
    except KeyboardInterrupt:
        shutdown_handler()
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
    finally:
        loop.close()
