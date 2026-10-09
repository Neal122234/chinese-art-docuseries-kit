#!/bin/zsh
# 等配音版出片（out/VOICE_DONE 出现）后再启动 1080 排队渲染；心跳写 segs_1080/wait.log
S=~/claude-projects/china-art/series
until [[ -f $S/out/VOICE_DONE ]]; do echo "$(date '+%T') 等 VOICE_DONE"; sleep 30; done
echo "$(date '+%F %T') VOICE_DONE 出现，启动 render_1080.sh"
exec zsh $S/segs/render_1080.sh
