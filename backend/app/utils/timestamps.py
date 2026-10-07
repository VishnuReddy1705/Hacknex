import math

def seconds_to_timestamp(seconds: float) -> str:
    if seconds is None or math.isnan(seconds) or seconds < 0:
        return "00:00"
    total_sec = int(round(seconds))
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def timestamp_to_seconds(ts_str: str) -> float:
    if not ts_str:
        return 0.0
    parts = ts_str.strip().split(":")
    try:
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 1:
            return float(parts[0])
    except ValueError:
        return 0.0
    return 0.0

def format_duration_str(seconds: float) -> str:
    if seconds is None or seconds <= 0:
        return "0s"
    sec = round(seconds, 1)
    if sec < 60:
        return f"{sec}s"
    mins = int(sec // 60)
    rem_sec = round(sec % 60, 1)
    return f"{mins}m {rem_sec}s"
