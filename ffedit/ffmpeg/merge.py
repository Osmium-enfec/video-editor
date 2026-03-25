"""
FFmpeg merge operation module.
Generates FFmpeg command for merging/concatenating videos.
"""
def build_merge_command(filelist_path, output_file):
    """
    Build FFmpeg command for merging videos using a file list.
    Args:
        filelist_path (str): Path to text file listing videos.
        output_file (str): Path to output video.
    Returns:
        list: FFmpeg command as list of args.
    """
    return [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", filelist_path,
        "-c", "copy",
        output_file
    ]
