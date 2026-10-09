import numpy as np, json, sys
from PIL import Image, ImageDraw
W,H=127821,3400
a=np.memmap('shuitu/shuitu_full_127821x3400.rgb',np.uint8,'r',shape=(H,W,3))
S=json.load(open('shuitu/sections_auto.json'))
order=list(range(len(S)))[::-1][1:]
tiles=[]
st=3
for k,i in enumerate(order):
    s=S[i]; x0=s['x0']; y0=s['y0']; x1=x0+1200; y1=y0+1650
    c=np.array(a[y0:y1:st, x0:x1:st]); im=Image.fromarray(c); d=ImageDraw.Draw(im)
    for gx in range((x0//100+1)*100,x1,100):
        X=(gx-x0)/st; d.line([(X,0),(X,im.height)],fill=(255,0,0) if gx%500==0 else (255,150,150)); 
        if gx%500==0: d.text((X+2,2),str(gx),fill=(255,255,0))
    for gy in range((y0//100+1)*100,y1,100):
        Y=(gy-y0)/st; d.line([(0,Y),(im.width,Y)],fill=(255,0,0) if gy%500==0 else (255,150,150)); d.text((2,Y+2),str(gy),fill=(255,255,0))
    d.text((5,im.height-14),'#%d x0=%d'%(k+2,x0),fill=(255,255,255))
    tiles.append(im)
tw,th=tiles[0].size
c=Image.new('RGB',(tw*6+50,th*2+10),'white')
for j,t in enumerate(tiles): c.paste(t,((j%6)*(tw+10),(j//6)*(th+10)))
c.save(sys.argv[1],quality=88); print(c.size)
