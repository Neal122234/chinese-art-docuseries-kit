import numpy as np, cv2, sys
W,H=38414,1800
a=np.memmap('/Users/mr.ni/claude-projects/china-art/series/assets/qingming/qingming_cc_38414x1800.rgb',dtype=np.uint8,mode='r',shape=(H,W,3))
x0,x1,y0,y1,ds,out=int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),float(sys.argv[5]),sys.argv[6]
c=np.ascontiguousarray(a[y0:y1,x0:x1])
if ds!=1: c=cv2.resize(c,(int((x1-x0)/ds),int((y1-y0)/ds)),interpolation=cv2.INTER_AREA)
# grid every 100 full px (labels every 500)
g=c.copy(); 
for X in range((x0//100+1)*100,x1,100):
    px=int((X-x0)/ds); col=(255,255,0) if X%500==0 else (120,120,0)
    if X%500==0: cv2.putText(g,str(X),(px+2,14),cv2.FONT_HERSHEY_SIMPLEX,0.4,(255,255,0),1); g[:, px]=col
for Y in range((y0//100+1)*100,y1,100):
    py=int((Y-y0)/ds)
    if Y%500==0: g[py,:]=(255,255,0); cv2.putText(g,str(Y),(2,py-2),cv2.FONT_HERSHEY_SIMPLEX,0.4,(255,255,0),1)
cv2.imwrite(out,cv2.cvtColor(g,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,88])
