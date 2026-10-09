import numpy as np, json, cv2
W,H=127821,3400
a=np.memmap('shuitu/shuitu_full_127821x3400.rgb',np.uint8,'r',shape=(H,W,3))
S=json.load(open('shuitu/sections_auto.json'))
for s in sorted(S,key=lambda t:t['order']):
    x0,x1,y0,y1=s['x0']+300,s['x1']-60,s['y0']+30,s['y1']-30
    ds=4
    g=np.asarray(a[y0:y1:ds,x0:x1:ds]).astype(np.float32)
    red=g[...,0]-g[...,1]; g=g.mean(2)
    dog=cv2.GaussianBlur(g,(0,0),8)-cv2.GaussianBlur(g,(0,0),1.2)
    m=(dog>6)&(red<12)
    rowd=cv2.GaussianBlur(m.mean(1).astype(np.float32)[:,None],(0,0),10)[:,0]
    base=np.percentile(rowd[:len(rowd)//5],50)
    thr=base+0.3*(rowd.max()-base)
    rr=np.nonzero(rowd>thr)[0]
    s['water_y0']=int(y0+rr.min()*ds)
    prof=' '.join('%.2f'%v for v in rowd[::max(1,len(rowd)//12)])
    print(s['order'],s['name'],'water_y0',s['water_y0'],'| rowd',prof)
json.dump(S,open('shuitu/sections_auto.json','w'),indent=1,ensure_ascii=False)
