import time
import asyncio
import logging
import threading
import paho.mqtt.client as mqtt

from crane_bt import ZhiyunCraneBLE
from config import BROKER, PORT, CLIENT_ID, MQTT_TOPICS, CRANE_MAC, COMMAND_MAP


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)


crane = ZhiyunCraneBLE(CRANE_MAC)
loop = asyncio.new_event_loop()  
current_direction: str | None = None  # текущее направление движения
last_command_time: float = 0.0
COMMAND_TIMEOUT = 0.2


def on_connect(client, userdata, flags, rc):
    logger.info(f"MQTT connected (rc={rc})")
    client.subscribe(MQTT_TOPICS)

def on_message(client, userdata, msg):
    global current_direction, last_command_time
    payload = msg.payload.decode().strip().lower()
    logger.info(f"Command received: {msg.topic} → {payload}")

    if payload in COMMAND_MAP:
        current_direction = payload  # start moving
        last_command_time = time.time() # timer updating
    elif payload == "stop":
        current_direction = None


def mqtt_thread():
    client = mqtt.Client(client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_forever()


async def crane_loop():
    global current_direction
    while True:
        if current_direction:
            if time.time() - last_command_time > COMMAND_TIMEOUT:
                current_direction = None
            else:
                cmd_bytes = bytes(COMMAND_MAP[current_direction])
            try:
                await crane.send_command(cmd_bytes)
            except Exception as e:
                logger.error(f"Sent error: {e}")
                
    await asyncio.sleep(0.05)


async def main_async():
    try:
        await crane.connect()
        logger.info("MQTT-subscribe active through sepparate thread. Waiting...")

        
        loop_task = asyncio.create_task(crane_loop())

        await loop_task 
    except Exception as e:
        logger.error(f"Error in main_async: {e}")
    finally:
        await crane.disconnect()


if __name__ == "__main__":
    
    mqtt_t = threading.Thread(target=mqtt_thread, daemon=True)
    mqtt_t.start()

    
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main_async())
    except KeyboardInterrupt:
        logger.info("Stopping...")
        loop.run_until_complete(crane.disconnect())
    finally:
        loop.close()
