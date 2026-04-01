from __future__ import annotations

from functools import partial
import os

from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from ffedit.ffmpeg.cut import build_cut_command
from ffedit.core.executor import FFmpegExecutor


class CutFeature:
    def __init__(self, main_window):
        self.main_window = main_window
        self.multi_mode_active = False
        self.multi_segments = []  # list of (start, end)
        self.archived_segments: list[tuple[str, str]] = []
        self._last_multi_end = self._latest_archived_end() or "00:00:00:00"
        self._pending_multi_jobs = []  # list of (index, start, end, output)
        self._multi_total_segments = 0
        self._multi_completed_segments = 0

    def cut_video(self):
        if not self.main_window.input_file:
            self.main_window.layout.log_panel.append("No input file selected.")
            return

        if self.multi_mode_active:
            self._complete_multi_cut()
            return

        mode, ok = QInputDialog.getItem(
            self.main_window,
            "Choose Cut Mode",
            "Select how you would like to cut the video:",
            ["Single Cut", "Multiple Cuts"],
            0,
            False,
        )
        if not ok:
            return
        if mode == "Single Cut":
            self._run_single_cut()
        else:
            self._start_multi_mode()

    def reset_for_new_video(self) -> None:
        """Clear any multi-cut state when the active video is removed."""

        self.archived_segments = []
        self._reset_multi_state()

    def start_single_cut_shortcut(self) -> None:
        if not self.main_window.input_file:
            self.main_window.layout.log_panel.append(
                "Load a video before starting a Single Cut (shortcut C)."
            )
            return
        if self.multi_mode_active:
            self.main_window.layout.log_panel.append(
                "Complete or cancel Multiple Cuts before starting a Single Cut."
            )
            return
        self._run_single_cut()

    def start_multiple_cut_shortcut(self) -> None:
        if not self.main_window.input_file:
            self.main_window.layout.log_panel.append(
                "Load a video before enabling Multiple Cuts (shortcut M)."
            )
            return
        if self.multi_mode_active:
            self.main_window.layout.log_panel.append(
                "Multiple Cuts already enabled. Use Mark Cut or press B to export."
            )
            return
        self._start_multi_mode()

    def apply_current_time_cut_shortcut(self) -> None:
        if not self.main_window.input_file:
            self.main_window.layout.log_panel.append(
                "Load a video before applying a cut with shortcut B."
            )
            return
        if not self.multi_mode_active:
            self.main_window.layout.log_panel.append(
                "Press M to enable Multiple Cuts before using shortcut B."
            )
            return
        if self._pending_multi_jobs:
            self.main_window.layout.log_panel.append(
                "Finish the ongoing export before marking new segments."
            )
            return

        player_widget = self.main_window.layout.player_widget
        player_widget.pause()
        current_ms = player_widget.media_player.position()
        if current_ms <= 0:
            self.main_window.layout.log_panel.append(
                "Move the playhead to the desired time before pressing B."
            )
            return

        start_time = self._last_multi_end or self._latest_archived_end() or "00:00:00:00"
        end_time = self._format_timecode_from_ms(current_ms)
        if not self._is_end_after_start(start_time, end_time):
            self.main_window.layout.log_panel.append(
                f"Shortcut B skipped: current time must be after the last marker ({start_time})."
            )
            return

        self._append_segment(start_time, end_time, via_shortcut=True)

    def complete_multiple_cut_shortcut(self) -> None:
        if not self.main_window.input_file:
            self.main_window.layout.log_panel.append(
                "Load a video before exporting Multiple Cuts (shortcut B)."
            )
            return
        if not self.multi_mode_active:
            self.main_window.layout.log_panel.append(
                "Press M to enable Multiple Cuts before exporting with B."
            )
            return
        self._complete_multi_cut()

    def _run_single_cut(self) -> None:
        start, ok1 = QInputDialog.getText(
            self.main_window,
            "Start Time",
            "Enter start time (format hh:mm:ss:cc or seconds):",
            text="00:00:00:00",
        )
        if not ok1 or not start:
            return
        end, ok2 = QInputDialog.getText(
            self.main_window,
            "End Time",
            "Enter end time (format hh:mm:ss:cc or seconds):",
            text=start,
        )
        if not ok2 or not end:
            return
        out_file, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Save Cut Video As",
            os.path.expanduser("~"),
            "Video Files (*.mp4 *.mov *.avi *.mkv)",
        )
        if not out_file:
            return
        self._launch_cut_job(start.strip(), end.strip(), out_file)

    def _launch_cut_job(
        self,
        start: str,
        end: str,
        out_file: str,
        *,
        segment_label: str | None = None,
        segment_output: str | None = None,
    ) -> None:
        start_display, start_cmd = self._prepare_time_value(start)
        end_display, end_cmd = self._prepare_time_value(end)
        cmd = build_cut_command(self.main_window.input_file, start_cmd, end_cmd, out_file)
        executor = FFmpegExecutor(cmd)
        executor.progress.connect(self.main_window.layout.progress.setValue)
        executor.log.connect(self.main_window.layout.log_panel.append)
        if segment_label:
            executor.finished.connect(
                partial(self._on_multi_segment_finished, segment_label, segment_output or out_file)
            )
        else:
            executor.finished.connect(self.main_window._on_cut_finished)
        self.main_window.executor = executor
        self.main_window.layout.progress.setValue(0)
        label = segment_label or "cut"
        self.main_window.layout.log_panel.append(
            f"Starting {label}: {start_display} to {end_display} -> {out_file}"
        )
        executor.start()

    def _start_multi_mode(self) -> None:
        self.multi_mode_active = True
        self.multi_segments = []
        self._pending_multi_jobs = []
        self._last_multi_end = self._latest_archived_end() or "00:00:00:00"
        self._multi_total_segments = 0
        self._multi_completed_segments = 0
        layout = self.main_window.layout
        layout.cut_btn.setText("Complete Cut")
        layout.mark_btn.setEnabled(True)
        layout.mark_btn.setVisible(True)
        layout.update_responsive_controls(self.main_window.width())
        layout.log_panel.append(
            "Multiple Cuts mode enabled. Use Mark Cut to add segments before completing."
        )
        self._update_timeline_markers()

    def add_multi_cut_segment(self) -> None:
        if not self.multi_mode_active:
            self.main_window.layout.log_panel.append(
                "Enable Multiple Cuts to add marked segments."
            )
            return

        player_widget = self.main_window.layout.player_widget
        player_widget.pause()
        current_position = player_widget.media_player.position()
        end_default = self._format_timecode_from_ms(current_position)

        default_start = self._last_multi_end or self._latest_archived_end() or "00:00:00:00"
        start, ok1 = QInputDialog.getText(
            self.main_window,
            "Segment Start",
            "Enter segment start time (hh:mm:ss:cc or seconds):",
            text=default_start,
        )
        if not ok1 or not start:
            return
        end, ok2 = QInputDialog.getText(
            self.main_window,
            "Segment End",
            "Enter segment end time (hh:mm:ss:cc or seconds):",
            text=end_default,
        )
        if not ok2 or not end:
            return

        self._append_segment(start, end)

    def _append_segment(self, start: str, end: str, *, via_shortcut: bool = False) -> bool:
        start = (start or "").strip()
        end = (end or "").strip()
        if not start or not end:
            self.main_window.layout.log_panel.append(
                "Segment not added: start and end times are required."
            )
            return False
        if not self._is_end_after_start(start, end):
            self.main_window.layout.log_panel.append(
                "Segment not added: end time must be after start time."
            )
            return False

        start_norm, _ = self._prepare_time_value(start)
        end_norm, _ = self._prepare_time_value(end)
        start_norm = self._adjust_start_for_archived(start_norm)

        if not self._is_end_after_start(start_norm, end_norm):
            self.main_window.layout.log_panel.append(
                "Segment not added: end must be after adjusted start time."
            )
            return False
        if self._segment_overlaps_archived(start_norm, end_norm):
            self.main_window.layout.log_panel.append(
                "Segment overlaps previously exported footage and was skipped."
            )
            return False

        if self.multi_segments:
            last_end = self._time_to_seconds(self.multi_segments[-1][1]) or 0.0
            new_start = self._time_to_seconds(start_norm) or 0.0
            if new_start < last_end:
                self.main_window.layout.log_panel.append(
                    "Segment not added: start overlaps the previous marked segment."
                )
                return False

        self.multi_segments.append((start_norm, end_norm))
        self._last_multi_end = end_norm
        idx = len(self.multi_segments)
        suffix = " (shortcut B)" if via_shortcut else ""
        self.main_window.layout.log_panel.append(
            f"Marked segment {idx}: {start_norm} -> {end_norm}{suffix}"
        )
        self._update_timeline_markers()
        return True

    def remove_segment_marker(self, ratio: float) -> None:
        """Remove the corresponding segment when a timeline marker is clicked."""
        if not self.multi_mode_active or self._pending_multi_jobs:
            self._update_timeline_markers()
            return

        duration_ms = self.main_window.layout.player_widget.media_player.duration()
        if duration_ms <= 0:
            self._update_timeline_markers()
            return
        duration_s = duration_ms / 1000.0
        threshold = 0.02
        closest_idx = None
        closest_diff = threshold

        for idx, (_, end) in enumerate(self.multi_segments):
            end_secs = self._time_to_seconds(end)
            if end_secs is None or duration_s <= 0:
                continue
            seg_ratio = max(0.0, min(1.0, end_secs / duration_s))
            diff = abs(seg_ratio - ratio)
            if diff <= closest_diff:
                closest_idx = idx
                closest_diff = diff

        if closest_idx is None:
            self._update_timeline_markers()
            return

        start, end = self.multi_segments.pop(closest_idx)
        self._last_multi_end = self.multi_segments[-1][1] if self.multi_segments else "00:00:00:00"
        self.main_window.layout.log_panel.append(
            f"Removed segment {closest_idx + 1}: {start} -> {end}"
        )
        self._update_timeline_markers()

    def _complete_multi_cut(self) -> None:
        if not self.multi_segments:
            self.main_window.layout.log_panel.append(
                "Add at least one segment with Mark Cut before completing."
            )
            return

        duration_ms = self.main_window.layout.player_widget.media_player.duration()
        should_confirm = False
        if duration_ms > 0 and self.multi_segments:
            duration_s = duration_ms / 1000.0
            last_end_secs = self._time_to_seconds(self.multi_segments[-1][1]) or 0.0
            if duration_s - last_end_secs > 0.05:
                should_confirm = True
        if should_confirm:
            reply = QMessageBox.question(
                self.main_window,
                "Export Marked Portions?",
                "The video still has unmarked footage. Export the marked segments anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.main_window.layout.log_panel.append(
                    "Export canceled. Continue adding marks to cover the remaining video."
                )
                return

        base_file, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Save Multiple Cuts As",
            os.path.expanduser("~"),
            "Video Files (*.mp4 *.mov *.avi *.mkv)",
        )
        if not base_file:
            return

        base_dir = os.path.dirname(base_file) or os.getcwd()
        chosen_name = os.path.basename(base_file)
        if "." in os.path.basename(base_file):
            stem, ext = os.path.splitext(chosen_name)
        else:
            stem, ext = chosen_name, ".mp4"
        stem = stem.strip()
        if not stem:
            stem = "segment"
        numbered = []
        for idx, (start, end) in enumerate(self.multi_segments, start=1):
            filename = f"{stem} - {idx}{ext}"
            output_path = os.path.join(base_dir, filename)
            numbered.append((idx, start, end, output_path))

        self._pending_multi_jobs = numbered
        self._multi_total_segments = len(numbered)
        self._multi_completed_segments = 0
        self.main_window.layout.cut_btn.setEnabled(False)
        self.main_window.layout.mark_btn.setEnabled(False)
        self.main_window.layout.log_panel.append(
            f"Exporting {len(numbered)} segments to '{base_dir}'."
        )
        self._update_multi_progress()
        self._start_next_multi_job()

    def _start_next_multi_job(self) -> None:
        if not self._pending_multi_jobs:
            self._archive_current_segments()
            self.main_window.layout.log_panel.append("All segments exported.")
            self.main_window.layout.cut_btn.setEnabled(True)
            self._reset_multi_state()
            return

        idx, start, end, output = self._pending_multi_jobs.pop(0)
        segment_label = f"segment {idx}"
        self._launch_cut_job(
            start,
            end,
            output,
            segment_label=segment_label,
            segment_output=output,
        )

    def _on_multi_segment_finished(
        self, segment_label: str, output_path: str, code: int, msg: str
    ) -> None:
        layout = self.main_window.layout
        if code == 0:
            layout.log_panel.append(
                f"Finished {segment_label}: saved to {output_path}"
            )
            self._multi_completed_segments += 1
            self._update_multi_progress()
            self._start_next_multi_job()
        else:
            layout.log_panel.append(
                f"{segment_label.title()} failed ({msg}). Multiple Cuts aborted."
            )
            layout.cut_btn.setEnabled(True)
            self._reset_multi_state()

    def _reset_multi_state(self) -> None:
        self.multi_mode_active = False
        self.multi_segments = []
        self._pending_multi_jobs = []
        self._last_multi_end = "00:00:00:00"
        self._multi_total_segments = 0
        self._multi_completed_segments = 0
        layout = self.main_window.layout
        layout.cut_btn.setText("Cut Video")
        layout.cut_btn.setEnabled(True)
        layout.mark_btn.setEnabled(False)
        layout.mark_btn.setVisible(False)
        self._update_timeline_markers()

    def _archive_current_segments(self) -> None:
        if not self.multi_segments:
            return
        existing = {(start, end) for start, end in self.archived_segments}
        added = False
        for segment in self.multi_segments:
            if segment not in existing:
                self.archived_segments.append(segment)
                added = True
        if added:
            self._sort_archived_segments()
            self._last_multi_end = self._latest_archived_end() or "00:00:00:00"
        if added:
            self.main_window.layout.log_panel.append(
                "Archived exported segments on the timeline (green markers)."
            )
        self._update_timeline_markers()

    def _is_end_after_start(self, start: str, end: str) -> bool:
        start_secs = self._time_to_seconds(start)
        end_secs = self._time_to_seconds(end)
        if start_secs is None or end_secs is None:
            return end.strip() != start.strip()
        return end_secs > start_secs

    @staticmethod
    def _time_to_seconds(value: str) -> float | None:
        text = value.strip()
        if not text:
            return None
        try:
            if ":" not in text:
                return float(text)
            parts = text.split(":")
            if len(parts) == 4:
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                fraction = parts[3]
                if fraction:
                    frac_value = float(fraction)
                    frac_seconds = frac_value / (10 ** len(fraction))
                else:
                    frac_seconds = 0.0
                return hours * 3600 + minutes * 60 + seconds + frac_seconds

            float_parts = [float(p) for p in parts]
            while len(float_parts) < 3:
                float_parts.insert(0, 0.0)
            hours, minutes, seconds = float_parts[-3:]
            return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            return None

    @staticmethod
    def _format_timecode_from_ms(ms: int) -> str:
        ms = max(0, ms)
        total_centiseconds = ms // 10
        centiseconds = total_centiseconds % 100
        total_seconds = total_centiseconds // 100
        seconds = total_seconds % 60
        total_minutes = total_seconds // 60
        minutes = total_minutes % 60
        hours = total_minutes // 60
        return f"{hours:02}:{minutes:02}:{seconds:02}:{centiseconds:02}"

    @staticmethod
    def _seconds_to_timecode(seconds: float) -> str:
        ms = int(round(max(0.0, seconds) * 1000))
        return CutFeature._format_timecode_from_ms(ms)

    @staticmethod
    def _seconds_to_ffmpeg(seconds: float) -> str:
        ms = int(round(max(0.0, seconds) * 1000))
        rem_ms = ms % 1000
        total_seconds = ms // 1000
        secs = total_seconds % 60
        total_minutes = total_seconds // 60
        minutes = total_minutes % 60
        hours = total_minutes // 60
        return f"{hours:02}:{minutes:02}:{secs:02}.{rem_ms:03}"

    def _prepare_time_value(self, value: str) -> tuple[str, str]:
        text = (value or "").strip()
        if not text:
            text = "0"
        seconds = self._time_to_seconds(text)
        if seconds is None:
            return text, text
        display = self._seconds_to_timecode(seconds)
        ffmpeg_value = self._seconds_to_ffmpeg(seconds)
        return display, ffmpeg_value

    def _update_timeline_markers(self) -> None:
        duration_ms = self.main_window.layout.player_widget.media_player.duration()
        if duration_ms <= 0:
            self.main_window.layout.set_cut_markers([], [])
            return
        duration_s = duration_ms / 1000.0
        active_markers = self._build_marker_ratios(self.multi_segments, duration_s)
        archived_markers = self._build_marker_ratios(self.archived_segments, duration_s)
        self.main_window.layout.set_cut_markers(active_markers, archived_markers)

    def _build_marker_ratios(
        self,
        segments: list[tuple[str, str]],
        duration_s: float,
    ) -> list[float]:
        markers: list[float] = []
        if duration_s <= 0:
            return markers
        for _, end in segments:
            seconds = self._time_to_seconds(end)
            if seconds is None:
                continue
            ratio = max(0.0, min(1.0, seconds / duration_s))
            markers.append(ratio)
        return markers

    def _latest_archived_end(self) -> str | None:
        if not self.archived_segments:
            return None
        return self.archived_segments[-1][1]

    def _adjust_start_for_archived(self, start: str) -> str:
        latest = self._latest_archived_end()
        if not latest:
            return start
        start_secs = self._time_to_seconds(start)
        latest_secs = self._time_to_seconds(latest)
        if start_secs is None or latest_secs is None:
            return start
        if start_secs <= latest_secs:
            return self._seconds_to_timecode(latest_secs)
        return start

    def _segment_overlaps_archived(self, start: str, end: str) -> bool:
        start_secs = self._time_to_seconds(start)
        end_secs = self._time_to_seconds(end)
        if start_secs is None or end_secs is None:
            return False
        for arc_start, arc_end in self.archived_segments:
            arc_start_secs = self._time_to_seconds(arc_start)
            arc_end_secs = self._time_to_seconds(arc_end)
            if arc_start_secs is None or arc_end_secs is None:
                continue
            if start_secs < arc_end_secs and end_secs > arc_start_secs:
                return True
        return False

    def _sort_archived_segments(self) -> None:
        self.archived_segments.sort(
            key=lambda seg: self._time_to_seconds(seg[0]) or 0.0
        )

    def _update_multi_progress(self) -> None:
        total = max(1, self._multi_total_segments)
        completed = min(self._multi_completed_segments, total)
        percent = int((completed / total) * 100)
        self.main_window.layout.progress.setValue(percent)
