
"""
SpeechHandler: Menangani speech-to-text (STT) menggunakan Whisper dan text-to-speech (TTS).
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, Optional
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")


class SpeechHandler:
    def __init__(self, storage_path: str = "./neuro_memory_storage"):
        self.storage_path = Path(storage_path) / "language_tutor" / "audio"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Inisialisasi lazy (hanya load ketika dibutuhkan)
        self._whisper_model = None
        self._tts_engine = None

    def get_tts_config(self) -> Dict[str, object]:
        """Expose status provider TTS untuk UI/config endpoint."""
        return {
            "recommended_default": "local",
            "local": {
                "provider": "pyttsx3",
                "available": self._is_local_tts_available()
            },
            "api": {
                "provider": "template_http",
                "url": os.getenv("PANDAI_TTS_API_URL", ""),
                "voice": os.getenv("PANDAI_TTS_API_VOICE", "default"),
                "format": os.getenv("PANDAI_TTS_API_FORMAT", "mp3"),
                "has_api_key": bool(os.getenv("PANDAI_TTS_API_KEY")),
                "configured": bool(os.getenv("PANDAI_TTS_API_URL")) and bool(os.getenv("PANDAI_TTS_API_KEY"))
            },
            "api_template_env": [
                "PANDAI_TTS_API_KEY=YOUR_TTS_API_KEY_HERE",
                "PANDAI_TTS_API_URL=https://your-tts-provider.example.com/synthesize",
                "PANDAI_TTS_API_VOICE=default",
                "PANDAI_TTS_API_FORMAT=mp3"
            ]
        }

    def _is_local_tts_available(self) -> bool:
        try:
            import pyttsx3  # noqa: F401
            return True
        except ImportError:
            return False

    def _is_api_tts_configured(self) -> bool:
        cfg = self.get_tts_config()["api"]
        return bool(cfg["configured"])

    def _load_whisper(self):
        """Load Whisper model secara lazy."""
        if self._whisper_model is None:
            try:
                import whisper
                # Gunakan model tiny untuk kecepatan, bisa diganti ke small/medium
                self._whisper_model = whisper.load_model("tiny")
            except ImportError:
                print("[SpeechHandler] Whisper not installed. Run: pip install openai-whisper")
                self._whisper_model = None
        return self._whisper_model

    def text_to_speech(
        self, 
        text: str, 
        language: str = "en", 
        output_filename: Optional[str] = None,
        tts_mode: str = "local"
    ) -> Path:
        """
        Convert text ke speech menggunakan gTTS atau pyttsx3 sebagai fallback.
        
        Args:
            text: Teks yang akan diubah ke suara
            language: Kode bahasa (en, id, dll)
            output_filename: Nama file output (opsional)
            
        Returns:
            Path ke file audio yang dihasilkan
        """
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:10]
        base_name = output_filename or f"tts_{digest}"
        if "." in base_name:
            base_name = base_name.rsplit(".", 1)[0]

        mode = (tts_mode or "local").strip().lower()
        if mode not in {"local", "api", "auto"}:
            mode = "local"

        if mode == "local":
            return self._text_to_speech_local(text=text, output_basename=base_name)

        if mode == "api":
            return self._text_to_speech_api(text=text, language=language, output_basename=base_name)

        try:
            return self._text_to_speech_local(text=text, output_basename=base_name)
        except Exception as local_error:
            if self._is_api_tts_configured():
                return self._text_to_speech_api(text=text, language=language, output_basename=base_name)
            raise RuntimeError(
                f"Local TTS unavailable: {local_error}. API TTS belum dikonfigurasi."
            ) from local_error

    def _text_to_speech_local(self, text: str, output_basename: str) -> Path:
        """Gunakan provider lokal/offline."""
        try:
            import pyttsx3
            if self._tts_engine is None:
                self._tts_engine = pyttsx3.init()
                self._tts_engine.setProperty("rate", 170)
                self._tts_engine.setProperty("volume", 1.0)

            wav_path = self.storage_path / f"{output_basename}.wav"
            self._tts_engine.save_to_file(text, str(wav_path))
            self._tts_engine.runAndWait()
            if not wav_path.exists():
                raise RuntimeError("File audio lokal tidak berhasil dibuat.")
            return wav_path
        except Exception as e:
            print(f"[SpeechHandler] Local TTS Error: {e}")
            raise

    def _text_to_speech_api(self, text: str, language: str, output_basename: str) -> Path:
        """Gunakan provider API eksternal yang akan dikonfigurasi belakangan."""
        api_url = os.getenv("PANDAI_TTS_API_URL", "").strip()
        api_key = os.getenv("PANDAI_TTS_API_KEY", "").strip()
        voice = os.getenv("PANDAI_TTS_API_VOICE", "default")
        audio_format = os.getenv("PANDAI_TTS_API_FORMAT", "mp3").strip().lower() or "mp3"

        if not api_url or not api_key:
            raise RuntimeError("API TTS belum dikonfigurasi. Isi PANDAI_TTS_API_URL dan PANDAI_TTS_API_KEY.")

        try:
            import requests

            response = requests.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "language": language,
                    "voice": voice,
                    "format": audio_format
                },
                timeout=int(os.getenv("PANDAI_TTS_API_TIMEOUT", "45"))
            )
            response.raise_for_status()

            output_path = self.storage_path / f"{output_basename}.{audio_format}"
            output_path.write_bytes(response.content)
            return output_path
        except Exception as e:
            print(f"[SpeechHandler] API TTS Error: {e}")
            raise

    def speech_to_text(
        self, 
        audio_filepath: str, 
        language: str = "en"
    ) -> str:
        """
        Convert speech ke text menggunakan OpenAI Whisper.
        
        Args:
            audio_filepath: Path ke file audio
            language: Kode bahasa (en, id, dll)
            
        Returns:
            Teks yang dihasilkan dari speech
        """
        model = self._load_whisper()
        if model is None:
            return "[Speech-to-text not available. Please install Whisper.]"
        
        try:
            result = model.transcribe(audio_filepath, language=language)
            return result["text"].strip()
        except Exception as e:
            print(f"[SpeechHandler] STT Error: {e}")
            return "[Error transcribing audio]"
