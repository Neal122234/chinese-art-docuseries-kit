import numpy as np, cv2, json
D='/Users/mr.ni/claude-projects/china-art/series/assets/qingming/'
W,H=38414,1800
src=np.memmap(D+'work/src_raw_38414x1800.rgb',dtype=np.uint8,mode='r',shape=(H,W,3))
ref=cv2.cvtColor(cv2.imread(D+'ref_dpm_hongqiao_1258x500.jpg'),cv2.COLOR_BGR2RGB)
xa,xb,ya,yb=17852,22163,54,1768
crop=cv2.resize(np.ascontiguousarray(src[ya:yb,xa:xb]),(ref.shape[1],ref.shape[0]),interpolation=cv2.INTER_AREA)
b=lambda a: cv2.GaussianBlur(a.astype(np.float32),(0,0),4)
S=b(crop).reshape(-1,3)/255.; R=b(ref).reshape(-1,3)/255.
# work in gamma-ish space; fit affine 3x3 + offset via least squares
X=np.hstack([S,np.ones((len(S),1))])
M,_,_,_=np.linalg.lstsq(X,R,rcond=None)
print('M=\n',M)
out=np.clip(X@M,0,1)
print('rmse before',np.sqrt(((S-R)**2).mean(0)),'after',np.sqrt(((out-R)**2).mean(0)))
print('mean src',S.mean(0)*255,'ref',R.mean(0)*255)
np.save(D+'work/colorM.npy',M)
def apply(a):
    f=a.reshape(-1,3).astype(np.float32)/255.
    f=np.hstack([f,np.ones((len(f),1),np.float32)])@M.astype(np.float32)
    return (np.clip(f,0,1)*255+0.5).astype(np.uint8).reshape(a.shape)
cor=apply(crop)
st=np.vstack([ref,crop,cor])
cv2.imwrite('/private/tmp/claude-501/-Users-mr-ni/8621ade9-43b6-4f6f-85fe-2f04272ab0ab/scratchpad/qm_color.jpg',cv2.cvtColor(st,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,88])
