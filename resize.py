#!/usr/bin/env python3
"""
videos/*.mp4 → out/* に
  ▸ 1024×1024 正方形
  ▸ 面積 1024² の最適横長  ( width>height , 例 1345×768 )
  ▸ 面積 1024² の最適縦長  ( height>width, 例 768×1345 )
へリサイズ＋黒パディング
"""
import pathlib, json, math, subprocess, shlex, os
import numpy as np
from sklearn.cluster import KMeans              # pip install scikit-learn  :contentReference[oaicite:0]{index=0}

SRC   = pathlib.Path("old")
DST   = pathlib.Path("image");  DST.mkdir(exist_ok=True)
AREA  = 1024**2               # 正方形と同じピクセル数
SHORT_MIN = 640               # 短辺は 640px 未満にしない

# ---------- ffprobe で幅×高さ取得 ----------
meta=[]
for p in SRC.glob("*.mp4"):
    info=json.loads(subprocess.check_output(
        shlex.split(f'ffprobe -v quiet -print_format json -show_streams "{p}"')))               # :contentReference[oaicite:1]{index=1}
    w,h=[s[k] for s in info["streams"] if s["codec_type"]=="video" for k in ("width","height")]
    r=h/w
    meta.append((p,w,h,r))

# ---------- k-means=2 で縦横クラスタ ----------
rat=np.array([[m[3]] for m in meta])
km=KMeans(n_clusters=2,n_init="auto").fit(rat)                                                  # :contentReference[oaicite:2]{index=2}
vert_ratio=max(km.cluster_centers_)[0]   # r>1
hori_ratio=min(km.cluster_centers_)[0]   # r<1
print(f"縦長≈{vert_ratio:.3f}:1  横長≈1:{1/hori_ratio:.3f}")

def target_size(r):
    if abs(r-1)<1e-3:           # 正方形
        return 1024,1024
    # 面積=S²,  r=H/W
    W=math.sqrt(AREA/r) if r>1 else math.sqrt(AREA*r)
    H=AREA/W
    W,H=map(lambda x:int(math.ceil(x/2)*2), (W,H))  # 偶数化 :contentReference[oaicite:3]{index=3}
    # 短辺が 640 未満なら比率維持で拡大
    if min(W,H)<SHORT_MIN:
        scale=SHORT_MIN/min(W,H)
        W=int(math.ceil(W*scale/2)*2); H=int(math.ceil(H*scale/2)*2)
    return W,H

# ---------- 変換 ----------
for p,w,h,r in meta:
    kind = "square" if abs(r-1)<1e-3 else ("vertical" if r>1 else "horizontal")
    tw,th = target_size(vert_ratio if kind=="vertical" else hori_ratio if kind=="horizontal" else 1)
    vf=(f"scale='min({tw},iw)':'min({th},ih)':force_original_aspect_ratio=decrease,"          # :contentReference[oaicite:4]{index=4}
        f"pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2:color=black")                                    # :contentReference[oaicite:5]{index=5}
    out=DST/p.name
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(p),
         '-vf',vf,'-c:v','libx264','-preset','veryfast','-crf','22','-c:a','copy',str(out)]
    subprocess.run(cmd,check=True)
    print(f"{p.name} → {out.name}  ({tw}×{th})")
