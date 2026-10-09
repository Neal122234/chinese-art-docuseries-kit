# 从 work_full.npy (mmap) 裁出画心，按 1/3 和 1/8 生成工作底图
import numpy as np, cv2, time, os
t=time.time()
src=np.load('~/claude-projects/china-art/trailer/assets_v3/xishan/work_full.npy',mmap_mode='r')
x,y,w,h=530,3600,9980,19920
out=os.path.dirname(os.path.abspath(__file__))+'/../work/'
S=3
H3,W3=h//S,w//S
tex=np.zeros((H3,W3,3),np.uint8)
step=1500  # 源行数/块（3 的倍数）
for r0 in range(0,h,step):
    r1=min(h,r0+step)
    blk=np.ascontiguousarray(src[y+r0:y+r1, x:x+w])
    dh=(r1-r0)//S
    tex[r0//S:r0//S+dh]=cv2.resize(blk,(W3,dh),interpolation=cv2.INTER_AREA)
np.save(out+'tex_s3.npy',tex)
cv2.imwrite(out+'tex_s8.jpg',cv2.cvtColor(cv2.resize(tex,(w//8,h//8),interpolation=cv2.INTER_AREA),cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,92])
print(tex.shape,'%.1fs'%(time.time()-t))
