#!/usr/bin/env bash
# resize_to_square640.sh
# すべての MP4 を 640×640 に整形（比率維持＋パディング）

SRC_DIR="old"
DST_DIR="image"
mkdir -p "$DST_DIR"

for f in "$SRC_DIR"/*.mp4; do
  ffmpeg -hide_banner -loglevel error -y -i "$f" \
  -vf "scale='if(gte(iw,ih),640,-2)':'if(lt(iw,ih),640,-2)':force_original_aspect_ratio=decrease,\
       pad=640:640:(ow-iw)/2:(oh-ih)/2:color=black" \
  -c:v libx264 -preset veryfast -crf 18 -c:a copy \
  "$DST_DIR/$(basename "$f")"
done
echo "✅  全動画を 640x640 に整形しました → $DST_DIR"
