# 分层：FAR(天+主峰) / MID(林木坡石、路、驮队) / FG(前景巨石与底边)
# 深度(Depth Anything V2 Small+Base) 给粗分；墨色连通扩展把细松针并入 MID；前景上沿用 DP 沿墨线走
import numpy as np, cv2
W='~/claude-projects/china-art/series/spike/work/'
im=np.load(W+'tex_s8.npy'); H,Wd=im.shape[:2]
L=cv2.cvtColor(im,cv2.COLOR_RGB2GRAY).astype(np.float32)
dS=np.load(W+'depth_Small_1036.npy'); dB=np.load(W+'depth_Base_1400.npy'); dm=0.5*(dS+dB)
v=(np.arange(H)[:,None]/H)*np.ones((1,Wd)); u=np.ones((H,1))*(np.arange(Wd)[None,:]/Wd)

# ---- MID 粗分 + 墨色扩展（松树顶、寺顶、崖面）
mid0=(v>0.6)&(dm>0.27)&~((u<0.1)&(v<0.7))
bg=cv2.GaussianBlur(L,(0,0),25)
ink=(L<bg-10)&(v>0.57)&(v<0.8)
cand=(ink|mid0).astype(np.uint8)
cand=cv2.morphologyEx(cand,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
n,lab=cv2.connectedComponents(cand,connectivity=8)
keep=np.unique(lab[mid0]); keep=keep[keep>0]
mid=np.isin(lab,keep)
mid=cv2.morphologyEx(mid.astype(np.uint8),cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
# 填掉 MID 内部小洞（林间雾缝保留大的）
inv=(1-mid).astype(np.uint8); n2,l2,st,_=cv2.connectedComponentsWithStats(inv,connectivity=4)
for i in range(1,n2):
    if st[i,cv2.CC_STAT_AREA]<400: mid[l2==i]=1
mid=mid.astype(bool)

# ---- FG：DP 沿巨石上沿墨线
fg0=(v>0.6)&(dm>0.62)
y0=np.array([np.argmax(fg0[:,x]) if fg0[:,x].any() else H-1 for x in range(Wd)])
y0=cv2.GaussianBlur(y0.astype(np.float32).reshape(1,-1),(0,0),15).ravel()
Ls=cv2.GaussianBlur(L,(0,0),1.2)
band=34; ys=np.arange(-band,band+1)
C=np.full((len(ys),Wd),1e9,np.float32)
for x in range(Wd):
    yy=np.clip((y0[x]+ys).astype(int),0,H-1)
    C[:,x]=Ls[yy,x]+25*(np.abs(ys)/band)**2
acc=C[:,0].copy(); bp=np.zeros((len(ys),Wd),np.int16)
for x in range(1,Wd):
    best=np.full(len(ys),1e9,np.float32); arg=np.zeros(len(ys),np.int16)
    for d in range(-3,4):
        sh=np.roll(acc,d)+3*abs(d)
        if d>0: sh[:d]=1e9
        if d<0: sh[d:]=1e9
        m=sh<best; best[m]=sh[m]; arg[m]=d
    acc=best+C[:,x]; bp[:,x]=arg
path=np.zeros(Wd,int); k=int(np.argmin(acc))
for x in range(Wd-1,-1,-1):
    path[x]=k; k=k-bp[k,x]
seam=np.clip(y0+ys[path],0,H-1)
seam=cv2.GaussianBlur(seam.astype(np.float32).reshape(1,-1),(0,0),1.0).ravel()
fg=(np.arange(H)[:,None]>=(seam[None,:]-2.5))   # 往上多吃 2.5px，墨线整条归 FG
mid=mid&~fg
# 人工补丁 1：林中寺庙屋顶（墨淡，深度与墨色都没抓到）→ MID
poly=np.array([[1028,1702],[1044,1680],[1062,1668],[1086,1680],[1112,1698],[1142,1716],[1148,1748],[1026,1750]],np.int32)
pm=np.zeros((H,Wd),np.uint8); cv2.fillPoly(pm,[poly],1); mid|=pm.astype(bool)
# FAR 里被 MID/FG 围住的碎块（林间亮崖面）→ MID：先腐蚀断开细连接，只留与画顶相连的 FAR
far=(~mid&~fg).astype(np.uint8)
fe=cv2.erode(far,np.ones((5,5),np.uint8))
n3,l3=cv2.connectedComponents(fe,connectivity=4)
top=np.unique(l3[:5]); top=top[top>0]
mainfar=cv2.dilate(np.isin(l3,top).astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)&far.astype(bool)
mid=mid|(far.astype(bool)&~mainfar&(v>0.55))

lab3=np.zeros((H,Wd),np.uint8); lab3[mid]=1; lab3[fg]=2
np.save(W+'lab3_s8.npy',lab3); np.save(W+'fg_seam_s8.npy',seam)
cols=np.array([[255,120,60],[60,220,90],[230,60,200]],np.float32)
ov=(im.astype(np.float32)*0.62+cols[lab3]*0.38).astype(np.uint8)
lo=slice(int(0.55*H),H)
cv2.imwrite(W+'labels_v1_lower.jpg',cv2.cvtColor(ov[lo],cv2.COLOR_RGB2BGR))
# 近看：巨石上沿与驮队段
z=ov[int(0.8*H):int(0.97*H), int(0.15*Wd):int(0.95*Wd)]
cv2.imwrite(W+'labels_v1_fgedge.jpg',cv2.cvtColor(cv2.resize(z,None,fx=1.5,fy=1.5),cv2.COLOR_RGB2BGR))
z=ov[int(0.58*H):int(0.75*H), int(0.4*Wd):int(1.0*Wd)]
cv2.imwrite(W+'labels_v1_canopy.jpg',cv2.cvtColor(cv2.resize(z,None,fx=1.5,fy=1.5),cv2.COLOR_RGB2BGR))
print('ok', mid.mean(), fg.mean())
