"""FFmpeg command builders for audio controls."""

from __future__ import annotations

from typing import List, Optional

from ffedit.ffmpeg.timeutils import format_seconds, parse_time_to_seconds

_AUDIO_CODEC_ARGS = ["-c:a", "aac", "-b:a", "192k"]
_VIDEO_COPY_ARGS = ["-c:v", "copy"]


def _build_between_expression(start_time: Optional[str], end_time: Optional[str]) -> Optional[str]:
    if start_time is None or end_time is None:
        return None
    start_seconds = parse_time_to_seconds(start_time)
    end_seconds = parse_time_to_seconds(end_time)
    if start_seconds is None or end_seconds is None:
        return None
    if end_seconds <= start_seconds:
        raise ValueError("End time must be greater than start time.")
    return f"between(t,{format_seconds(start_seconds)},{format_seconds(end_seconds)})"


def build_mute_all_command(input_file: str, output_file: str) -> List[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-an",
        *_VIDEO_COPY_ARGS,
        output_file,
    ]


def build_mute_segment_command(
    input_file: str,
    output_file: str,
    *,
    start_time: str,
    end_time: str,
) -> List[str]:
    expr = _build_between_expression(start_time, end_time)
    if not expr:
        raise ValueError("Start and end times must be provided to mute a segment.")
    filter_str = f"volume=0:enable='{expr}'"
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-af",
        filter_str,
        *_VIDEO_COPY_ARGS,
        *_AUDIO_CODEC_ARGS,
        output_file,
    ]


def build_volume_command(
    input_file: str,
    output_file: str,
    *,
    factor: float,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
) -> List[str]:
    if factor <= 0:
        raise ValueError("Volume factor must be greater than 0.")
    expr = _build_between_expression(start_time, end_time)
    filter_str = f"volume={factor}"
    if expr:
        filter_str += f":enable='{expr}'"
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-af",
        filter_str,
        *_VIDEO_COPY_ARGS,
        *_AUDIO_CODEC_ARGS,
        output_file,
    ]


def build_loudnorm_command(input_file: str, output_file: str) -> List[str]:
    filter_str = "loudnorm=I=-16:TP=-1.5:LRA=11"
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-af",
        filter_str,
        *_VIDEO_COPY_ARGS,
        *_AUDIO_CODEC_ARGS,
        output_file,
    ]


def build_denoise_command(
    input_file: str,
    output_file: str,
    *,
    noise_reduction: int = 18,
) -> List[str]:
    filter_str = f"afftdn=nr={max(1, min(noise_reduction, 60))}"
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-af",
        filter_str,
        *_VIDEO_COPY_ARGS,
        *_AUDIO_CODEC_ARGS,
        output_file,
    ]


def build_extract_audio_command(input_file: str, output_file: str) -> List[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-vn",
        output_file,
    ]


def build_replace_audio_command(
    video_file: str,
    audio_file: str,
    output_file: str,
) -> List[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        video_file,
        "-i",
        audio_file,
        "-map",
        "0:v",
        "-map",
        "1:a",
        *_VIDEO_COPY_ARGS,
        *_AUDIO_CODEC_ARGS,
        "-shortest",
        output_file,
    ]


def build_mix_background_command(
    video_file: str,
    music_file: str,
    output_file: str,
    *,
    music_volume: float = 0.2,
) -> List[str]:
    if music_volume <= 0:
        raise ValueError("Music volume must be greater than 0.")
    filter_complex = (
        f"[1:a]volume={music_volume}[bg];"
        "[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )
    return [
        "ffmpeg",
        "-y",
        "-i",
        video_file,
        "-i",
        music_file,
        "-filter_complex",
        filter_complex,
        "-map",
        "0:v",
        "-map",
        "[aout]",
        *_VIDEO_COPY_ARGS,
        *_AUDIO_CODEC_ARGS,
        "-shortest",
        output_file,
    ]


def build_fade_command(
    input_file: str,
    output_file: str,
    *,
    fade_in_duration: int = 0,
    fade_out_duration: int = 0,
    fade_out_start: Optional[str] = None,
) -> List[str]:
    filters: List[str] = []
    if fade_in_duration > 0:
        filters.append(f"afade=t=in:ss=0:d={fade_in_duration}")
    if fade_out_duration > 0:
        start_seconds = parse_time_to_seconds(fade_out_start) if fade_out_start else 0.0
        if start_seconds is None:
            start_seconds = 0.0
        filters.append(
            f"afade=t=out:st={format_seconds(start_seconds)}:d={fade_out_duration}"
        )
    if not filters:
        raise ValueError("Provide at least one fade duration.")
    filter_str = ",".join(filters)
    return [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-af",
        filter_str,
        *_VIDEO_COPY_ARGS,
        *_AUDIO_CODEC_ARGS,
        output_file,
    ]
