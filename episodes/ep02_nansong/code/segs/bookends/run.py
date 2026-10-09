# -*- coding: utf-8 -*-
"""启动器：注册 bookends 的扩展 fx（ink / tone），再按 engine.py 的 CLI 跑。
lockf -k series/.heavy.lock python3 segs/bookends/run.py SEG.py OUT.mp4 [--stills ...] [--res 1080]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), 'lib')
sys.path.insert(0, LIB); sys.path.insert(0, HERE)
import engine as E
import inkfx
inkfx.register()
if __name__ == '__main__':
    try:
        E.main(sys.argv[1:])
    except E.EngineError as e:
        print('ENGINE ERROR:', e, file=sys.stderr); sys.exit(2)
