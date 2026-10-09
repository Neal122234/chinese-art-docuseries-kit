#!/bin/zsh
set -e
cd /Users/mr.ni/claude-projects/china-art/series/assemble
python3 ../tools/pan_speed_check.py ../out/pilot_beisong_v2.mp4 --min_run 0.01 > work/pancheck_v2_detail.log 2>&1 || true
echo PAN_DONE
P=../out/北宋_试做章节_v2_手机.mp4
ffmpeg -v error -y -i ../out/pilot_beisong_v2.mp4 -vf scale=854:480:flags=lanczos -c:v libx264 -preset slow -b:v 640k -pass 1 -passlogfile work/p2 -an -f mp4 /dev/null
ffmpeg -v error -y -i ../out/pilot_beisong_v2.mp4 -vf scale=854:480:flags=lanczos -c:v libx264 -preset slow -b:v 640k -pass 2 -passlogfile work/p2 -pix_fmt yuv420p -profile:v high -c:a aac -b:a 96k -ar 48000 -movflags +faststart $P
ls -la $P
ffprobe -v error -show_entries stream=codec_type,width,height,duration -of compact $P
echo PHONE_DONE
