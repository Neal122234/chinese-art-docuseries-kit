import numpy as np, cv2
Y='~/claude-projects/china-art/trailer/assets_v3/yeyan/work_listen_16000x3981.rgb'
a=np.memmap(Y,np.uint8,'r',shape=(3981,16000,3))
rows=[]
for r in range(0,3981,500):
    b=np.ascontiguousarray(a[r:r+500]); rows.append(cv2.resize(b,(2000,max(1,b.shape[0]//8)),interpolation=cv2.INTER_AREA))
p=np.concatenate(rows,0)
for x in range(0,2000,125):
    cv2.line(p,(x,0),(x,8),(255,0,0),1); cv2.putText(p,str(x*8//1000),(x+1,18),0,0.35,(255,255,0),1)
cv2.imwrite('review/yeyan_ds8.jpg',cv2.cvtColor(p,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,88])
print(p.shape, p.reshape(-1,3).mean(0), np.median(p.reshape(-1,3),0))
