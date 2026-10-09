#!/bin/zsh
cd "$(dirname $0)"
# Wikimedia 要求 User-Agent 带联系方式；工具包里不写死个人邮箱，跑前 export CONTACT_EMAIL=你的邮箱
UA="china-art-research/1.0 (${CONTACT_EMAIL:?先 export CONTACT_EMAIL（Wikimedia UA 要求联系方式）})"
curl -s -L -m 1800 --retry 3 -A "$UA" -o tage/src_tage_minghuaji_7831x13391.png "https://upload.wikimedia.org/wikipedia/commons/5/5d/%E9%A9%AC%E8%BF%9C%E8%B8%8F%E6%AD%8C%E5%9B%BE%E8%BD%B4.png"
echo "tage $(stat -f %z tage/src_tage_minghuaji_7831x13391.png)"
curl -s -L -m 3600 --retry 3 -A "$UA" -o shuitu/src_shuitu_minghuaji_127821x3400.png "https://upload.wikimedia.org/wikipedia/commons/4/49/%E9%A9%AC%E8%BF%9C%E6%B0%B4%E5%9B%BE%E5%8D%B7.png"
echo "shuitu $(stat -f %z shuitu/src_shuitu_minghuaji_127821x3400.png)"
echo DONE
