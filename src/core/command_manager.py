import asyncio
import time
from utils.logger import setup_logger
from src.config.settings import COMMAND_MAP
from src.config.settings import CAMERA_COMMANDS

logger = setup_logger("command_manager")


class CommandManager:
    def __init__(self, timeout: float = 0.5, crane=None, camera=None):
        self.crane = crane
        self.camera = camera
        self.timeout = timeout
        self.current_direction: str | None = None
        self.command_start_time: float = 0.0
        self.loop: asyncio.AbstractEventLoop | None = None
        self.is_hold_mode = False
        
    def receive_command_camera(self, command: str):
        if self.camera is None:
            logger.warning("Camera not available, ignoring camera command")
            return

        if command in CAMERA_COMMANDS:
            self.camera.handle_command(command)
        else:
            logger.warning(f"Unknown camera command: {command}")

        logger.info(f"Received camera command: {command}")
        
    def receive_command(self, direction: str):
        if direction not in COMMAND_MAP and direction != "stop":
            logger.warning(f"Unknown command received: {direction}")
            return
        
        if direction == "stop":
            self.current_direction = None
        else:
            self.current_direction = direction
            self.command_start_time = self.loop.time() if self.loop else 0.0
            logger.info(f"Received command: {direction}")
    
        
    def get_active_command(self) -> list[str]:
        if self.current_direction:
            return self.current_direction
        
        if self.loop and self.loop.time() - self.command_start_time > self.timeout:
            logger.info(f"Command timeout reached for {self.current_direction}")
            return None
        
        return self.current_direction
    
    def is_active(self) -> bool:
        return self.get_active_command() is not None