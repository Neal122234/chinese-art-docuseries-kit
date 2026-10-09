# -*- coding: utf-8 -*-
"""单线程版启动器（机器忙、锁排长队时用）：cv2 单线程 + ffmpeg 单线程，峰值 <1 GB、只占一个核。"""
import os, sys, subprocess
import cv2
cv2.setNumThreads(1)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run  # noqa: 注册 fx、设置路径
import engine as E
_Popen = subprocess.Popen
def _popen1(cmd, *a, **k):
    if cmd and cmd[0] == 'ffmpeg' and '-threads' not in cmd:
        i = cmd.index('libx264'); cmd = cmd[:i + 1] + ['-threads', '1'] + cmd[i + 1:]
    return _Popen(cmd, *a, **k)
E.subprocess.Popen = _popen1
if __name__ == '__main__':
    try:
        E.main(sys.argv[1:])
    except E.EngineError as e:
        print('ENGINE ERROR:', e, file=sys.stderr); sys.exit(2)
