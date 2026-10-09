#!/usr/bin/env bash
# 新机器 / 新环境准备：python venv + 依赖包、ffmpeg 检查、字体与模型的下载提示。
# 用法（在仓库根目录）：
#   scripts/bootstrap.sh                # 建 .venv 并装核心包（渲染 / 总装 / 配音合成 / 读音比对）
#   scripts/bootstrap.sh --asr          # 另装读音核对用的 faster-whisper（+ Apple Silicon 上的 mlx-whisper）
#   scripts/bootstrap.sh --depth        # 另装估深度分层用的 torch + transformers（Depth Anything V2）
#   scripts/bootstrap.sh --fetch-fonts  # 另从 Adobe 官方 GitHub 下载思源宋体 SC（约 139 MB zip），解出 3 个字重到 fonts/
#   scripts/bootstrap.sh --check        # 只检查（python / ffmpeg / 字体，字体目录 = $FONT_DIR 或 fonts/），不建 venv、不装包
# 包清单来自仓库内全部 .py 的 import 统计（2026-09-30）：
#   核心  numpy opencv-python pillow scipy scikit-image numexpr edge-tts pypinyin
#   --asr faster-whisper huggingface_hub（+ mlx-whisper，仅 macOS arm64）
#   --depth torch transformers huggingface_hub
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$KIT/.venv"
FONTS="${FONT_DIR:-$KIT/fonts}"          # 已有字体目录可用 FONT_DIR 指过去
DO_ASR=0; DO_DEPTH=0; DO_FONTS=0; CHECK_ONLY=0
for a in "$@"; do
  case "$a" in
    --asr) DO_ASR=1 ;;
    --depth) DO_DEPTH=1 ;;
    --fetch-fonts) DO_FONTS=1 ;;
    --check) CHECK_ONLY=1 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "未知参数：${a}（--help 看用法）"; exit 2 ;;
  esac
done

ok()   { printf '  [OK]   %s\n' "$*"; }
warn() { printf '  [WARN] %s\n' "$*"; }
miss() { printf '  [MISS] %s\n' "$*"; }
PROBLEMS=0

echo "== 1. Python"
if command -v python3 >/dev/null 2>&1; then
  PYV=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
  if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then ok "python3 $PYV（全部 .py 在 3.9 与 3.14 下 py_compile 通过；原工程实际用 3.14）"
  else miss "python3 $PYV 太旧，需要 ≥ 3.9"; PROBLEMS=1; fi
else
  miss "没有 python3"; PROBLEMS=1
fi

echo "== 2. ffmpeg / ffprobe（全部渲染、总装、配音都靠它）"
for t in ffmpeg ffprobe; do
  if command -v $t >/dev/null 2>&1; then ok "$t: $(command -v $t)"; else miss "$t 未安装（macOS: brew install ffmpeg；Debian/Ubuntu: sudo apt install ffmpeg）"; PROBLEMS=1; fi
done
if command -v ffmpeg >/dev/null 2>&1; then
  ENC=$(ffmpeg -hide_banner -encoders 2>/dev/null || true); FLT=$(ffmpeg -hide_banner -filters 2>/dev/null || true)
  if grep -q libx264 <<<"$ENC"; then ok "ffmpeg 带 libx264"; else miss "ffmpeg 没编 libx264（引擎/总装都用 libx264 出片）"; PROBLEMS=1; fi
  if grep -q ebur128 <<<"$FLT"; then ok "ffmpeg 带 ebur128（响度）"; else warn "ffmpeg 没有 ebur128 滤镜，配乐电平/响度自检会失败"; fi
fi
if command -v lockf >/dev/null 2>&1; then ok "lockf（重活串行锁，macOS 自带）"
elif command -v flock >/dev/null 2>&1; then warn "没有 lockf；Linux 上把文档里的 'lockf -k LOCK cmd' 换成 'flock LOCK cmd'"
else warn "没有 lockf / flock：重活请手动串行，别并行开多个渲染"; fi

echo "== 3. 字体（仓库不带字体文件）"
need_fonts=(SourceHanSerifSC-Regular.otf SourceHanSerifSC-Light.otf SourceHanSerifSC-ExtraLight.otf)
if [[ $DO_FONTS == 1 && $CHECK_ONLY == 0 ]]; then
  mkdir -p "$FONTS"
  ZIP_URL="https://github.com/adobe-fonts/source-han-serif/releases/download/2.003R/09_SourceHanSerifSC.zip"
  TMPZ="$(mktemp -t shs_sc.XXXXXX).zip"
  echo "  下载 ${ZIP_URL}（约 139 MB）..."
  curl -fL --retry 3 -o "$TMPZ" "$ZIP_URL"
  unzip -o -j "$TMPZ" 'OTF/SimplifiedChinese/SourceHanSerifSC-Regular.otf' 'OTF/SimplifiedChinese/SourceHanSerifSC-Light.otf' \
        'OTF/SimplifiedChinese/SourceHanSerifSC-ExtraLight.otf' 'LICENSE.txt' -d "$FONTS" >/dev/null
  rm -f "$TMPZ"
fi
fmiss=0
for f in "${need_fonts[@]}"; do if [[ -f "$FONTS/$f" ]]; then ok "$FONTS/$f"; else miss "$FONTS/$f"; fmiss=1; PROBLEMS=1; fi; done
if [[ $fmiss == 1 ]]; then
  cat <<'TXT'
  思源宋体 Source Han Serif SC（SIL Open Font License 1.1，可免费商用、可随项目分发但本仓库不入库）：
    官方发布页 https://github.com/adobe-fonts/source-han-serif/releases/tag/2.003R
    取 09_SourceHanSerifSC.zip（地区子集 OTF），解出 OTF/SimplifiedChinese/SourceHanSerifSC-{Regular,Light,ExtraLight}.otf
    与 LICENSE.txt 放到仓库 fonts/；或直接 scripts/bootstrap.sh --fetch-fonts 自动完成。
TXT
fi
echo "  （可选）Noto Sans SC（OFL）：https://fonts.google.com/noto/specimen/Noto+Sans+SC"
echo "    下载后把 static/NotoSansSC-{Regular,Medium,Bold,Black}.ttf 装到 ~/Library/Fonts/（代码写死此路径）。"
echo "  封面脚本、幕后片个别卡片用 macOS 系统字体 Songti.ttc / Menlo.ttc / Arial.ttf，非 macOS 需自行替换。"

if [[ $CHECK_ONLY == 1 ]]; then
  echo "== --check 结束（未建 venv、未装包）"; exit $PROBLEMS
fi

echo "== 4. Python venv：$VENV"
[[ -x "$VENV/bin/python" ]] || python3 -m venv "$VENV"
PY="$VENV/bin/python"
"$PY" -m pip install -U pip wheel >/dev/null
CORE=(numpy opencv-python pillow scipy scikit-image numexpr edge-tts pypinyin)
echo "  pip install ${CORE[*]}"
"$PY" -m pip install "${CORE[@]}"
if [[ $DO_ASR == 1 ]]; then
  ASR=(faster-whisper huggingface_hub)
  [[ "$(uname -s)" == Darwin && "$(uname -m)" == arm64 ]] && ASR+=(mlx-whisper)
  echo "  pip install ${ASR[*]}"; "$PY" -m pip install "${ASR[@]}"
fi
if [[ $DO_DEPTH == 1 ]]; then
  echo "  pip install torch transformers huggingface_hub"; "$PY" -m pip install torch transformers huggingface_hub
fi
"$PY" - <<'PYCHK'
import importlib
for m in ['numpy', 'cv2', 'PIL', 'scipy', 'skimage', 'numexpr', 'edge_tts', 'pypinyin']:
    importlib.import_module(m)
print('  [OK]   核心包 import 通过')
PYCHK

echo "== 5. 模型（按需下载；脚本都以 HF_HUB_OFFLINE=1 离线读本地缓存，所以要先下好）"
cat <<TXT
  读音核对（pipeline/build_voice.py asr，需 --asr 装的包）：
    $PY -c "from huggingface_hub import snapshot_download as d; d('Systran/faster-whisper-base')"
    $PY -c "from huggingface_hub import snapshot_download as d; d('mlx-community/whisper-large-v3-turbo')"   # 仅 Apple Silicon
  估深度分层（episodes/ep01_beisong/code/spike/*depth*.py，需 --depth 装的包）：
    $PY -c "from huggingface_hub import snapshot_download as d; [d(f'depth-anything/Depth-Anything-V2-{s}-hf') for s in ('Small','Base')]"
  配音合成 edge-tts 走微软在线服务，需联网，无需下载模型。
TXT

echo "== 6. 建议的环境变量（写进 shell 配置或每次 export）"
cat <<TXT
  export CHINA_ART_ROOT=/path/to/china-art          # 素材与各集成品所在的工程目录（大文件不在本仓库）
  export EP_DIR=\$CHINA_ART_ROOT/series/ep02_nansong  # 当前在做的一集
  export FONT_DIR=$FONTS
  export TTS_PY=$PY
  export ASR_PY=$PY
  # 可选：ENGINE_CACHE（引擎 mip 缓存，缺省 engine/cache/）、BED（配乐）、ANCHORS、VOICE_DIR、ASM_DIR
TXT
[[ $PROBLEMS == 0 ]] && echo "== 完成" || { echo "== 完成，但上面有 [MISS] 项要先处理"; exit 1; }
