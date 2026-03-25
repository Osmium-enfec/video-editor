"""
FFmpeg progress parser for ffedit.
Parses FFmpeg stderr for progress information.
"""
def parse_progress(line):
    """
    Parse FFmpeg progress from stderr line.
    Returns progress as float (0.0-1.0) or None if not found.
    """
    if "time=" in line:
        # Example: time=00:01:23.45
        import re
        m = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
        if m:
            h, m_, s = map(float, m.groups())
            seconds = h * 3600 + m_ * 60 + s
            return seconds
    return None
