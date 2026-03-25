import pytest
from ffedit.ffmpeg.cut import build_cut_command
from ffedit.ffmpeg.merge import build_merge_command
from ffedit.ffmpeg.blur import build_blur_command
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
from ffedit.ffmpeg.black import build_black_command

def test_build_cut_command():
    cmd = build_cut_command('in.mp4', '00:00:10', '00:00:20', 'out.mp4')
    assert cmd == [
        'ffmpeg', '-y',
        '-ss', '00:00:10',
        '-to', '00:00:20',
        '-i', 'in.mp4',
        '-c', 'copy',
        'out.mp4'
    ]

def test_build_merge_command():
    cmd = build_merge_command('filelist.txt', 'out.mp4')
    assert cmd == [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', 'filelist.txt',
        '-c', 'copy',
        'out.mp4'
    ]

def test_build_blur_command_full():
    cmd = build_blur_command('in.mp4', 'out.mp4', None, 10)
    assert '-vf' in cmd
    vf_value = cmd[cmd.index('-vf') + 1]
    assert vf_value.startswith('boxblur=10')
    assert '-c:a' in cmd and cmd[cmd.index('-c:a') + 1] == 'copy'

def test_build_blur_command_region():
    cmd = build_blur_command('in.mp4', 'out.mp4', (10, 20, 100, 200), 5)
    assert '-filter_complex' in cmd
    graph = cmd[cmd.index('-filter_complex') + 1]
    assert 'crop=100:200:10:20' in graph
    assert 'overlay=10:20' in graph
    assert '[outv]' in graph
    assert '-map' in cmd and '[outv]' in cmd[cmd.index('-map') + 1]

def test_build_mute_all_command():
    cmd = build_mute_all_command('in.mp4', 'out.mp4')
    assert '-an' in cmd
    assert '-c:v' in cmd and cmd[cmd.index('-c:v') + 1] == 'copy'


def test_build_mute_segment_command():
    cmd = build_mute_segment_command('in.mp4', 'out.mp4', start_time='5', end_time='10')
    af_value = cmd[cmd.index('-af') + 1]
    assert "volume=0" in af_value and "between(t,5,10)" in af_value


def test_build_volume_command_range():
    cmd = build_volume_command('in.mp4', 'out.mp4', factor=2.0, start_time='1', end_time='4')
    af_value = cmd[cmd.index('-af') + 1]
    assert "volume=2.0" in af_value and "between(t,1,4)" in af_value


def test_build_volume_command_full_track():
    cmd = build_volume_command('in.mp4', 'out.mp4', factor=0.7)
    af_value = cmd[cmd.index('-af') + 1]
    assert "enable" not in af_value


def test_build_loudnorm_command():
    cmd = build_loudnorm_command('in.mp4', 'out.mp4')
    assert 'loudnorm' in cmd[cmd.index('-af') + 1]


def test_build_denoise_command():
    cmd = build_denoise_command('in.mp4', 'out.mp4', noise_reduction=80)
    assert 'afftdn=nr=60' in cmd[cmd.index('-af') + 1]


def test_build_extract_audio_command():
    cmd = build_extract_audio_command('in.mp4', 'out.mp3')
    assert '-vn' in cmd


def test_build_replace_audio_command():
    cmd = build_replace_audio_command('video.mp4', 'new.wav', 'out.mp4')
    assert '-map' in cmd and '0:v' in cmd[cmd.index('-map') + 1]
    assert '1:a' in cmd[cmd.index('-map', cmd.index('-map') + 1) + 1]


def test_build_mix_background_command():
    cmd = build_mix_background_command('video.mp4', 'music.mp3', 'out.mp4', music_volume=0.3)
    fc_value = cmd[cmd.index('-filter_complex') + 1]
    assert 'volume=0.3' in fc_value and 'amix=inputs=2' in fc_value


def test_build_fade_command():
    cmd = build_fade_command(
        'in.mp4',
        'out.mp4',
        fade_in_duration=2,
        fade_out_duration=3,
        fade_out_start='50',
    )
    af_value = cmd[cmd.index('-af') + 1]
    assert 'afade=t=in:ss=0:d=2' in af_value
    assert 'afade=t=out:st=50:d=3' in af_value

def test_build_black_command_with_audio():
    cmd = build_black_command('in.mp4', 'out.mp4', start_time='10', end_time='15', mute_audio=False)
    assert '-vf' in cmd
    vf_section = cmd[cmd.index('-vf') + 1]
    assert 'drawbox=' in vf_section and "enable='between(t,10,15)'" in vf_section
    assert '-c:a' in cmd and cmd[cmd.index('-c:a') + 1] == 'copy'

def test_build_black_command_with_mute():
    cmd = build_black_command('in.mp4', 'out.mp4', start_time='00:00:05', end_time='00:00:12', mute_audio=True)
    assert '-af' in cmd
    af_section = cmd[cmd.index('-af') + 1]
    assert "volume=enable='between(t,5,12)'" in af_section
    assert '-c:a' in cmd and cmd[cmd.index('-c:a') + 1] == 'aac'
