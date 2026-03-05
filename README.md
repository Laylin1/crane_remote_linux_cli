## Crane 2S BLE Remote controller
The project is a client-server application for remote control of the Zhiyun Crane 2S via BLE, using MQTT as the transport layer.
The architecture supports both MQTT for gimbal control and HTTP for camera streaming.

## Architecture

- Client (MQTT/HTTP)
- MQTT Broker (gimbal control)
- HTTP Server (camera streaming)
- Crane 2S Device (BLE)
- Camera Controller (ZED camera)

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

Before running make sure your MQTT broker (e.g. mosquitto) is up:

```bash
mosquitto -v
```

Then launch the controller:

```bash
python3 -m src.main
```

By default the program initialises the camera capture thread and will open a
preview window when a client connects to the HTTP stream.  If you would rather
run completely headless (no GUI at all) set the environment variable
`PREVIEW_ENABLED=false` or omit it entirely; the HTTP MJPEG stream will still
work without the window.

You can also disable the camera hardware completely with
`CAMERA_ENABLED=false` (useful when testing without a device).
## Example execution

**Gimbal commands via MQTT**

```bash
mosquitto_pub -h 127.0.0.1 -t crane/control -m up
mosquitto_pub -h 127.0.0.1 -t crane/control -m down
mosquitto_pub -h 127.0.0.1 -t crane/control -m left
mosquitto_pub -h 127.0.0.1 -t crane/control -m right
mosquitto_pub -h 127.0.0.1 -t crane/control -m stop
```

**Camera control via MQTT**

```bash
mosquitto_pub -h 127.0.0.1 -t crane/camera -m photo
mosquitto_pub -h 127.0.0.1 -t crane/camera -m record
mosquitto_pub -h 127.0.0.1 -t crane/camera -m stop_record
```

**HTTP endpoints for live view and snapshots**

Once the server is running you can access the camera over HTTP on port 8000:

* `GET /health` ‑‑ basic health check
* `GET /api/camera/photo` ‑‑ current JPEG frame
* `GET /api/camera/stream` ‑‑ MJPEG live stream
* `POST /api/camera/capture` ‑‑ take photo
* `POST /api/camera/record/start` and `/stop` ‑‑ control recording
* `GET /api/camera/status` ‑‑ camera status

Refer to `HTTP_API.md` for detailed usage examples.

## Roadmap
- work via USB protocol
- adding a third axis