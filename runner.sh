python SN_parameters_emulation.py \
    --originals-dir sample_videos/non-shared/ \
    --socials-dir sample_videos/shared/ \
    --platform Youtube \
    --codec libx264 \
    --output-model-file compression_models.json


python SN_encoding_emulation.py \
    --input-dir sample_videos/non-shared_NewSet \
    --output-dir sample_videos/emulated \
    --platform Youtube \
    --model-file compression_models.json