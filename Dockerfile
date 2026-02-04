FROM python:3.10-slim

# Устанавливаем зависимости для BLE и Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    bluetooth \
    bluez \
    libbluetooth-dev \
    dbus \
    gcc \
    python3-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем требования и устанавливаем Python пакеты
COPY crane/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY crane/ .

# Даем права на доступ к Bluetooth (для root в privileged контейнере)
RUN usermod -a -G bluetooth root

# Запуск приложения
CMD ["python", "main.py"]
