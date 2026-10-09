#!/bin/zsh
# 【工具包说明】一次锁内跑完：配音混音（build_voice.py mix）→ 整片出片 + 自检（final.sh）。以第二集·南宋 work/run_v2_all.sh 为准。
# 输入：$EP_DIR/assemble/work/music_mix.wav（先跑 python3 pipeline/assemble.py audio 生成）、配音 timing；输出：$EP_DIR/out/audio/*.wav、成片（见 final.sh）。
# 环境变量：CHINA_ART_ROOT、EP_DIR（缺省本机 series/ep02_nansong），其余透传给 final.sh；不设即本机原路径。
# 跑法：nohup lockf -k $CHINA_ART_ROOT/series/.heavy.lock pipeline/run_all.sh > final.log 2>&1 &
set -e
PIPE=${0:A:h}
: ${CHINA_ART_ROOT:=~/claude-projects/china-art}
: ${EP_DIR:=$CHINA_ART_ROOT/series/ep02_nansong}
export CHINA_ART_ROOT EP_DIR
python3 $PIPE/build_voice.py mix $EP_DIR/assemble/work/music_mix.wav
echo MIX_DONE $(date)
$PIPE/final.sh
