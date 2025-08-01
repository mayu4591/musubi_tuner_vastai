#!/bin/bash

## 別
accelerate config

## 断片化対策(効果あるか不明)
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256

# - In which compute environment are you running?: This machine
# - Which type of machine are you using?: No distributed training
# - Do you want to run your training on CPU only (even if a GPU / Apple Silicon / Ascend NPU device is available)?[yes/NO]: NO
# - Do you wish to optimize your script with torch dynamo?[yes/NO]: NO
# - Do you want to use DeepSpeed? [yes/NO]: NO
# - What GPU(s) (by id) should be used for training on this machine as a comma-seperated list? [all]: all
# - Would you like to enable numa efficiency? (Currently only supported on NVIDIA hardware). [yes/NO]: NO
# - Do you wish to use mixed precision?: bf16


# 前処理+学習
export LORA_NAME=xxx

python src/musubi_tuner/cache_latents.py --dataset_config dataset/dataset.toml --vae ckpts/hunyuan-video-t2v-720p/vae/pytorch_model.pt --vae_chunk_size 32 --vae_tiling

python src/musubi_tuner/cache_text_encoder_outputs.py --dataset_config dataset/dataset.toml  --text_encoder1 ckpts/text_encoder --text_encoder2 ckpts/text_encoder_2 --batch_size 16


accelerate launch \
  --num_cpu_threads_per_process 1 \
  src/musubi_tuner/hv_train_network.py \
  --dataset_config dataset/dataset.toml \
  --output_dir loras/${LORA_NAME} \
  --output_name ${LORA_NAME} \
  --dit ckpts/hunyuan-video-t2v-720p/transformers/mp_rank_00_model_states.pt \
  --flash_attn \
  --mixed_precision bf16 \
  --fp8_base \
  --optimizer_type adamw8bit \
  --learning_rate 2e-4 \
  --gradient_checkpointing \
  --max_data_loader_n_workers 2 \
  --persistent_data_loader_workers \
  --network_module networks.lora \
  --network_dim 32 \
  --timestep_sampling shift \
  --discrete_flow_shift 7.0 \
  --max_train_epochs 16 \
  --save_every_n_epochs 1 \
  --seed 42 | tee -a train.log

#python ema_lora.py \
#  --model_dir loras/run01 \
#  --decay 0.9999 \
#  --save_as loras/${LORA_NAME}_ema.safetensors
#
#python src/musubi_tuner/lora_post_hoc_ema.py checkpoint1.safetensors checkpoint2.safetensors checkpoint3.safetensors --output_file merged_lora.safetensors --beta 0.95

python src/musubi_tuner/lora_post_hoc_ema.py \
  loras/$LORA_NAME/*.safetensors \
  --output_file loras/${LORA_NAME}_ema_pwr.safetensors \
  --sigma_rel 0.2

python convert_lora.py \
  --input loras/${LORA_NAME}_ema_pwr.safetensors \
  --output loras/${LORA_NAME}_ema_pwr_comfy.safetensors \
  --target other