"""留白转场用：寒江独钓全貌空绢（s3 同一相机/墙面/底板，去掉船、钓丝、涟漪、展签），t=0 → work/hj_blank.png"""
import os, sys, cv2
sys.path.insert(0, '/Users/mr.ni/claude-projects/china-art/series/ep02_nansong/segs/s3_hanjiang')
sys.path.insert(0, '/Users/mr.ni/claude-projects/china-art/series/lib')
import engine as E
import seg_s3
R = E.Renderer(seg_s3.build(), 720)
fr = R.render(0.0)
cv2.imwrite(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hj_blank.png'), cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
print('ok', fr.shape)
