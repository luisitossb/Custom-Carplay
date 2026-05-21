import subprocess


def get_volume():
    """Get current output volume (0-100) via PipeWire."""
    try:
        result = subprocess.run(
            ['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'],
            capture_output=True, text=True
        )
        # output: "Volume: 0.80" or "Volume: 0.80 [MUTED]"
        return round(float(result.stdout.split()[1]) * 100)
    except Exception:
        return None


def set_volume(percent):
    """Set output volume (0-100) via PipeWire."""
    try:
        vol = max(0.0, min(1.0, percent / 100))
        subprocess.run(
            ['wpctl', 'set-volume', '@DEFAULT_AUDIO_SINK@', f'{vol:.2f}'],
            capture_output=True
        )
    except Exception:
        pass
