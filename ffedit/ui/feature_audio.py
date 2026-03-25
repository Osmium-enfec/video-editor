from typing import Callable, List, Optional, Tuple

from PySide6.QtWidgets import QFileDialog, QInputDialog
import os
from ffedit.ffmpeg.audio import (
    build_denoise_command,
    build_extract_audio_command,
    build_fade_command,
    build_loudnorm_command,
    build_mix_background_command,
    build_mute_all_command,
    build_mute_segment_command,
    build_replace_audio_command,
    build_volume_command,
)
from ffedit.core.executor import FFmpegExecutor

AudioBuilder = Callable[[str], List[str]]


class AudioFeature:
    def __init__(self, main_window):
        self.main_window = main_window

    def audio_controls(self):
        input_path = self.main_window.input_file
        if not input_path:
            self._log("No input file selected.")
            return

        operations = [
            "Mute Entire Audio",
            "Mute Between Times",
            "Adjust Volume",
            "Normalize Audio",
            "Remove Noise",
            "Extract Audio Only",
            "Replace Audio Track",
            "Add Background Music",
            "Fade In/Out",
        ]
        op, ok = QInputDialog.getItem(
            self.main_window,
            "Audio Operation",
            "Select audio operation:",
            operations,
            0,
            False,
        )
        if not ok:
            return

        prepared = self._prepare_operation(op, input_path)
        if not prepared:
            return
        desc, builder = prepared

        out_file = self._prompt_output_file(op)
        if not out_file:
            return

        try:
            cmd = builder(out_file)
        except ValueError as exc:
            self._log(str(exc))
            return

        executor = FFmpegExecutor(cmd)
        executor.progress.connect(self.main_window.layout.progress.setValue)
        executor.log.connect(self.main_window.layout.log_panel.append)
        executor.finished.connect(self.main_window._on_audio_finished)
        self.main_window.executor = executor
        self.main_window.layout.progress.setValue(0)
        self._log(f"Starting audio operation: {desc} -> {out_file}")
        executor.start()

    def _prepare_operation(
        self,
        op: str,
        input_path: str,
    ) -> Optional[Tuple[str, AudioBuilder]]:
        if op == "Mute Entire Audio":
            return (
                "Muting entire audio track",
                lambda out_file: build_mute_all_command(input_path, out_file),
            )

        if op == "Mute Between Times":
            start = self._prompt_time("Mute Start", "Mute start time (e.g. 00:00:10):", default="00:00:00")
            if start is None or not start:
                return None
            end = self._prompt_time("Mute End", "Mute end time (e.g. 00:00:15):")
            if end is None or not end:
                return None
            desc = f"Muting audio from {start} to {end}"
            return (
                desc,
                lambda out_file, s=start, e=end: build_mute_segment_command(
                    input_path,
                    out_file,
                    start_time=s,
                    end_time=e,
                ),
            )

        if op == "Adjust Volume":
            factor = self._prompt_double("Volume", "Enter volume (0.1-5.0):", 0.5, 0.1, 5.0)
            if factor is None:
                return None
            start = self._prompt_time("Volume Start", "Start time (blank = full track):", default="00:00:00", optional=True)
            if start is None:
                return None
            end = self._prompt_time("Volume End", "End time (blank = full track):", optional=True)
            if end is None:
                return None
            start = start or None
            end = end or None
            if (start and not end) or (end and not start):
                self._log("Provide both start and end times or leave both blank.")
                return None
            desc = f"Setting volume to {factor}x"
            if start and end:
                desc += f" between {start} and {end}"
            return (
                desc,
                lambda out_file, s=start, e=end, f=factor: build_volume_command(
                    input_path,
                    out_file,
                    factor=f,
                    start_time=s,
                    end_time=e,
                ),
            )

        if op == "Normalize Audio":
            return (
                "Normalizing audio loudness",
                lambda out_file: build_loudnorm_command(input_path, out_file),
            )

        if op == "Remove Noise":
            strength = self._prompt_int("Noise Reduction", "Noise reduction amount (1-60):", 20, 1, 60)
            if strength is None:
                return None
            desc = f"Reducing background noise (nr={strength})"
            return (
                desc,
                lambda out_file, nr=strength: build_denoise_command(
                    input_path,
                    out_file,
                    noise_reduction=nr,
                ),
            )

        if op == "Extract Audio Only":
            return (
                "Extracting audio track",
                lambda out_file: build_extract_audio_command(input_path, out_file),
            )

        if op == "Replace Audio Track":
            audio_file = self._prompt_media_file("Select replacement audio track")
            if not audio_file:
                return None
            desc = f"Replacing audio with {os.path.basename(audio_file)}"
            return (
                desc,
                lambda out_file, new_audio=audio_file: build_replace_audio_command(
                    input_path,
                    new_audio,
                    out_file,
                ),
            )

        if op == "Add Background Music":
            music_file = self._prompt_media_file("Select background music track")
            if not music_file:
                return None
            volume = self._prompt_double("Music Volume", "Music volume (0.05-1.0):", 0.2, 0.05, 1.0)
            if volume is None:
                return None
            desc = f"Mixing {os.path.basename(music_file)} at {volume * 100:.0f}%"
            return (
                desc,
                lambda out_file, track=music_file, mv=volume: build_mix_background_command(
                    input_path,
                    track,
                    out_file,
                    music_volume=mv,
                ),
            )

        if op == "Fade In/Out":
            fade_in = self._prompt_int("Fade In", "Fade-in duration (seconds):", 0, 0, 120)
            if fade_in is None:
                return None
            fade_out = self._prompt_int("Fade Out", "Fade-out duration (seconds):", 0, 0, 120)
            if fade_out is None:
                return None
            fade_out_start = None
            if fade_out > 0:
                start = self._prompt_time(
                    "Fade Out Start",
                    "Fade-out start time (blank = from 0):",
                    optional=True,
                )
                if start is None:
                    return None
                fade_out_start = start or None
            if fade_in == 0 and fade_out == 0:
                self._log("Set at least one fade duration.")
                return None
            desc = f"Applying fades (in={fade_in}s, out={fade_out}s)"
            return (
                desc,
                lambda out_file, fi=fade_in, fo=fade_out, fos=fade_out_start: build_fade_command(
                    input_path,
                    out_file,
                    fade_in_duration=fi,
                    fade_out_duration=fo,
                    fade_out_start=fos,
                ),
            )

        return None

    def _prompt_output_file(self, caption: str) -> Optional[str]:
        out_file, _ = QFileDialog.getSaveFileName(
            self.main_window,
            f"Save Result ({caption})",
            os.path.expanduser("~"),
            "Media Files (*.mp4 *.mov *.mkv *.mp3 *.wav *.aac)",
        )
        return out_file or None

    def _prompt_media_file(self, caption: str) -> Optional[str]:
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            caption,
            "",
            "Audio Files (*.mp3 *.wav *.aac *.m4a *.flac)",
        )
        return file_path or None

    def _prompt_time(
        self,
        title: str,
        label: str,
        *,
        default: str = "",
        optional: bool = False,
    ) -> Optional[str]:
        text, ok = QInputDialog.getText(self.main_window, title, label, text=default)
        if not ok:
            return None
        text = text.strip()
        if not text:
            return "" if optional else None
        return text

    def _prompt_double(
        self,
        title: str,
        label: str,
        default: float,
        minimum: float,
        maximum: float,
    ) -> Optional[float]:
        value, ok = QInputDialog.getDouble(
            self.main_window,
            title,
            label,
            default,
            minimum,
            maximum,
            2,
        )
        if not ok:
            return None
        return value

    def _prompt_int(
        self,
        title: str,
        label: str,
        default: int,
        minimum: int,
        maximum: int = 600,
    ) -> Optional[int]:
        value, ok = QInputDialog.getInt(
            self.main_window,
            title,
            label,
            default,
            minimum,
            maximum,
        )
        if not ok:
            return None
        return value

    def _log(self, message: str) -> None:
        self.main_window.layout.log_panel.append(message)
