#!/bin/zsh
# 第二版"全片不用雾"：s2 去雾纱/宫阙雾/田埂雾带、s1 去松间云带。只重渲有雾的帧段，拼回原段（其余帧不变）。
# 须在 heavy 锁内跑：nohup lockf -k ../../.heavy.lock ./rerender_nofog_v2.sh > rerender_nofog_v2.log 2>&1 &
set -e
cd ~/claude-projects/china-art/series/ep02_nansong/segs
W=work_nofog_v2; mkdir -p $W
echo "start $(date)"
# s1：瀑布近景 段内帧 1047–1206（全局 41.9–47.2）
(cd s1_wanhe && python3 seg_s1.py --frames 1047:1207 --out ../$W/s1_b.mp4)
# s2：全貌→题诗 段内帧 378–471（全局 61.6–64.73）；下降→田埂→拖枝柳→拉回 段内帧 816–1589（全局 76.2–102.0）
(cd s2_tage && python3 seg_s2.py --frames 378:472 --out ../$W/s2_a.mp4)
(cd s2_tage && python3 seg_s2.py --frames 816:1590 --out ../$W/s2_b.mp4)
echo RENDER_DONE $(date)
# 拼回（原段帧 + 新帧，crf 12 同原段）
ffmpeg -v error -y -i seg_s1_v2_cloud.mp4 -i $W/s1_b.mp4 -filter_complex \
 "[0:v]trim=start_frame=0:end_frame=1047,setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];[0:v]trim=start_frame=1207,setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1[v]" \
 -map "[v]" -c:v libx264 -preset medium -crf 12 -pix_fmt yuv420p -r 30 -movflags +faststart $W/seg_s1_new.mp4
ffmpeg -v error -y -i seg_s2_v1_fog.mp4 -i $W/s2_a.mp4 -i $W/s2_b.mp4 -filter_complex \
 "[0:v]trim=start_frame=0:end_frame=378,setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];[0:v]trim=start_frame=472:end_frame=816,setpts=PTS-STARTPTS[c];[2:v]setpts=PTS-STARTPTS[d];[0:v]trim=start_frame=1590,setpts=PTS-STARTPTS[e];[a][b][c][d][e]concat=n=5:v=1[v]" \
 -map "[v]" -c:v libx264 -preset medium -crf 12 -pix_fmt yuv420p -r 30 -movflags +faststart $W/seg_s2_new.mp4
for f in $W/seg_s1_new.mp4 $W/seg_s2_new.mp4; do
  echo "$f frames: $(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 $f)"
done
n1=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 $W/seg_s1_new.mp4)
n2=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 $W/seg_s2_new.mp4)
[[ $n1 == 1470 && $n2 == 2040 ]] || { echo FRAMECOUNT_BAD; exit 1; }
mv $W/seg_s1_new.mp4 seg_s1.mp4
mv $W/seg_s2_new.mp4 seg_s2.mp4
python3 ../../tools/pan_speed_check.py seg_s1.mp4 || true
python3 ../../tools/pan_speed_check.py seg_s2.mp4 || true
echo ALL_DONE $(date)
