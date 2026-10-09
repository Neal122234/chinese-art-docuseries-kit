import numpy as np, cv2
D='/Users/mr.ni/claude-projects/china-art/series/assets/qingming/'
W,H=38414,1800
src=np.memmap(D+'work/src_raw_38414x1800.rgb',dtype=np.uint8,mode='r',shape=(H,W,3))
ref=cv2.cvtColor(cv2.imread(D+'ref_dpm_hongqiao_1258x500.jpg'),cv2.COLOR_BGR2RGB)
rg=cv2.cvtColor(ref,cv2.COLOR_RGB2GRAY).astype(np.float32)
x0,x1=14000,24000
reg=np.ascontiguousarray(src[:,x0:x1])
best=None
for th in range(440,560,4):   # template height in scaled src space  -> test scales
    s=th/ref.shape[0]         # ref scale factor
    sc=500/1800               # scale src to 500 high first
    R=cv2.resize(reg,(int((x1-x0)*sc),500),interpolation=cv2.INTER_AREA)
    rg2=cv2.resize(rg,(int(ref.shape[1]*s),th),interpolation=cv2.INTER_AREA)
    Rg=cv2.cvtColor(R,cv2.COLOR_RGB2GRAY).astype(np.float32)
    if rg2.shape[0]>Rg.shape[0]: continue
    m=cv2.matchTemplate(Rg,rg2,cv2.TM_CCOEFF_NORMED); _,mv,_,ml=cv2.minMaxLoc(m)
    if best is None or mv>best[0]: best=(mv,th,ml)
print(best)
mv,th,(mx,my)=best
sc=500/1800
# ref pixel (u,v) -> src full coords
fx=lambda u: x0+(mx+u*th/500)/sc
fy=lambda v: (my+v*th/500)/sc
print('ref box in src full: x %.0f-%.0f  y %.0f-%.0f'%(fx(0),fx(ref.shape[1]),fy(0),fy(ref.shape[0])))
np.save(D+'work/align.npy',np.array([x0,mx,my,th]))
