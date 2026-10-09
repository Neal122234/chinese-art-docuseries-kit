import numpy as np, cv2, json
a=np.memmap('tage/tage_full_7831x13391.rgb',np.uint8,'r',shape=(13391,7831,3))
X0,Y0,X1,Y1=2550,350,4850,2250
blk=np.asarray(a[Y0:Y1,X0:X1]).astype(np.float32)
g=blk.mean(2); red=blk[...,0]-blk[...,1]
bg=cv2.GaussianBlur(g,(0,0),40); dk=bg-g
m=((dk>14)&(red<12)).astype(np.uint8)
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
m=cv2.dilate(m,np.ones((11,11),np.uint8))
# columns by x projection
colp=m.sum(0)
cols=[];s=None
for x,v in enumerate(colp>40):
    if v and s is None: s=x
    if not v and s is not None:
        if x-s>60: cols.append([s,x])
        s=None
if s is not None: cols.append([s,len(colp)])
cols=cols[::-1]
lines=['宿雨清畿甸','朝陽麗帝城','豐年人樂業','壠上踏歌行']
out=[]
for ci,(c0,c1) in enumerate(cols):
    sub=m[:,c0:c1]; prof=sub.sum(1)>0
    runs=[];s=None
    for y,v in enumerate(prof):
        if v and s is None: s=y
        if not v and s is not None: runs.append([s,y]); s=None
    if s is not None: runs.append([s,len(prof)])
    mr=[r for r in runs if r[1]-r[0]>=12]
    while len(mr)>5:   # merge the pair with the smallest gap
        gaps=[mr[i+1][0]-mr[i][1] for i in range(len(mr)-1)]
        i=int(np.argmin(gaps)); mr[i]=[mr[i][0],mr[i+1][1]]; del mr[i+1]
    chars=[]
    for k,r in enumerate(mr):
        sub2=m[r[0]:r[1],c0:c1]; xs=np.nonzero(sub2.sum(0))[0]
        chars.append(dict(ch=lines[ci][k] if ci<4 and k<5 else '?', box=[int(X0+c0+xs.min()),int(Y0+r[0]),int(xs.max()-xs.min()+1),int(r[1]-r[0])]))
    print('col',ci+1,'x',X0+c0,X0+c1,len(mr),[ (c['ch'],c['box']) for c in chars])
    out.append(dict(line=lines[ci] if ci<4 else '?',x0=int(X0+c0),x1=int(X0+c1),chars=chars))
json.dump(out,open('tage/poem_chars.json','w'),indent=1,ensure_ascii=False)
