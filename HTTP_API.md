# HTTP API для Crane 2S Controller

## Запуск

HTTP сервер автоматически запускается вместе с приложением на порту **8000**.
По умолчанию при обращении к `/api/camera/stream` появляется локальное окно
OpenCV, но это поведение можно отключить полностью (см. ниже).

```bash
python3 -m src.main
```

## API Endpoints

### Health Check
```bash
curl http://127.0.0.1:8000/health
```

**Ответ:**
```json
{"status": "ok", "service": "crane-controller"}
```

---

### Получить текущий кадр (JPEG)

**Endpoint:** `GET /api/camera/photo`

```bash
# Получить текущий кадр
curl http://127.0.0.1:8000/api/camera/photo -o current.jpg

# Или использовать в браузере
# http://127.0.0.1:8000/api/camera/photo
```

---

### Live Stream (MJPEG)

**Endpoint:** `GET /api/camera/stream`

By default this endpoint also opens an OpenCV preview window on the host
computer.  The window is created only while a client is connected and is
closed when the stream ends.  To run completely headless (no window at all,
not even during a stream) set the environment variable
`PREVIEW_ENABLED=false` before starting the program — the HTTP stream will
continue to work normally but `cv2.imshow` will never be called.

Usage examples:

```bash
# VLC Player
vlc http://127.0.0.1:8000/api/camera/stream

# FFmpeg
ffplay http://127.0.0.1:8000/api/camera/stream

# HTML
<img src="http://127.0.0.1:8000/api/camera/stream" />
```

---

### Снять фото

**Endpoint:** `POST /api/camera/capture`

```bash
curl -X POST http://127.0.0.1:8000/api/camera/capture
```

**Ответ:**
```json
{"status": "success", "message": "Photo captured"}
```

Фото сохраняется в `media/photo/photo_YYYY-MM-DD_HH-MM-SS.jpg`

---

### Начать запись видео

**Endpoint:** `POST /api/camera/record/start`

```bash
curl -X POST http://127.0.0.1:8000/api/camera/record/start
```

**Ответ:**
```json
{"status": "success", "message": "Recording started"}
```

Видео сохраняется в `media/video/recording_YYYY-MM-DD_HH-MM-SS.avi`

---

### Остановить запись видео

**Endpoint:** `POST /api/camera/record/stop`

```bash
curl -X POST http://127.0.0.1:8000/api/camera/record/stop
```

**Ответ:**
```json
{"status": "success", "message": "Recording stopped"}
```

---

### Статус камеры

**Endpoint:** `GET /api/camera/status`

```bash
curl http://127.0.0.1:8000/api/camera/status
```

**Ответ:**
```json
{
  "status": "ok",
  "recording": false,
  "frame_available": true
}
```

---

## Примеры использования

### Python Client

```python
import requests
import cv2

# Получить текущий кадр
response = requests.get('http://127.0.0.1:8000/api/camera/photo')
with open('frame.jpg', 'wb') as f:
    f.write(response.content)

# Снять фото
requests.post('http://127.0.0.1:8000/api/camera/capture')

# Начать запись
requests.post('http://127.0.0.1:8000/api/camera/record/start')

# Получить статус
status = requests.get('http://127.0.0.1:8000/api/camera/status').json()
print(f"Recording: {status['recording']}")

# Остановить запись
requests.post('http://127.0.0.1:8000/api/camera/record/stop')
```

### JavaScript/Fetch API

```javascript
// Получить текущий кадр
async function getPhoto() {
  const response = await fetch('http://127.0.0.1:8000/api/camera/photo');
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  document.getElementById('photo').src = url;
}

// Live stream в img tag
document.getElementById('stream').src = 'http://127.0.0.1:8000/api/camera/stream';

// Снять фото
async function takePhoto() {
  const response = await fetch('http://127.0.0.1:8000/api/camera/capture', {
    method: 'POST'
  });
  const data = await response.json();
  console.log(data.message);
}
```

### HTML Stream Viewer

```html
<!DOCTYPE html>
<html>
<head>
    <title>Crane 2S Camera Stream</title>
    <style>
        body { font-family: Arial; text-align: center; }
        img { max-width: 100%; border: 1px solid #ccc; }
        button { padding: 10px 20px; margin: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Crane 2S Live Stream</h1>
    
    <div>
        <img id="stream" src="http://127.0.0.1:8000/api/camera/stream" 
             style="width: 640px; height: 480px;" />
    </div>
    
    <div>
        <button onclick="capturePhoto()">📸 Take Photo</button>
        <button id="recordBtn" onclick="toggleRecording()">⏺️ Start Recording</button>
    </div>
    
    <div id="status"></div>
    
    <script>
        let isRecording = false;
        
        async function capturePhoto() {
            const response = await fetch(
                'http://127.0.0.1:8000/api/camera/capture',
                { method: 'POST' }
            );
            const data = await response.json();
            document.getElementById('status').innerText = 
                '✓ ' + data.message;
        }
        
        async function toggleRecording() {
            const endpoint = isRecording ? 
                'record/stop' : 'record/start';
            const response = await fetch(
                `http://127.0.0.1:8000/api/camera/${endpoint}`,
                { method: 'POST' }
            );
            const data = await response.json();
            isRecording = !isRecording;
            document.getElementById('recordBtn').innerText = 
                isRecording ? '⏹️ Stop Recording' : '⏺️ Start Recording';
            document.getElementById('status').innerText = 
                '✓ ' + data.message;
        }
        
        // Update status every 2 seconds
        setInterval(async () => {
            const response = await fetch(
                'http://127.0.0.1:8000/api/camera/status'
            );
            const data = await response.json();
            const recordingText = data.recording ? 
                '🔴 Recording...' : '⚫ Not recording';
            document.getElementById('status').innerText = recordingText;
        }, 2000);
    </script>
</body>
</html>
```

---

## Производительность

- **MJPEG Stream**: ~30 FPS (автоматическое снижение quality до 80% для оптимизации)
- **Single Photo**: < 100ms
- **Recording**: Параллельно с потоком, полное качество (1920x1080 @ 30 FPS)

---

## CORS

API имеет включенный CORS, поэтому можно обращаться с веб-приложений на других доменах.

---

## Ошибки

**503 Service Unavailable** - Камера недоступна
```json
{"error": "Camera not available"}
```

**500 Internal Server Error** - Ошибка обработки
```json
{"error": "error description"}
```
