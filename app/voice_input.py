import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import tempfile
import os
from typing import Optional

def get_jd_from_voice(duration: int = 15) -> Optional[str]:
    recognizer = sr.Recognizer()
    fs = 44100
    print(f"Recording for {duration} seconds...")
    try:
        audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
    except Exception as e:
        print(f"Audio record error: {e}")
        return None
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            sf.write(tmp_file.name, audio_data, fs)
            tmp_path = tmp_file.name
        with sr.AudioFile(tmp_path) as source:
            audio = recognizer.record(source)
            transcribed_text = recognizer.recognize_google(audio)
            print("Transcription successful.")
            return transcribed_text
    except sr.UnknownValueError:
        print("Audio not understood.")
        return None
    except sr.RequestError as e:
        print(f"Google Speech Recognition error: {e}")
        return None
    except Exception as e:
        print(f"Transcription error: {e}")
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
