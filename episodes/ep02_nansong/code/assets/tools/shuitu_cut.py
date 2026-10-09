import numpy as np, json, cv2, os
W,H=127821,3400
a=np.memmap('shuitu/shuitu_full_127821x3400.rgb',np.uint8,'r',shape=(H,W,3))
S=json.load(open('shuitu/sections_auto.json'))
os.makedirs('shuitu/sections',exist_ok=True)
slug={1:'01_canduan',2:'02_dongting_fengxi',3:'03_cengbo_dielang',4:'04_hantang_qingqian',5:'05_changjiang_wanqing',6:'06_huanghe_niliu',7:'07_qiushui_huibo',8:'08_yunsheng_canghai',9:'09_huguang_lianyan',10:'10_yunshu_langjuan',11:'11_xiaori_hongshan',12:'12_xilang_piaopiao'}
for s in sorted(S,key=lambda t:t['order']):
    x0,x1,y0,y1=s['x0'],s['x1'],s['y0'],s['y1']
    blk=np.ascontiguousarray(a[y0:y1,x0:x1])
    fn='shuitu/sections/%s_%dx%d.rgb'%(slug[s['order']],x1-x0,y1-y0)
    blk.tofile(fn)
    pv=cv2.resize(blk,((x1-x0)//4,(y1-y0)//4),interpolation=cv2.INTER_AREA)
    cv2.imwrite(fn.replace('.rgb','_preview_ds4.jpg'),pv[...,::-1],[cv2.IMWRITE_JPEG_QUALITY,88])
    s['file']=fn; print(fn)
json.dump(S,open('shuitu/sections_auto.json','w'),indent=1,ensure_ascii=False)
