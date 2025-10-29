# Social Media Compression Emulation Framework

This framework provides a two-phase system to improve deepfake's detectors performance when tested on video shared on social networks, by emulating social network's re-compression and resizing artifacts.

1.  **Parameter Estimation Module (`SN_parameters_emulation.py`):** Compares a set of original videos to their counterparts downloaded from a social platform (e.g., Youtube, Facebook). It determines the Constant Rate Factor (CRF) and resolution changes, saving these findings as a "database" in a JSON file.
2.  **Social Network Encoding Emulation Module (`SN_encoding_emulation.py`):** Uses the generated JSON database to apply the *same* compression artifacts to a new, broader set of videos, creating a realistic training set for analysis.

## 📦 Requirements

You must have the `ffmpeg` command-line tool installed on your system check this [link](https://www.ffmpeg.org/download.html). The Python dependencies can be installed via pip:

```bash
pip install ffmpeg-python numpy pandas tqdm
```

## ⚙️ Core Scripts

  * `video_utils.py`: A shared helper module for all low-level `ffmpeg` and `ffprobe` operations (getting metadata, encoding videos).
  * `SN_parameters_emulation.py`: **Part 1.** The analysis script that generates the compression model.
  * `SN_encoding_emulation.py`: **Part 2.** The emulation script that applies the compression model to new videos.
  * `compression_models.json`: The output of the analyzer and input for the emulator. This file stores the "database" of compression samples.

## 🚀 Workflow & Usage

The process is a two-step workflow. 

### Step 1: Analyze & Create the Model

First, use `SN_parameters_emulation.py` to compare your source videos against the versions downloaded from a social platform. The script will find video pairs by matching filenames within the specified directories.

It works by:

1.  Finding pairs (e.g., `originals/FaceSwap/.../001.mp4` and `social/Youtube/.../001.mp4`).
2.  For each pair, it gets the metadata (resolution, bitrate) of the social video.
3.  It then re-encodes the *original* video multiple times (`--crf-min` to `--crf-max`) to find the CRF value that produces a bitrate just below the social video's bitrate.
4.  It saves all findings (original resolution, target resolution, CRF) as a list of samples in the `compression_models.json` file.

**Example Command:**

```bash
python SN_parameters_emulation.py \
    --originals-dir sample_videos/non-shared/ \
    --socials-dir sample_videos/shared/ \
    --platform Youtube \
    --codec libx264 \
    --output-model-file compression_models.json
```

  * `--originals-dir`: The base directory containing your original, high-quality videos (e.g., `/media/SSD_new/FaceForensics++/manipulated_sequences`).
  * `--socials-dir`: The base directory containing the same videos downloaded from the social platform (e.g., `/media/ff++_shared/FaceForensics++_shared/`).

You can run this command multiple times for different platforms (e.g., once for `Youtube`, once for `Facebook`) to append all samples to the same JSON file.

### Step 2: Emulate Compression on New Videos

Second, use `SN_encoding_emulation.py` to apply the learned compression parameters to a new, larger dataset of videos.

It works by:

1.  Loading all samples for the specified platform from `compression_models.json`.
2.  For each new video, it finds the **closest matching input resolution** from the samples.
3.  It identifies the **target output resolution** associated with that best match.
4.  It **averages the CRF** of *all* samples in the database that share that same target output resolution.
5.  It re-encodes the new video using the determined target resolution, average CRF, and correct profile (`high` for Youtube, `main` for others).

**Example Command:**

```bash
python SN_encoding_emulation.py \
    --input-dir sample_videos/non-shared_NewSet \
    --output-dir sample_videos/emulated \
    --platform Youtube \
    --model-file compression_models.json
```

  * `--input-dir`: The directory containing all the new videos you want to process.
  * `--output-dir`: The destination where the compressed videos will be saved, mirroring the input directory structure.
  * `--platform`: The target platform to emulate (e.g., `Youtube`, `Facebook`). This determines which samples to use and which profile (`high`/`main`) to apply.

### Run everything all at once
Modify and run runner.sh

```
bash runner.sh
```

## Cite

```
@inproceedings{montibeller2025bridging,
  title={Bridging the Gap: A Framework for Real-World Video Deepfake Detection via Social Network Compression Emulation},
  author={Montibeller, Andrea and Shullani, Dasara and Baracchi, Daniele and Piva, Alessandro and Boato, Giulia},
  booktitle={Proceedings of the 1st on Deepfake Forensics Workshop: Detection, Attribution, Recognition, and Adversarial Challenges in the Era of AI-Generated Media},
  pages={29--36},
  year={2025}
}
```
