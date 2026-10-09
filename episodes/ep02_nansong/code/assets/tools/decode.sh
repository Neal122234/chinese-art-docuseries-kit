#!/bin/zsh
cd ~/claude-projects/china-art/series/ep02_nansong/assets
T=tools/pngstream
time $T 8 tage/tage 0 7831 < tage/src_tage_minghuaji_7831x13391.png
time $T 16 shuitu/shuitu 0 127821 < shuitu/src_shuitu_minghuaji_127821x3400.png
ls -la tage shuitu
echo DONE
