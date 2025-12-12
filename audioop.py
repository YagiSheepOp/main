# audioop.py
# Lightweight stub so discord.py can import audioop on platforms
# where the C extension _audioop is missing (e.g., some containers).
# If any real audio functions are called, this raises a clear error.

def __getattr__(name):
    def _missing(*args, **kwargs):
        raise RuntimeError(
            "audioop is not available in this environment. "
            "Voice/audio features are disabled. "
            "If you need voice support, deploy to an image with the audio C extensions "
            "(or install a Python build that includes _audioop)."
        )
    return _missing
