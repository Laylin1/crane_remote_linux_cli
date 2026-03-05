import os

BROKER = os.getenv("BROKER", "0.0.0.0")
PORT = int(os.getenv("PORT", 1883))

MQTT_TOPICS = [
    ("crane/control", 0),
    ("crane/camera", 0),
]

MAC_ADDRESS = os.getenv("CRANE_MAC", "80:EA:CA:00:D5:8B")

CRANE_SERVICE_UUID = "0000fee9-0000-1000-8000-00805f9b34fb"
CRANE_WRITE_CHAR_UUID = "d44bc439-abfd-45a2-b575-925416129600"

COMMAND_MAP = {
    'up':    bytes([0x06, 0x10, 0x01, 0x0e, 0x89, 0xc2, 0xbc, 0x06, 0x10, 0x02, 0x08, 0x00, 0x31, 0xeb]),
    'down':  bytes([0x06, 0x10, 0x03, 0x08, 0x00, 0x06, 0xdb, 0x06, 0x10, 0x01, 0x01, 0x76, 0xcc, 0x72]),
    'left':  bytes([0x06, 0x10, 0x02, 0x08, 0x00, 0x31, 0xeb, 0x06, 0x10, 0x03, 0x01, 0x76, 0xa2, 0x12]),
    'right': bytes([0x06, 0x10, 0x02, 0x08, 0x00, 0x31, 0xeb, 0x06, 0x10, 0x03, 0x0d, 0xd9, 0xa3, 0x7a]),
}

CAMERA_COMMANDS = {
    'photo': 'photo',
    'record': 'record',
    'stop_record': 'stop_record',
}
    
# feature flag to disable camera initialization/startup; set to "false" in environment
CAMERA_ENABLED = os.getenv("CAMERA_ENABLED", "true").lower() in ("1", "true", "yes")

# whether the OpenCV preview window may ever be shown; turn off to run truly headless
# Accepts 1/true/yes to enable; anything else disables.
# default is **False** so setting the variable is required to show the window.
PREVIEW_ENABLED = os.getenv("PREVIEW_ENABLED", "false").lower() in ("1", "true", "yes")
