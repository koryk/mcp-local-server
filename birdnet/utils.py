import os


def get_audio_bytes(filename: str) -> bytes:
    audio_dir = os.path.expanduser(os.getenv('BIRDNET_AUDIO_DIR', '~/BirdSongs/Extracted/'))
    audio_path = os.path.join(audio_dir, filename)
    try:
        with open(audio_path, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Audio file not found: {filename}")
