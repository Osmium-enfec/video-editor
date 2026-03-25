"""FFmpeg blur operation module for both full-frame and region-focused workflows."""

from typing import List, Optional, Tuple

from ffedit.ffmpeg.timeutils import format_seconds, parse_time_to_seconds


def build_blur_command(
    input_file: str,
    output_file: str,
    region: Optional[Tuple[int, int, int, int]] = None,
    strength: int = 10,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> List[str]:
    """Return an FFmpeg command that blurs the full frame or a cropped region.

    Raises:
        ValueError: If provided timestamps cannot be parsed.
    """

    start_seconds = parse_time_to_seconds(start_time)
    end_seconds = parse_time_to_seconds(end_time)
    enable_expr = None
    if start_seconds is not None and end_seconds is not None:
        enable_expr = f"between(t,{format_seconds(start_seconds)},{format_seconds(end_seconds)})"

    cmd: List[str] = ["ffmpeg", "-y", "-i", input_file]

    if region:
        x, y, w, h = region
        filters = [
            "[0:v]split=2[base][work]",
            f"[work]crop={w}:{h}:{x}:{y},boxblur={strength}[blurred]",
        ]
        overlay = f"[base][blurred]overlay={x}:{y}"
        if enable_expr:
            overlay += f":enable='{enable_expr}'"
        overlay += "[outv]"
        filters.append(overlay)
        filter_graph = ";".join(filters)
        cmd += [
            "-filter_complex",
            filter_graph,
            "-map",
            "[outv]",
            "-map",
            "0:a?",
        ]
    else:
        vf = f"boxblur={strength}"
        if enable_expr:
            vf += f":enable='{enable_expr}'"
        cmd += ["-vf", vf]

    cmd += [
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "slow",
        "-c:a",
        "copy",
        output_file,
    ]
    return cmd
