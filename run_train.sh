# 前処理+学習
export LORA_NAME=xray

python src/musubi_tuner/cache_latents.py --dataset_config dataset/dataset.toml --vae ckpts/hunyuan-video-t2v-720p/vae/pytorch_model.pt --vae_chunk_size 32 --vae_tiling

python src/musubi_tuner/cache_text_encoder_outputs.py --dataset_config dataset/dataset.toml  --text_encoder1 ckpts/text_encoder --text_encoder2 ckpts/text_encoder_2 --batch_size 16

accelerate launch \
  --num_cpu_threads_per_process 1 \
  src/musubi_tuner/hv_train_network.py \
  --dataset_config dataset/dataset.toml \
  --output_dir loras/${LORA_NAME} \
  --output_name ${LORA_NAME} \
  --dit ckpts/hunyuan-video-t2v-720p/transformers/mp_rank_00_model_states.pt \
  --vae ckpts/hunyuan-video-t2v-720p/vae/pytorch_model.pt \
  --image_encoder ckpts/image_encoder/model.safetensors \
  --text_encoder1 ckpts/text_encoder \
  --text_encoder2 ckpts/text_encoder_2 \
  --flash_attn \
  --mixed_precision bf16 \
  --fp8_base \
  --optimizer_type adamw8bit \
  --learning_rate 1e-3 \
  --gradient_checkpointing \
  --max_data_loader_n_workers 2 \
  --persistent_data_loader_workers \
  --network_module networks.lora \
  --network_dim 32 \
  --timestep_sampling shift \
  --discrete_flow_shift 7.0 \
  --max_train_epochs 16 \
  --save_every_n_epochs 1 \
  --save_last_n_epochs_state 1 \
  --save_state \
  --blocks_to_swap 36 \
  --seed 42 2>&1 | tee -a train.log