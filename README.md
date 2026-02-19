## Crane 2S BLE Remte controller
The project is a client-server application for remote control of the Zhiyun Crane 2S via BLE, using MQTT as the transport layer.
The architecture is designed to allow for the optional data transfer protocol.

## Architecture

- Client
- Broker
- MQTT Adapter
- Crane 2S Device

## Project Structue 
```bash

.
├── docks
│   └── Architecture.drawio
│
├── media
│   ├── photo
│   └── video
│
├── README.md
├── requirements.txt
├── src
│   ├── config
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── core
│   │   └── command_manager.py
│   │
│   ├── devices
│   │   ├── camera_controller.py
│   │   └── zhiyun_crane_ble.py
│   │
│   ├── inputs
│   │   └── mqtt_adapter.py
│   │
│   ├── interfaces
│   │   ├── device.py
│   │   └── input.py
│   │
│   └── main.py
│   
├── utils
│   └── logger.py
│   
└── venv

```

## Installation

### Requirements
- Python 3.11+
- MQTT Broker(Mosquitto)
- Linux with BLE support

### Setup

```bash
- git clone https://github.com/Laylin1/crane_remote_linux_cli.git
- pip install -r requirements.txt
```

## Start

```bash
- mosquitto -v
- python3 -m src.main # In another terminal)
```
## Example execution

```bash
mosquitto_pub -h 127.0.0.1 -t crane/control -m up
mosquitto_pub -h 127.0.0.1 -t crane/control -m down
mosquitto_pub -h 127.0.0.1 -t crane/control -m left
mosquitto_pub -h 127.0.0.1 -t crane/control -m right
mosquitto_pub -h 127.0.0.1 -t crane/control -m stop

# Camera commands
mosquitto_pub -h 127.0.0.1 -t crane/camera -m photo
mosquitto_pub -h 127.0.0.1 -t crane/camera -m record
mosquitto_pub -h 127.0.0.1 -t crane/camera -m stop_record

```

## Roadmap
- work via USB protocol
- adding a third axis