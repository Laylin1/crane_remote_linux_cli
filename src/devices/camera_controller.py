import subprocess
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


from src.config.settings import PREVIEW_ENABLED

class CameraController:
    def __init__(self):
        self.recording = False
        self.video_writer = None
        self.current_frame = None
        self.lock = threading.Lock()  # чтобы безопасно брать фрейм в разных потоках
        self.running = True
        # preview/window management
        self.show_window = False
        self.window_created = False
        self.preview_allowed = PREVIEW_ENABLED

    def enable_preview(self):
        """Start showing the camera window. Safe to call multiple times.

        If PREVIEW_ENABLED is False the call has no effect; this allows running
        completely headless even when the HTTP stream endpoint is used.
        """
        if not self.preview_allowed:
            logger.debug("Preview not allowed by configuration, ignoring enable")
            return
        self.show_window = True

    def disable_preview(self):
        """Stop showing the camera window and destroy it if created."""
        self.show_window = False
        if self.window_created:
            cv2.destroyWindow("Camera")
            self.window_created = False
        
    def camera_number_detection(self):
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_V4L2)

            if cap.isOpened():
                result = subprocess.run(
                    ["v4l2-ctl", "--device", f"/dev/video{i}", "--info"],
                    capture_output=True,
                    text=True
                )

                if "ZED" in result.stdout:
                    logger.info(f"ZED found at index {i}")
                    cap.release()
                    return i

            cap.release()

        logger.warning("ZED not found, using default 0")
        return 0


    def open_camera(self):
        
        index = self.camera_number_detection()

        self.cap = cv2.VideoCapture(index, cv2.CAP_V4L2)

        # Настройки применять ПОСЛЕ открытия
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        if not self.cap.isOpened():
            raise RuntimeError(f"Camera {index} not found")

        # do not create a window until preview is requested
        # window sizing will be handled when we first show

        while self.running:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.current_frame = frame.copy()

                # display only when requested and allowed
                if self.show_window and self.preview_allowed:
                    if not self.window_created:
                        cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
                        cv2.resizeWindow("Camera", 1280, 720)
                        self.window_created = True

                    cv2.imshow("Camera", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        # user closed preview manually
                        self.disable_preview()

                if self.recording and self.video_writer:
                    self.video_writer.write(frame)

        # cleanup when loop exits
        self.cap.release()
        if self.window_created:
            cv2.destroyAllWindows()

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

        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        filename = f"media/video/recording_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.avi"
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
