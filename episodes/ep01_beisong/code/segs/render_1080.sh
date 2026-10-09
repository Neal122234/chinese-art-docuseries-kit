#!/bin/zsh
# 1080p 终版各段渲染排队（画面同第二版，只换分辨率）。
# 用法：nohup ~/claude-projects/china-art/series/segs/render_1080.sh > /dev/null 2>&1 &
#   - 逐段渲染，每段单独占一次 .heavy.lock（段与段之间放锁，别的短任务可以插空）
#   - 输出 segs_1080/（与 segs/ 同名：seg_s01/s2/s3/s4/s5/s6.mp4 + seg_s3/s4_water_mask.mp4），1920×1080 30 fps crf 12
#   - 每段完成后跑 tools/pan_speed_check.py；全部日志追加到 segs_1080/render.log
#   - 可续跑：已完成且帧数、尺寸正确的段跳过；先写 *.part.mp4，校验通过再 mv
#   - 全部完成写 segs_1080/ALL_DONE；有失败的段则写 segs_1080/FAILED（列出段名），重跑本脚本只补失败/缺的段
# 各段渲染器（v2 同一套参数）：bookends/run.py（ss 2）、xishan/seg_s2.py --ss 1、qingming/s3.py（S3_SS=1）、
#   qianli/render.py（ss 1，--mask 同时出水面遮罩）、ru/seg_s5.py（ss 2）
S=~/claude-projects/china-art/series
O=$S/segs_1080
L=$S/.heavy.lock
LOG=$O/render.log
SELF=$S/segs/render_1080.sh
mkdir -p $O

typeset -A NF=(seg_s01 660 seg_s2 2610 seg_s3 2370 seg_s4 2250 seg_s5 1860 seg_s6 450)
typeset -A MASK=(seg_s3 seg_s3_water_mask seg_s4 seg_s4_water_mask)
ORDER=(seg_s01 seg_s2 seg_s3 seg_s4 seg_s5 seg_s6)

ts() { date '+%F %T'; }
probe() {  # 帧数,宽,高（按包计数，不解码）
  [[ -f $1 ]] || { echo "0,0,0"; return; }
  ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets,width,height \
    -of csv=p=0 $1 2>/dev/null | awk -F, '{print $3","$1","$2}'
}
ok_file() { [[ "$(probe $1)" == "$2,1920,1080" ]]; }
seg_ok() {
  local s=$1
  ok_file $O/$s.mp4 ${NF[$s]} || return 1
  [[ -n ${MASK[$s]} ]] && { ok_file $O/${MASK[$s]}.mp4 ${NF[$s]} || return 1; }
  return 0
}
publish() {  # part → 正式文件（已有旧文件先 cp 备份）
  local part=$1 dst=$2
  [[ -f $dst ]] && cp $dst $dst.bak_$(date +%H%M%S)
  mv $part $dst
}

# ---------------- 单段（在锁内执行） ----------------
if [[ $1 == __do ]]; then
  s=$2; n=${NF[$s]}
  set -o pipefail
  cd $S/segs
  P=$O/$s.part.mp4; rm -f $P
  echo "[$(ts)] ▶ $s 开始（$n 帧）"
  case $s in
    seg_s01) python3 bookends/run.py bookends/seg_s01.py $P --res 1080 || exit 1 ;;
    seg_s6)  python3 bookends/run.py bookends/seg_s6.py  $P --res 1080 || exit 1 ;;
    seg_s2)  (cd xishan && python3 seg_s2.py --res 1080 --ss 1 --out $P) || exit 1 ;;
    seg_s3)
      [[ -f qingming/work/fix_tail.todo ]] && { echo "qingming/work/fix_tail.todo 存在（--mask 会改 720 成品），中止"; exit 1; }
      PM=$O/${MASK[$s]}.part.mp4; rm -f $PM
      if ! ok_file $O/$s.mp4 $n; then
        (cd qingming && S3_SS=1 python3 s3.py --res 1080 --render --out $P) || exit 1
      fi
      (cd qingming && S3_SS=1 python3 s3.py --res 1080 --mask --mask_out $PM) || exit 1 ;;
    seg_s4)
      PM=$O/${MASK[$s]}.part.mp4; rm -f $PM
      (cd qianli && python3 render.py $P --res 1080 --mask $PM) || exit 1 ;;
    seg_s5)  (cd ru && python3 seg_s5.py $P --res 1080) || exit 1 ;;
  esac
  if [[ -f $P ]]; then
    ok_file $P $n || { echo "✗ $s 帧数/尺寸不对：$(probe $P)（应为 $n,1920,1080）"; exit 1; }
    publish $P $O/$s.mp4
  fi
  if [[ -n ${MASK[$s]} ]]; then
    PM=$O/${MASK[$s]}.part.mp4
    ok_file $PM $n || { echo "✗ ${MASK[$s]} 帧数/尺寸不对：$(probe $PM)"; exit 1; }
    publish $PM $O/${MASK[$s]}.mp4
  fi
  echo "[$(ts)] $s 渲染完成，速度自检："
  python3 $S/tools/pan_speed_check.py $O/$s.mp4 2>&1 | tee $O/$s.speed.log
  echo "[$(ts)] ✓ $s 完成 $(probe $O/$s.mp4)"
  exit 0
fi

# ---------------- 排队 ----------------
{
  echo "[$(ts)] ==== render_1080 开始（pid $$）===="
  failed=()
  for s in $ORDER; do
    if seg_ok $s; then echo "[$(ts)] = $s 已完成，跳过"; continue; fi
    echo "[$(ts)] … $s 等锁"
    lockf -k $L zsh $SELF __do $s || { failed+=($s); echo "[$(ts)] ✗ $s 失败"; }
  done
  bad=()
  for s in $ORDER; do seg_ok $s || bad+=($s); done
  if (( ${#bad} == 0 )); then
    rm -f $O/FAILED
    { for s in $ORDER; do echo "$s $(probe $O/$s.mp4)"; done
      for m in ${(v)MASK}; do echo "$m $(probe $O/$m.mp4)"; done; echo "done $(ts)"; } > $O/ALL_DONE
    echo "[$(ts)] ==== 全部完成 → $O/ALL_DONE ===="
  else
    echo "${bad[*]}" > $O/FAILED
    echo "[$(ts)] ==== 未完成：${bad[*]}（重跑本脚本续跑）===="
  fi
} >> $LOG 2>&1
