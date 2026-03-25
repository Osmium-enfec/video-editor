"""
FFmpeg cut operation module.
Generates FFmpeg command for lossless video cutting.
"""
def build_cut_command(input_file, start, end, output_file):
    """
    Build FFmpeg command for lossless cut.
    Args:
        input_file (str): Path to input video.
        start (str): Start time (e.g. '00:01:00').
        end (str): End time (e.g. '00:02:00').
        output_file (str): Path to output video.
    Returns:
        list: FFmpeg command as list of args.
    """
    return [
        "ffmpeg", "-y",
        "-ss", start,
        "-to", end,
        "-i", input_file,
        "-c", "copy",
        output_file
    ]
