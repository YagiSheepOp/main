# audioop.py
# Lightweight stub so discord.py can import audioop where the C extension is missing.
# If any real audio functions are used, this will raise a clear error.

def __getattr__(name):
    def _missing(*args, **kwargs):
        raise RuntimeError(
            "audioop is not available in this environment. "
            "Voice/audio features are disabled. "
            "If you need voice support, deploy to an environment with the audio C extension."
        )
    return _missing
