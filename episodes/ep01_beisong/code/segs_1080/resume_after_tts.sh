#!/bin/zsh
S=~/claude-projects/china-art/series
until [[ -f $S/voice/local/SHORTLIST.md ]]; do echo "$(date '+%T') 等 SHORTLIST.md（TTS 试听优先）" >> $S/segs_1080/wait.log; sleep 60; done
echo "$(date '+%F %T') SHORTLIST 出现，续跑 1080" >> $S/segs_1080/wait.log
rm -f $S/segs_1080/PAUSED.txt
exec zsh $S/segs/render_1080.sh
