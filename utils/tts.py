import hashlib
from gtts import gTTS
import os

# ✅ Ensure we save the file in Hugging Face-compatible directory
AUDIO_DIR = "/tmp/audio"  # Hugging Face allows writing to /tmp/
os.makedirs(AUDIO_DIR, exist_ok=True)  # Create dir if it doesn’t exist

def generate_hindi_tts(text):
    """Generate Hindi speech from text and return audio file path"""
    try:
        if not text or not isinstance(text, str):
            raise ValueError("Invalid text input for TTS")

        # Create a hash of the text for a consistent filename
        hash_name = hashlib.md5(text.encode()).hexdigest()[:10]  # 10-char hash
        filename = f"{hash_name}.mp3"
        file_path = os.path.join(AUDIO_DIR, filename)

        # Check if file already exists to avoid re-generating it
        if not os.path.exists(file_path):
            tts = gTTS(text=text, lang="hi")
            tts.save(file_path)
            os.chmod(file_path, 0o644)  # ✅ Fix file permission issues
            print(f"✅ New audio file saved: {file_path}")
        else:
            print(f"🔄 Reusing existing file: {file_path}")

        return file_path  # ✅ Corrected path

    except Exception as e:
        print(f"❌ Error generating TTS: {e}")
        return None
