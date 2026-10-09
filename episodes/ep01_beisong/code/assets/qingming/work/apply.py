import numpy as np, cv2, time
D='/Users/mr.ni/claude-projects/china-art/series/assets/qingming/'
W,H=38414,1800
t=time.time()
src=np.memmap(D+'work/src_raw_38414x1800.rgb',dtype=np.uint8,mode='r',shape=(H,W,3))
dst=np.memmap(D+'qingming_cc_38414x1800.rgb',dtype=np.uint8,mode='w+',shape=(H,W,3))
M=np.load(D+'work/colorM.npy').astype(np.float32)
# build 3D LUT-free direct apply per chunk
for x in range(0,W,2048):
    a=np.ascontiguousarray(src[:,x:x+2048]).astype(np.float32)/255.
    f=a@M[:3]+M[3]
    dst[:,x:x+2048]=(np.clip(f,0,1)*255+0.5).astype(np.uint8)
dst.flush(); print('applied',time.time()-t,flush=True)
pw=4000; ph=round(H*pw/W)
# preview: downscale chunkwise via area resize of full (ok: 207MB)
pv=cv2.resize(np.asarray(dst),(pw,ph),interpolation=cv2.INTER_AREA)
cv2.imwrite(D+'qingming_cc_preview_4000.jpg',cv2.cvtColor(pv,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,90])
pv2=cv2.resize(np.asarray(src),(pw,ph),interpolation=cv2.INTER_AREA)
cv2.imwrite(D+'work/src_preview_4000.jpg',cv2.cvtColor(pv2,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,90])
print('done',pw,ph,time.time()-t,flush=True)
