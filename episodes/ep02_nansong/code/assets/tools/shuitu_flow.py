import numpy as np, json, cv2
W,H=127821,3400
a=np.memmap('shuitu/shuitu_full_127821x3400.rgb',np.uint8,'r',shape=(H,W,3))
S=json.load(open('shuitu/sections_auto.json'))
S[0]  # leftmost = #12
for s in S:
    if s['order']==11:
        s['title_box']=[58930,555,205,830]; s['title_chars_y']=[[555,705],[790,905],[1000,1160],[1250,1385]]
for s in sorted(S,key=lambda t:t['order']):
    x0,x1,y0,y1=s['x0']+40,s['x1']-40,s['y0']+40,s['y1']-40
    ds=2
    g=np.asarray(a[y0:y1:ds,x0:x1:ds]).astype(np.float32).mean(2)
    bg=cv2.GaussianBlur(g,(0,0),25); dk=np.clip(bg-g,0,None)
    # line density per row (ink edges)
    lines=(dk>10).astype(np.float32)
    rowd=cv2.GaussianBlur(lines.mean(1)[:,None],(0,0),20)[:,0]
    thr=max(0.02, 0.25*rowd.max())
    rr=np.nonzero(rowd>thr)[0]
    wy0=y0+rr.min()*ds if len(rr) else None
    # structure tensor on water area
    gx=cv2.Sobel(dk,cv2.CV_32F,1,0,ksize=5); gy=cv2.Sobel(dk,cv2.CV_32F,0,1,ksize=5)
    sl=slice(rr.min(),None)
    Jxx=(gx[sl]**2).mean(); Jyy=(gy[sl]**2).mean(); Jxy=(gx[sl]*gy[sl]).mean()
    # dominant gradient angle; line direction perpendicular
    th=0.5*np.degrees(np.arctan2(2*Jxy,Jxx-Jyy)); line_ang=th+90
    lam1=0.5*(Jxx+Jyy+np.sqrt((Jxx-Jyy)**2+4*Jxy**2)); lam2=0.5*(Jxx+Jyy-np.sqrt((Jxx-Jyy)**2+4*Jxy**2))
    coh=(lam1-lam2)/(lam1+lam2+1e-6)
    # ink coverage in water zone
    cov=lines[sl].mean()
    s['water_y0']=int(wy0); s['line_angle_deg']=round(float(((line_ang+90)%180)-90),1); s['coherence']=round(float(coh),2); s['ink_cov']=round(float(cov),3)
    print(s['order'],s['name'],'x',s['x0'],s['x1'],'y',s['y0'],s['y1'],'water from y',wy0,'line angle %.1f coh %.2f cov %.3f'%(s['line_angle_deg'],coh,cov))
json.dump(S,open('shuitu/sections_auto.json','w'),indent=1,ensure_ascii=False)
