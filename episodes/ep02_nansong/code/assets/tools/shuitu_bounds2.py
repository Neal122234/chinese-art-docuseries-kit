import numpy as np, json
W,H=127821,3400
a=np.memmap('shuitu/shuitu_full_127821x3400.rgb',np.uint8,'r',shape=(H,W,3))
S=json.load(open('shuitu/sections_auto.json'))
for s in S:
    blk=np.asarray(a[:, s['x0']+200:s['x1']-200:6]).astype(np.float32).mean(2)
    rowm=np.median(blk,axis=1)
    mid=H//2; silk=np.median(rowm[1000:2500]); paper=np.median(np.r_[rowm[60:200],rowm[3300:3380]])
    th=(silk+paper)/2
    t=mid
    while t>0 and rowm[t-1]<th: t-=1
    b=mid
    while b<H-1 and rowm[b+1]<th: b+=1
    s['y0']=int(t); s['y1']=int(b+1); s['h']=s['y1']-s['y0']
    print(s, 'silk %.0f paper %.0f'%(silk,paper))
json.dump(S,open('shuitu/sections_auto.json','w'),indent=1)
