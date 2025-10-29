# video_utils.py

import subprocess
import ffmpeg  # Requires ffmpeg-python
import json
from pathlib import Path
from typing import Tuple, Optional

def get_video_metadata(video_path: Path) -> dict:
    """Gets all essential video stream metadata using ffprobe."""
    try:
        probe = ffmpeg.probe(str(video_path))
        video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        return {
            "width": int(video_stream['width']),
            "height": int(video_stream['height']),
            "resolution_str": f"{video_stream['width']}x{video_stream['height']}",
            "bitrate": int(video_stream.get('bit_rate', 0)), # .get() for safety
            "frame_rate": eval(video_stream['r_frame_rate']),
            "pix_fmt": video_stream.get('pix_fmt', 'yuv420p'),
            "codec": video_stream.get('codec_name', 'h264'),
            "profile": video_stream.get('profile', 'Main'),
        }
    except Exception as e:
        print(f"😢 Error probing {video_path}: {e}")
        return None

def adjust_resolution(width: int, height: int, factor: float) -> Tuple[int, int]:
    """Adjusts resolution by a factor, ensuring dimensions are even."""
    new_width = round(width / factor)
    new_height = round(height / factor)
    
    # Ensure even numbers for compatibility
    if new_width % 2 != 0: new_width += 1
    if new_height % 2 != 0: new_height += 1
        
    return new_width, new_height

def encode_video(
    input_path: Path, 
    output_path: Path, 
    target_resolution: str, 
    crf: int, 
    codec: str, 
    profile: str,
    pix_fmt: str = 'yuv420p'
):
    """
    Compresses a video to the target specifications using ffmpeg-python.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    w, h = map(int, target_resolution.split('x'))
    
    try:
        (
            ffmpeg
            .input(str(input_path))
            .filter('scale', w, h)
            .output(
                str(output_path),
                vcodec=codec,
                crf=crf,
                **{'profile:v': profile},
                pix_fmt=pix_fmt,
                loglevel='error'
            )
            .run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print(f"😢 FFmpeg error on {input_path}:\n{e.stderr.decode()}")