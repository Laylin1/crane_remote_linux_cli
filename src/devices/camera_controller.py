import cv2
import threading
from datetime import datetime
import os
from utils.logger import setup_logger
from src.config.settings import CAMERA_COMMANDS

logger = setup_logger("camera_controller")

os.makedirs("media/photo", exist_ok=True)
os.makedirs("media/video", exist_ok=True)

camera_number = 0  # по умолчанию, можно изменить на другой индекс камеры при необходимости


class CameraController:
    def __init__(self):
        self.recording = False
        self.video_writer = None
        self.current_frame = None
        self.lock = threading.Lock()  # чтобы безопасно брать фрейм в разных потоках
        self.running = True
        
    def camera_number_detection(camera_number):
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                logger.info(f"Camera found at index {i}")
                camera_number = i
                return camera_number
                cap.release()
                return i
        logger.warning("No camera found, defaulting to index 0")
        return 0

    def open_camera(self):
        self.cap = cv2.VideoCapture(camera_number)
        if not self.cap.isOpened():
            raise RuntimeError(f"Camera {camera_number} not found")
        
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.current_frame = frame.copy()
                cv2.imshow('Camera', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False
                break

        self.cap.release()
        cv2.destroyAllWindows()


    def handle_command(self, command: str):
        if command not in CAMERA_COMMANDS:
            logger.warning(f"Unknown camera command: {command}")
            return

        if command == 'photo':
            self.take_photo()
        elif command == 'record':
            self.start_recording()
        elif command == 'stop_record':
            self.stop_recording()

    def take_photo(self):
        with self.lock:
            if self.current_frame is None:
                logger.warning("No frame available for photo")
                return
            frame = self.current_frame.copy()

        filename = f"media/photo/photo_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
        cv2.imwrite(filename, frame)
        logger.info(f"Photo saved as {filename}")

    def start_recording(self):
        if self.recording:
            logger.info("Already recording")
            return

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        filename = f"media/video/recording_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4"
        self.video_writer = cv2.VideoWriter(filename, fourcc, 20.0,
                                            (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                             int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))
        self.recording = True
        logger.info(f"Started recording to {filename}")

    def stop_recording(self):
        if not self.recording:
            logger.info("Not currently recording")
            return

        self.video_writer.release()
        self.video_writer = None
        self.recording = False
        logger.info("Stopped recording")

    def update(self):
        """Вызывать регулярно для записи видео"""
        if self.recording and self.current_frame is not None:
            with self.lock:
                self.video_writer.write(self.current_frame)
