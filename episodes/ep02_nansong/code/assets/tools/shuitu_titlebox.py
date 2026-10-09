import numpy as np, json, cv2
W,H=127821,3400
a=np.memmap('shuitu/shuitu_full_127821x3400.rgb',np.uint8,'r',shape=(H,W,3))
S=json.load(open('shuitu/sections_auto.json'))
names=['(残，无题)','洞庭風細','層波疊浪','寒塘清淺','長江萬頃','黃河逆流','秋水迴波','雲生滄海','湖光瀲灔','雲舒浪卷','曉日烘山','細浪漂漂']
order=list(range(len(S)))[::-1]
for k,i in enumerate(order):
    s=S[i]; s['order']=k+1; s['name']=names[k]
    if k==0: continue
    X0=s['x0']+150; Y0=s['y0']; X1=s['x0']+1250; Y1=s['y0']+1350
    blk=np.asarray(a[Y0:Y1,X0:X1]).astype(np.float32)
    g=blk.mean(2); red=blk[...,0]-blk[...,1]
    bg=cv2.GaussianBlur(g,(0,0),40)
    dk=(bg-g)
    m=((dk>22)&(red<14)).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    m=cv2.dilate(m,np.ones((9,9),np.uint8))
    n,lab,st,cen=cv2.connectedComponentsWithStats(m)
    # keep big components (glyph parts)
    keep=[j for j in range(1,n) if st[j,4]>1500]
    if not keep: print(k+1,'none'); continue
    # column: take x-center weighted; cluster by x near the heaviest
    xs=np.array([cen[j,0] for j in keep]); ws=np.array([st[j,4] for j in keep])
    xc=np.average(xs,weights=ws**2)
    col=[j for j in keep if abs(cen[j,0]-xc)<150]
    x_min=min(st[j,0] for j in col); x_max=max(st[j,0]+st[j,2] for j in col)
    y_min=min(st[j,1] for j in col); y_max=max(st[j,1]+st[j,3] for j in col)
    # char split by row projection within column box
    sub=m[y_min:y_max, x_min:x_max]; prof=sub.sum(1)>0
    runs=[];st0=None
    for yy,v in enumerate(prof):
        if v and st0 is None: st0=yy
        if (not v) and st0 is not None: runs.append([st0,yy]); st0=None
    if st0 is not None: runs.append([st0,len(prof)])
    # merge tiny gaps
    mr=[]
    for r in runs:
        if mr and r[0]-mr[-1][1]<18: mr[-1][1]=r[1]
        else: mr.append(r)
    s['title_box']=[int(X0+x_min),int(Y0+y_min),int(x_max-x_min),int(y_max-y_min)]
    s['title_chars_y']=[[int(Y0+y_min+r[0]),int(Y0+y_min+r[1])] for r in mr]
    print(k+1,names[k],'box',s['title_box'],'chars',len(mr),s['title_chars_y'])
json.dump(S,open('shuitu/sections_auto.json','w'),indent=1,ensure_ascii=False)
