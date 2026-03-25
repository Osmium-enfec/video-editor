"""Build FFmpeg commands for black screen overlays with optional audio control."""

from __future__ import annotations

from typing import List, Optional

from ffedit.ffmpeg.timeutils import format_seconds, parse_time_to_seconds


def build_black_command(
    input_file: str,
    output_file: str,
    *,
    start_time: str,
    end_time: str,
    mute_audio: bool = False,
) -> List[str]:
    """Return an FFmpeg command that paints a full-frame black box between two times."""

    start_seconds = parse_time_to_seconds(start_time)
    end_seconds = parse_time_to_seconds(end_time)
    if start_seconds is None or end_seconds is None:
        raise ValueError("Start and end times are required for black screen insertions.")
    if end_seconds <= start_seconds:
        raise ValueError("End time must be greater than start time for black screen insertions.")

    enable_expr = f"between(t,{format_seconds(start_seconds)},{format_seconds(end_seconds)})"
    drawbox = f"drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:enable='{enable_expr}'"

    cmd: List[str] = [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-vf",
        drawbox,
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "slow",
    ]

    if mute_audio:
        audio_filter = f"volume=enable='{enable_expr}':0"
        cmd += [
            "-af",
            audio_filter,
            "-c:a",
            "aac",
            "-b:a",
            "192k",
        ]
    else:
        cmd += ["-c:a", "copy"]

    cmd.append(output_file)
    return cmd
