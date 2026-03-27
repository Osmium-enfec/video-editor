from functools import partial
import os

from PySide6.QtWidgets import QFileDialog, QInputDialog

from ffedit.ffmpeg.cut import build_cut_command
from ffedit.core.executor import FFmpegExecutor


class CutFeature:
    def __init__(self, main_window):
        self.main_window = main_window
        self.multi_mode_active = False
        self.multi_segments = []  # list of (start, end)
        self._last_multi_end = "00:00:00"
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

    def _run_single_cut(self) -> None:
        start, ok1 = QInputDialog.getText(
            self.main_window, "Start Time", "Enter start time (e.g. 00:01:00):"
        )
        if not ok1 or not start:
            return
        end, ok2 = QInputDialog.getText(
            self.main_window, "End Time", "Enter end time (e.g. 00:02:00):"
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
        cmd = build_cut_command(self.main_window.input_file, start, end, out_file)
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
            f"Starting {label}: {start} to {end} -> {out_file}"
        )
        executor.start()

    def _start_multi_mode(self) -> None:
        self.multi_mode_active = True
        self.multi_segments = []
        self._pending_multi_jobs = []
        self._last_multi_end = "00:00:00"
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
        layout.set_cut_markers([])

    def add_multi_cut_segment(self) -> None:
        if not self.multi_mode_active:
            self.main_window.layout.log_panel.append(
                "Enable Multiple Cuts to add marked segments."
            )
            return

        default_start = self._last_multi_end
        start, ok1 = QInputDialog.getText(
            self.main_window,
            "Segment Start",
            "Enter segment start time (hh:mm:ss or seconds):",
            text=default_start,
        )
        if not ok1 or not start:
            return
        end, ok2 = QInputDialog.getText(
            self.main_window,
            "Segment End",
            "Enter segment end time (hh:mm:ss or seconds):",
            text=start,
        )
        if not ok2 or not end:
            return

        start = start.strip()
        end = end.strip()
        if not self._is_end_after_start(start, end):
            self.main_window.layout.log_panel.append(
                "Segment not added: end time must be after start time."
            )
            return

        self.multi_segments.append((start, end))
        self._last_multi_end = end
        idx = len(self.multi_segments)
        self.main_window.layout.log_panel.append(
            f"Marked segment {idx}: {start} -> {end}"
        )
        self._update_timeline_markers()

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
        self._last_multi_end = self.multi_segments[-1][1] if self.multi_segments else "00:00:00"
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
        self._last_multi_end = "00:00:00"
        self._multi_total_segments = 0
        self._multi_completed_segments = 0
        layout = self.main_window.layout
        layout.cut_btn.setText("Cut Video")
        layout.cut_btn.setEnabled(True)
        layout.mark_btn.setEnabled(False)
        layout.mark_btn.setVisible(False)
        layout.set_cut_markers([])

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
            parts = [float(p) for p in text.split(":")]
            while len(parts) < 3:
                parts.insert(0, 0.0)
            hours, minutes, seconds = parts[-3:]
            return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            return None

    def _update_timeline_markers(self) -> None:
        duration_ms = self.main_window.layout.player_widget.media_player.duration()
        if duration_ms <= 0:
            self.main_window.layout.set_cut_markers([])
            return
        duration_s = duration_ms / 1000.0
        markers = []
        for _, end in self.multi_segments:
            seconds = self._time_to_seconds(end)
            if seconds is None or duration_s <= 0:
                continue
            ratio = max(0.0, min(1.0, seconds / duration_s))
            markers.append(ratio)
        self.main_window.layout.set_cut_markers(markers)

    def _update_multi_progress(self) -> None:
        total = max(1, self._multi_total_segments)
        completed = min(self._multi_completed_segments, total)
        percent = int((completed / total) * 100)
        self.main_window.layout.progress.setValue(percent)
