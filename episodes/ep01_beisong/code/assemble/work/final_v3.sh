#!/bin/zsh
# 第三版（配音）整片 720p：须在 heavy 锁内跑。音轨 = out/audio/mix.wav，字幕 = out/subs.srt（按语音对时）
set -e
cd /Users/mr.ni/claude-projects/china-art/series/assemble
python3 assemble.py video --audio ../out/audio/mix.wav --srt ../out/subs.srt --out ../out/pilot_beisong_v3.mp4
echo VIDEO_DONE
ffprobe -v error -show_entries stream=codec_type,duration,nb_frames,sample_rate,width,height -of compact ../out/pilot_beisong_v3.mp4
ffmpeg -nostats -i ../out/pilot_beisong_v3.mp4 -vn -af ebur128=peak=true -f null - 2>&1 | grep -A12 "Summary" | grep -E "I:|Peak:|LRA:"
ffmpeg -v info -i ../out/pilot_beisong_v3.mp4 -vf blackdetect=d=0.05:pix_th=0.10 -an -f null - 2>&1 | grep -c blackdetect | sed 's/^/blackdetect_hits: /' || true
echo ALL_DONE
