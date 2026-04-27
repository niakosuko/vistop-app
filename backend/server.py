import os
import tempfile
import wave
import audioop
from pathlib import Path

from flask import Flask, jsonify, request, redirect, send_from_directory
from flask_cors import CORS
from faster_whisper import WhisperModel

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_SIZE = os.getenv("VISTOP_WHISPER_MODEL", "base")
HOST = os.getenv("VISTOP_HOST", "127.0.0.1")
PORT = int(os.getenv("VISTOP_PORT", "8765"))
SILENCE_RMS_THRESHOLD = int(os.getenv("VISTOP_SILENCE_RMS", "180"))
MIN_SECONDS = float(os.getenv("VISTOP_MIN_SECONDS", "0.8"))

app = Flask(__name__)
CORS(app)

_model = None


def get_model():
    global _model
    if _model is None:
        print(f"Cargando modelo Whisper: {MODEL_SIZE}")
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        print("Modelo listo.")
    return _model


def analizar_wav(path: str):
    with wave.open(path, "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        raw = wf.readframes(frames)

    duration = frames / float(rate or 1)

    if channels > 1:
        raw = audioop.tomono(raw, sample_width, 1, 1)

    rms = audioop.rms(raw, sample_width) if raw else 0
    return duration, rms


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "model": MODEL_SIZE})


@app.post("/api/transcribir")
def transcribir():
    if "audio" not in request.files:
        return jsonify({"error": "Falta archivo de audio"}), 400

    audio_file = request.files["audio"]

    if not audio_file.filename:
        return jsonify({"error": "Archivo vacío"}), 400

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            audio_file.save(tmp.name)
            temp_path = tmp.name

        duration, rms = analizar_wav(temp_path)

        if duration < MIN_SECONDS:
            return jsonify({"text": "", "reason": "too_short", "duration": duration, "rms": rms})

        if rms < SILENCE_RMS_THRESHOLD:
            return jsonify({"text": "", "reason": "silence", "duration": duration, "rms": rms})

        model = get_model()
        segments, info = model.transcribe(
            temp_path,
            language="es",
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False,
            temperature=0.0,
        )

        text = " ".join(segment.text.strip() for segment in segments).strip()
        return jsonify(
            {
                "text": text,
                "language": getattr(info, "language", "es"),
                "duration": duration,
                "rms": rms,
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@app.get("/")
def root():
    return redirect("/inicio.html")


@app.get("/<path:path>")
def static_files(path):
    full_path = BASE_DIR / path
    if full_path.exists() and full_path.is_file():
        return send_from_directory(BASE_DIR, path)
    return jsonify({"error": "Archivo no encontrado", "path": path}), 404


if __name__ == "__main__":
    print("=" * 60)
    print("VISTOP backend local")
    print(f"Modelo: {MODEL_SIZE}")
    print(f"Abrir en navegador: http://{HOST}:{PORT}/escucha.html")
    print("=" * 60)
    app.run(host=HOST, port=PORT, debug=True)
