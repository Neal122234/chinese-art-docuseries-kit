import numpy as np, json
W,H=127821,3400
a=np.memmap('shuitu/shuitu_full_127821x3400.rgb',np.uint8,'r',shape=(H,W,3))
runs=[(52992,57536),(58256,62816),(63536,68032),(68752,73328),(74064,78560),(79280,83872),(84576,89072),(89792,94384),(95104,99680),(100416,104960),(105680,110240),(110976,113248)]
out=[]
for s,e in runs:
    x0=s-500; x1=(e+1200 if e==113248 else e+500)
    blk=np.asarray(a[::4, x0:x1]).astype(np.float32).mean(2)   # rows subsampled
    colm=np.median(blk[200:650],axis=0)
    # mounting paper brightness ~ high; silk darker. threshold halfway between local paper and silk
    paper=np.percentile(colm,95); silk=np.percentile(colm,20)
    th=(paper+silk)/2
    d=np.nonzero(colm<th)[0]
    L=x0+d.min(); R=x0+d.max()
    # rows: within [L+200,R-200]
    blk2=np.asarray(a[:, L+300:R-300:8]).astype(np.float32).mean(2)
    rowm=np.median(blk2,axis=1)
    paper_r=np.percentile(rowm,97); silk_r=np.percentile(rowm,30); thr=(paper_r+silk_r)/2
    r=np.nonzero(rowm<thr)[0]
    T=r.min(); B=r.max()
    out.append(dict(x0=int(L),x1=int(R+1),y0=int(T),y1=int(B+1),w=int(R+1-L),h=int(B+1-T)))
    print(s,e,'->',L,R+1,'w',R+1-L,'rows',T,B+1,'h',B+1-T, 'paper %.0f silk %.0f'%(paper,silk))
json.dump(out,open('shuitu/sections_auto.json','w'),indent=1)
