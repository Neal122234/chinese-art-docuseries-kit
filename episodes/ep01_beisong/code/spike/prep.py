import numpy as np, cv2, time
t=time.time()
a=np.load('~/claude-projects/china-art/trailer/assets_v3/xishan/work_full.npy',mmap_mode='r')
# generous crop around painting area to check border
x0,y0,x1,y1=400,3480,10640,23640
out=[]
step=2000
for ys in range(y0,y1,step):
    ye=min(ys+step,y1)
    blk=np.ascontiguousarray(a[ys:ye,x0:x1])
    out.append(cv2.resize(blk,((x1-x0)//2,(ye-ys)//2),interpolation=cv2.INTER_AREA))
ds2=np.concatenate(out,0)
np.save('work_ds2_raw.npy',ds2)
print(ds2.shape,time.time()-t)
s8=cv2.resize(ds2,(ds2.shape[1]//4,ds2.shape[0]//4),interpolation=cv2.INTER_AREA)
cv2.imwrite('raw_s8.png',cv2.cvtColor(s8,cv2.COLOR_RGB2BGR))
# border profiles
g=cv2.cvtColor(s8,cv2.COLOR_RGB2GRAY).astype(float)
print('col means', np.round(g[500:2000].mean(0)[:30]).astype(int), np.round(g[500:2000].mean(0)[-30:]).astype(int))
print('row means', np.round(g[:,200:1000].mean(1)[:30]).astype(int), np.round(g[:,200:1000].mean(1)[-30:]).astype(int))
