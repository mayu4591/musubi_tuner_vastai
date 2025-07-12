#!/bin/bash
set -euo pipefail

cd /workspace

# musubi用の仮想環境有効化
sudo apt update
sudo apt upgrade -y

sudo apt install -y python3.12-venv build-essential
mkdir -p /opt/environments/python/
python3.12 -m venv /opt/environments/python/musubi-tuner/
source /opt/environments/python/musubi-tuner/bin/activate

# torchのインストール
pip uninstall -y torch torchvision torchaudio xformers
pip install -U --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128

# musubi_tunerのインストール
if [ ! -d musubi-tuner ]; then
  git clone https://github.com/kohya-ss/musubi-tuner
fi

cd musubi-tuner
pip install -e .

cd /workspace
if [ ! -d musubi_tuner_vastai ]; then
  git clone https://github.com/mayu4591/musubi_tuner_vastai.git
fi

# 並列でモデルダウンロード
nohup bash musubi_tuner_vastai/download_models.sh >> /workspace/download.log 2>&1 &

# Flash-Attention 3 のインストール
cd /workspace
if [ ! -d flash-attention ]; then
  git clone https://github.com/Dao-AILab/flash-attention
fi
cd flash-attention
export FLASH_ATTN_CUDA_ARCHS="120"        # 5090 = sm_120
python setup.py install

# resize.pyの依存関係をインストール
pip install scikit-learn