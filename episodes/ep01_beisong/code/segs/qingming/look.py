import numpy as np, cv2, sys
A = np.memmap('~/claude-projects/china-art/series/assets/qingming/qingming_cc_38414x1800.rgb', dtype=np.uint8, mode='r', shape=(1800,38414,3))
def crop(name, x0,y0,x1,y1, maxw=1600, grid=None):
    b = np.ascontiguousarray(A[y0:y1, x0:x1])
    f = min(1.0, maxw/(x1-x0))
    im = cv2.resize(b, (int((x1-x0)*f), int((y1-y0)*f)), interpolation=cv2.INTER_AREA)
    im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)
    if grid:
        for gx in range((x0//grid+1)*grid, x1, grid):
            X=int((gx-x0)*f); cv2.line(im,(X,0),(X,im.shape[0]),(0,0,255),1); cv2.putText(im,str(gx),(X+2,14),0,0.4,(0,0,255),1)
        for gy in range((y0//grid+1)*grid, y1, grid):
            Y=int((gy-y0)*f); cv2.line(im,(0,Y),(im.shape[1],Y),(255,0,0),1); cv2.putText(im,str(gy),(2,Y-2),0,0.4,(255,0,0),1)
    cv2.imwrite('look/'+name+'.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 88])
for a in sys.argv[1:]:
    p=a.split(','); crop(p[0], *map(int,p[1:5]), maxw=int(p[5]) if len(p)>5 else 1600, grid=int(p[6]) if len(p)>6 else None)
