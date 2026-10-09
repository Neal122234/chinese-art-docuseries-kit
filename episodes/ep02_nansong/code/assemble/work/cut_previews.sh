#!/bin/zsh
# 从成片剪各转场 ≤10 s 预览 → out/preview/trans_*.mp4
cd /Users/mr.ni/claude-projects/china-art/series/ep02_nansong/out
V=ep02_nansong_v1.mp4
for spec in fog:47:10 liubai:107:10 ripple:165:9 surge:213:8 crack:245:8; do
  n=${spec%%:*}; r=${spec#*:}; s=${r%%:*}; d=${r#*:}
  ffmpeg -v error -y -ss $s -i $V -t $d -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart preview/trans_$n.mp4
  echo "preview/trans_$n.mp4 $s+$d"
done
