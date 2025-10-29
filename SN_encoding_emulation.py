# emulate_compression.py

import argparse
import json
import numpy as np
from pathlib import Path
import video_utils as utils  # Assumes video_utils.py from the previous answer
from tqdm import tqdm

def get_closest_resolution(current_res: str, known_resolutions: list) -> str:
    """
    Finds the closest resolution from a list based on total pixel area.
    """
    if not known_resolutions:
        return None
        
    w, h = map(int, current_res.split('x'))
    current_area = w * h
    
    best_match = None
    min_diff = float('inf')
    
    for res_str in known_resolutions:
        w_known, h_known = map(int, res_str.split('x'))
        area = w_known * h_known
        diff = abs(current_area - area)
        
        if diff < min_diff:
            min_diff = diff
            best_match = res_str
            
    return best_match

def get_emulation_params(current_res: str, samples: list, platform: str) -> dict:
    """
    Implements the Look-Up-Table logic:
    1. Find best matching input resolution.
    2. Determine target output resolution from that match.
    3. Average CRF of ALL samples with that *target* resolution.
    """
    if not samples:
        return None

    # Get all unique original resolutions from our samples
    known_original_resolutions = list(set(s["original_res"] for s in samples))
    
    # --- 1. Find best matching input resolution ---
    best_input_res = None
    if current_res in known_original_resolutions:
        best_input_res = current_res
    else:
        best_input_res = get_closest_resolution(current_res, known_original_resolutions)
        
    if not best_input_res:
        print(f"Warning: No matching resolutions found in model for {current_res}.")
        return None

    # --- 2. Determine target output resolution ---
    # Find the first sample matching our best input res to see its target
    # (We assume all samples with the same input_res have the same target_res)
    selected_target_res = None
    
    # --- MODIFIED LINE: Set profile based on platform ---
    selected_profile = "high" if platform == "Youtube" else "main"

    for s in samples:
        if s["original_res"] == best_input_res:
            selected_target_res = s["target_res"]
            # We no longer get the profile from the sample
            break
            
    if not selected_target_res:
        print(f"Warning: Logic error, no target res found for {best_input_res}.")
        return None
        
    # --- 3. Average CRF of all samples with that target res ---
    crf_values = []
    for s in samples:
        if s["target_res"] == selected_target_res:
            crf_values.append(s["crf"])
            
    if not crf_values:
        print(f"Warning: No CRF values found for target res {selected_target_res}.")
        return None

    mean_crf = int(np.mean(crf_values))
    
    return {
        "target_resolution": selected_target_res,
        "crf": mean_crf,
        "profile": selected_profile
    }

def main(args):
    # Load the compression "database"
    try:
        with open(args.model_file, 'r') as f:
            models = json.load(f)
    except FileNotFoundError:
        print(f"😢 Error: Model file not found at {args.model_file}")
        print("Please run SN_parameters_emulation.py first.")
        return

    # Select the samples for the target platform and codec
    try:
        samples = models[args.platform][args.codec]
    except KeyError:
        print(f"😢 Error: No model data found for platform='{args.platform}' and codec='{args.codec}' in {args.model_file}")
        return
        
    if not samples:
        print(f"😢 Error: No samples found for {args.platform}/{args.codec}.")
        return

    # Find all videos recursively
    print(f"Finding videos 📼 in {args.input_dir}...")
    videos_to_process = list(Path(args.input_dir).rglob("*.mp4"))
    print(f"Found {len(videos_to_process)} videos 📼. Starting compression 🤖...")

    for video_path in tqdm(videos_to_process, desc="🤖 Compressing videos"):
        orig_meta = utils.get_video_metadata(video_path)
        if not orig_meta:
            print(f"🤔 Could not read metadata for {video_path}, skipping.")
            continue
            
        orig_res_str = orig_meta['resolution_str']
        
        # --- Apply the new LUT logic ---
        # --- MODIFIED LINE: Pass args.platform to the function ---
        params = get_emulation_params(orig_res_str, samples, args.platform)
        
        if not params:
            print(f"🤔 Warning: No compression rule found for {video_path.name} ({orig_res_str}). Skipping.")
            continue
            
        # Prepare output path, preserving directory structure
        relative_path = video_path.relative_to(args.input_dir)
        output_path = Path(args.output_dir) / relative_path
        # Run compression
        utils.encode_video(
            video_path,
            output_path,
            params["target_resolution"],
            params["crf"],
            args.codec, # Use codec from args
            params["profile"],
            "yuv420p" #hardcoded
        )

    print("\n🐝 Compression emulation complete. 🐝")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Emulate social media compression on a set of videos.")
    parser.add_argument("--input-dir", type=str, required=True, help="Directory of videos to compress.")
    parser.add_argument("--output-dir", type=str, required=True, help="Directory to save compressed videos.")
    parser.add_argument("--platform", type=str, required=True, choices=['Youtube', 'Facebook', 'other'], help="Target social platform.")
    parser.add_argument("--codec", type=str, default="libx264", help="Target codec (must match model).")
    parser.add_argument("--model-file", type=str, default="compression_models.json", help="Path to the compression model JSON file.")
    
    args = parser.parse_args()
    main(args)