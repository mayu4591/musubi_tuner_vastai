#/usr/bin/env bash
set -euo pipefail

python -m pip install "huggingface_hub[cli]"

cd musubi-tuner

huggingface-cli download tencent/HunyuanVideo --local-dir ./ckpts
cd ./ckpts
huggingface-cli download xtuner/llava-llama-3-8b-v1_1-transformers --local-dir ./llava-llama-3-8b-v1_1-transformers
cd ..
# https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanVideo/refs/heads/main/hyvideo/utils/preprocess_text_encoder_tokenizer_utils.py を実行
wget https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanVideo/refs/heads/main/hyvideo/utils/preprocess_text_encoder_tokenizer_utils.py -O preprocess_text_encoder_tokenizer_utils.py
pip install transformers
python preprocess_text_encoder_tokenizer_utils.py --input_dir ckpts/llava-llama-3-8b-v1_1-transformers --output_dir ckpts/text_encoder
cd ./ckpts
huggingface-cli download openai/clip-vit-large-patch14 --local-dir ./text_encoder_2
cd ..

mkdir ckpts/image_encoder
curl -L -o "./ckpts/image_encoder/model.safetensors" https://huggingface.co/lllyasviel/flux_redux_bfl/resolve/main/image_encoder/model.safetensors
