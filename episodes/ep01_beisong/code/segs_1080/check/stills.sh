#!/bin/zsh
# 1080 静帧检查：每段单独占一次锁，渲 2–4 张 1080 静帧（含展签/雾/遮罩/光效时刻）
S=~/claude-projects/china-art/series
C=$S/segs_1080/check
L=$S/.heavy.lock
seg=${1:-all}
run() { echo "== $1 $(date +%T)"; shift; /usr/bin/time -l lockf -k $L "$@" 2>&1 | grep -E "still|ERROR|Error|Traceback|maximum resident|real|完成|mask" ; }
cd $S/segs
if [[ $seg == all || $seg == s01 ]]; then run s01 python3 bookends/run.py bookends/seg_s01.py $C/s01.mp4 --res 1080 --stills 60,110,330; fi
if [[ $seg == all || $seg == s6 ]]; then run s6 python3 bookends/run.py bookends/seg_s6.py $C/s6.mp4 --res 1080 --stills 200,330; fi
if [[ $seg == all || $seg == s2 ]]; then (cd xishan && run s2 python3 seg_s2.py --res 1080 --ss 1 --stills 240,1170,2010 --out $C/s2.png); fi
if [[ $seg == all || $seg == s3 ]]; then (cd qingming && S3_SS=1 run s3 python3 s3.py --res 1080 --stills 360,1500,2280 --stills_prefix $C/s3); fi
if [[ $seg == all || $seg == s4 ]]; then (cd qianli && run s4 python3 render.py $C/s4.png --res 1080 --stills 120,360,1680,2130); fi
if [[ $seg == all || $seg == s5 ]]; then (cd ru && run s5 python3 seg_s5.py $C/s5.png --res 1080 --stills 300,600,760); fi
echo STILLS_DONE $(date +%T)
