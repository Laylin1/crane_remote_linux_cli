import asyncio
import threading
import cv2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from utils.logger import setup_logger

logger = setup_logger("http_adapter")


class HTTPAdapter:
    def __init__(self, host: str = "0.0.0.0", port: int = 8000, camera=None):
        self.host = host
        self.port = port
        self.camera = camera
        self.app = self._create_app()
        self.running = False


    def _create_app(self) -> FastAPI:
        app = FastAPI(title="Crane 2S Controller")

        # Enable CORS
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/health")
        async def health():
            """Health check endpoint"""
            return {"status": "ok", "service": "crane-controller"}

        @app.get("/api/camera/photo")
        async def get_photo():
            """Get current frame as JPEG"""
            if self.camera is None or self.camera.current_frame is None:
                return JSONResponse(
                    {"error": "Camera not available"},
                    status_code=503
                )

            with self.camera.lock:
                frame = self.camera.current_frame.copy()

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                return JSONResponse(
                    {"error": "Failed to encode frame"},
                    status_code=500
                )

            frame_bytes = buffer.tobytes()
            return StreamingResponse(
                iter([frame_bytes]),
                media_type="image/jpeg"
            )

        @app.get("/api/camera/stream")
        async def stream_video():
            """Stream live video as MJPEG; only show preview window while client is connected."""
            if self.camera is None:
                return JSONResponse(
                    {"error": "Camera not available"},
                    status_code=503
                )

            # enable window preview on demand (may be a no-op if it's disabled in settings)
            if hasattr(self.camera, 'enable_preview'):
                try:
                    self.camera.enable_preview()
                except Exception:
                    logger.exception("Failed to enable camera preview")

            async def generate_mjpeg():
                try:
                    while self.running:
                        if self.camera.current_frame is None:
                            await asyncio.sleep(0.01)
                            continue

                        with self.camera.lock:
                            frame = self.camera.current_frame.copy()

                        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        if not ret:
                            await asyncio.sleep(0.01)
                            continue

                        frame_bytes = buffer.tobytes()
                        yield (
                            b'--boundary\r\n'
                            b'Content-Type: image/jpeg\r\n'
                            b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                            + frame_bytes + b'\r\n'
                        )
                        await asyncio.sleep(0.033)  # ~30 FPS
                finally:
                    # turn off preview when the response completes/connection closes
                    try:
                        self.camera.disable_preview()
                    except Exception:
                        logger.exception("Failed to disable camera preview")

            return StreamingResponse(
                generate_mjpeg(),
                media_type="multipart/x-mixed-replace; boundary=boundary"
            )

        @app.post("/api/camera/capture")
        async def capture_photo():
            """Take a photo"""
            if self.camera is None:
                return JSONResponse(
                    {"error": "Camera not available"},
                    status_code=503
                )

            try:
                self.camera.take_photo()
                return {"status": "success", "message": "Photo captured"}
            except Exception as e:
                logger.error(f"Error taking photo: {e}")
                return JSONResponse(
                    {"error": str(e)},
                    status_code=500
                )

        @app.post("/api/camera/record/start")
        async def start_recording():
            """Start recording"""
            if self.camera is None:
                return JSONResponse(
                    {"error": "Camera not available"},
                    status_code=503
                )

            try:
                self.camera.start_recording()
                return {"status": "success", "message": "Recording started"}
            except Exception as e:
                logger.error(f"Error starting recording: {e}")
                return JSONResponse(
                    {"error": str(e)},
                    status_code=500
                )

        @app.post("/api/camera/record/stop")
        async def stop_recording():
            """Stop recording"""
            if self.camera is None:
                return JSONResponse(
                    {"error": "Camera not available"},
                    status_code=503
                )

            try:
                self.camera.stop_recording()
                return {"status": "success", "message": "Recording stopped"}
            except Exception as e:
                logger.error(f"Error stopping recording: {e}")
                return JSONResponse(
                    {"error": str(e)},
                    status_code=500
                )

        @app.get("/api/camera/status")
        async def camera_status():
            """Get camera status"""
            if self.camera is None:
                return JSONResponse(
                    {"error": "Camera not available"},
                    status_code=503
                )

            return {
                "status": "ok",
                "recording": self.camera.recording,
                "frame_available": self.camera.current_frame is not None
            }

        return app

    async def start(self):
        """Start HTTP server"""
        import uvicorn

        self.running = True
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)

        logger.info(f"HTTP server starting on {self.host}:{self.port}")
        try:
            await server.serve()
        except asyncio.CancelledError:
            logger.info("HTTP server stopped")
            self.running = False

    async def stop(self):
        """Stop HTTP server"""
        self.running = False
        logger.info("Stopping HTTP server...")
