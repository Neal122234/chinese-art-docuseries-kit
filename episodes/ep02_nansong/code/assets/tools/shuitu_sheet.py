import numpy as np, json, sys
from PIL import Image, ImageDraw
W,H=127821,3400
a=np.memmap('shuitu/shuitu_full_127821x3400.rgb',np.uint8,'r',shape=(H,W,3))
S=json.load(open('shuitu/sections_auto.json'))
order=list(range(len(S)))[::-1]   # scroll order: rightmost first
OW=760
tiles=[]
for k,i in enumerate(order):
    s=S[i]; x0,x1,y0,y1=s['x0']-60,s['x1']+60,s['y0']-60,s['y1']+60
    st=4
    c=np.array(a[y0:y1:st, x0:x1:st]); im=Image.fromarray(c)
    sc=OW/(x1-x0); im=im.resize((OW,int((y1-y0)*sc)),Image.LANCZOS)
    d=ImageDraw.Draw(im)
    for gx in range((x0//500+1)*500,x1,500):
        X=(gx-x0)*sc; d.line([(X,0),(X,im.height)],fill=(255,0,0)); d.text((X+2,2),str(gx),fill=(255,255,0))
    for gy in range((y0//500+1)*500,y1,500):
        Y=(gy-y0)*sc; d.line([(0,Y),(im.width,Y)],fill=(255,0,0)); d.text((2,Y+2),str(gy),fill=(255,255,0))
    d.text((OW-60,im.height-14),'#%d'%(k+1),fill=(255,255,255))
    tiles.append(im)
for part in range(2):
    ts=tiles[part*6:(part+1)*6]
    h=max(t.height for t in ts)
    c=Image.new('RGB',(OW*3+20,(h+10)*2),'white')
    for j,t in enumerate(ts): c.paste(t,((j%3)*(OW+10),(j//3)*(h+10)))
    c.save(sys.argv[1]+'_%d.jpg'%part,quality=88)
