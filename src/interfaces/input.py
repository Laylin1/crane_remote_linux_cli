from abc import ABC, abstractmethod
import asyncio
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger("CommandInputInterface")

class CommandInputInterface(ABC):
    def __init__(self, command_handler):
        self.command_handler = command_handler
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
    def set_command_handler(self, command_handler):
        self.command_handler = command_handler
        
    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError("start method must be implemented by subclasses")
    
    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError("stop method must be implemented by subclasses")
    
    async def _emit_command(self, direction: str) -> None:
        if self.command_handler is None:
            self.logger.warning("No command handler set, cannot emit command")  
            return
        
        try:
            if asyncio.iscoroutinefunction(self.command_handler):
                await self.command_handler(direction)
            else:
                self.command_handler(direction)
        except Exception as e:
            print(f"Error emitting command: {e}")
    
    @property
    def is_running(self) -> bool:
        return self.running
    
    async def run_forever(self) -> None:
        await self.start()
        try:
            await asyncio.Event().wait()  # Keep running until stopped
        except asyncio.CancelledError:
            await self.stop()