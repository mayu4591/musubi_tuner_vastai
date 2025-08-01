#!/bin/bash

CAPTION=""

# 動画ファイルのリストを取得し、各動画にキャプションを追加
# txtファイルを作成し、キャプションを保存(.mp4拡張子を.txtに変更)
find . -type f -name "*.mp4" -printf '%f\n' | while read CLIP; do echo "$CAPTION" > "${CLIP%.*}.txt"; done