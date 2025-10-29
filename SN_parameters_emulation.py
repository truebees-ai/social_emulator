# analyze_compression.py

import argparse
import json
import os
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from collections import defaultdict
import video_utils as utils  # Assumes video_utils.py from the previous answer

def find_best_crf(
    original_video: Path, 
    target_meta: dict,
    crf_range: tuple
) -> int:
    """
    Finds the CRF value that best matches the target bitrate 
    by re-encoding the original video.
    """
    target_bitrate = target_meta["bitrate"]
    target_res = target_meta["resolution_str"]
    codec = target_meta.get("codec", "libx264")
    profile = target_meta.get("profile", "Main")
    pix_fmt = target_meta.get("pix_fmt", "yuv420p")
    

    if target_bitrate == 0:
        print(f"Skipping {original_video.name}, target bitrate is 0.")
        return None

    # Search for the CRF
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_video_path = Path(tmpdir) / "temp.mp4"
        
        for crf in range(crf_range[0], crf_range[1] + 1):
            utils.encode_video(
                original_video, 
                temp_video_path, 
                target_res, 
                crf, 
                codec, 
                profile,
                pix_fmt
            )
            
            if not temp_video_path.exists():
                print(f"Failed to encode temp file for CRF {crf}")
                exit()
                
            encoded_meta = utils.get_video_metadata(temp_video_path)
            
            if not encoded_meta:
                print(f"Failed to probe temp file for CRF {crf}")
                exit()

            if encoded_meta["bitrate"] < target_bitrate:
                breakpoint()
                return crf  # Found the first CRF that is *below* the target

    return crf_range[1]  # Return max if bitrate was never met

def main(args):
    originals_dir = Path(args.originals_dir)
    socials_dir = Path(args.socials_dir)
    crf_range = (args.crf_min, args.crf_max)
    
    # This structure is based on your crf_computer_analyzer.py
    # It loops through known algorithms to find the matching pairs
    #algorithms = [
    #    "FaceShifter", 
    #    "Deepfakes", 
    #    "Face2Face", 
    #    "FaceSwap", 
    #    "NeuralTextures"
    #]
    
    # This will hold our "database"
    # We load it first to append data, not overwrite
    model_data = defaultdict(lambda: defaultdict(list))
    if os.path.exists(args.output_model_file):
        print(f"Loading existing model from {args.output_model_file} to append data...")
        with open(args.output_model_file, 'r') as f:
            model_data.update(json.load(f))
            # Convert loaded lists to defaultdicts for easier appends
            for platform, codecs in model_data.items():
                model_data[platform] = defaultdict(list, codecs)

    # This list will store all the individual sample data
    samples_list = model_data[args.platform][args.codec]
    
    print(f"Analyzing platform: {args.platform}, codec: {args.codec}")
    
    total_pairs_found = 0
    #for algorithm in algorithms:
    print(f"Checking Videos 📼")

    # Construct paths based on logic from your crf_computer_analyzer.py
    # Path to social videos
    social_video_dir = socials_dir #/ args.platform / f"val_{args.platform.lower()}_{algorithm}"
    # Path to original videos
    original_video_dir = originals_dir #/ algorithm / "c23/videos"
    print(original_video_dir, social_video_dir)
    if not social_video_dir.is_dir():
        print(f"😢  Fail: Social dir not found, skipping: {social_video_dir}")
        exit()
    if not original_video_dir.is_dir():
        print(f"😢  Fail: Original dir not found, skipping: {original_video_dir}")
        exit()

    social_videos = list(social_video_dir.glob("*.mp4"))
    print(f"  Found {len(social_videos)} social videos 📼 in {social_video_dir.name}")
    
    for social_video_path in tqdm(social_videos, desc="Social Videos"):
        original_video_path = original_video_dir / social_video_path.name
        
        if not original_video_path.exists():
            print(f"😱   Missing original for {social_video_path.name}, skipping.")
            continue
            
        orig_meta = utils.get_video_metadata(original_video_path)
        social_meta = utils.get_video_metadata(social_video_path)

        if not orig_meta or not social_meta:
            print(f"🤔  Could not read metadata for {social_video_path.name}, skipping.")
            continue
        best_crf = find_best_crf(original_video_path, social_meta, crf_range)
        
        if best_crf is not None:
            # Add this sample to our list
            samples_list.append({
                "original_res": orig_meta["resolution_str"],
                "target_res": social_meta["resolution_str"],
                "crf": best_crf,
                "profile": social_meta.get("profile", "Main"),
                "source_file": social_video_path.name
            })
            total_pairs_found += 1

    # Update the main data structure
    model_data[args.platform][args.codec] = samples_list
    
    # Save the "database"
    with open(args.output_model_file, 'w') as f:
        json.dump(model_data, f, indent=4)
        
    print(f"🐝 \nSuccessfully added {total_pairs_found} new samples. 🐝")
    print(f"🐝 Total samples for {args.platform}/{args.codec}: {len(samples_list)} 🐝")
    print(f"🐝 Compression model saved to {args.output_model_file} 🐝")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze social media compression and create a model.")
    parser.add_argument("--originals-dir", type=str, required=True, help="Base directory for original videos (e.g., /media/.../manipulated_sequences/)")
    parser.add_argument("--socials-dir", type=str, required=True, help="Base directory for social-shared videos (e.g., /.../ff++_shared/FaceForensics++_shared/)")
    parser.add_argument("--platform", type=str, required=True, choices=["Youtube", "Facebook"], help="Platform to analyze")
    parser.add_argument("--codec", type=str, default="libx264", help="Codec to analyze")
    parser.add_argument("--output-model-file", type=str, default="compression_models.json", help="Path to save the output JSON model.")
    parser.add_argument("--crf-min", type=int, default=20, help="Minimum CRF to search.")
    parser.add_argument("--crf-max", type=int, default=51, help="Maximum CRF to search.")
    
    args = parser.parse_args()
    main(args)