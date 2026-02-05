FROM python:3.10-slim


RUN apt-get update && apt-get install -y --no-install-recommends \
    bluetooth \
    bluez \
    libbluetooth-dev \
    dbus \
    gcc \
    python3-dev \
    ca-certificates \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app


COPY crane/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY crane/ .

COPY wait-for-mosquitto.sh /app/wait-for-mosquitto.sh
ENTRYPOINT ["/app/wait-for-mosquitto.sh", "mosquitto", "1883", "python", "main.py"]



# Права на доступ к Bluetooth (для root в privileged контейнере)
RUN usermod -a -G bluetooth root


CMD ["python", "main.py"]
