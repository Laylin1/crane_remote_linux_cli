import asyncio
import signal
from src.core.command_manager import CommandManager
from src.inputs.mqtt_adapter import MQTTAdapter
from src.devices.zhiyun_crane_ble import ZhiyunCraneBLE
from utils.logger import setup_logger
from src.config.settings import (
    BROKER,
    PORT,
    MQTT_TOPICS,
    COMMAND_MAP,
    CRANE_SERVICE_UUID,
    CRANE_WRITE_CHAR_UUID,
    MAC_ADDRESS as DEVICE_ADDRESS,
)

logger = setup_logger("main")


async def main():
    # 1. Драйвер BLE
    crane = ZhiyunCraneBLE(device_address=DEVICE_ADDRESS)

    # 2. Подключение к устройству
    try:
        await crane.connect()
        logger.info("BLE подключение установлено")
    except Exception as e:
        logger.error(f"Не удалось подключиться к BLE: {e}")
        return

    # 3. Менеджер команд
    manager = CommandManager(
        device_interface=crane,
        timeout=0.5
    )

    # 4. MQTT-адаптер
    mqtt_input = MQTTAdapter(
        broker=BROKER,
        port=PORT,
        topics=MQTT_TOPICS,
        command_handler=manager.receive_command
    )

    try:
        await mqtt_input.start()
        logger.info("MQTT адаптер запущен, слушаем команды...")

        loop = asyncio.get_running_loop()

        while True:
            active = manager.get_active_command()
            if active and active in COMMAND_MAP:
                data = COMMAND_MAP[active]
                try:
                    await crane.send_command(data)
                    logger.debug(f"Отправлено: {active} → {data.hex()}")
                except Exception as e:
                    logger.error(f"Ошибка отправки {active}: {e}")

            await asyncio.sleep(0.12)

    except asyncio.CancelledError:
        logger.info("Задачи отменены (Ctrl+C или внешняя остановка)")
    except KeyboardInterrupt:
        logger.info("Остановка по Ctrl+C")
    except Exception as e:
        logger.critical(f"Критическая ошибка в главном цикле: {e}", exc_info=True)
    finally:
        logger.info("Завершение программы...")
        await mqtt_input.stop()
        await crane.disconnect()
        logger.info("Программа завершена")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановка по Ctrl+C")
    except Exception as e:
        print(f"Неожиданная ошибка при запуске: {e}")