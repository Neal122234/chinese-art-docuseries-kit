# Depth Anything V2 (small/base, 本地 HF 缓存) 对画心出相对深度（值越大越近）
import numpy as np, cv2, torch, time, sys, os
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation
os.environ['HF_HUB_OFFLINE']='1'
W=os.path.dirname(os.path.abspath(__file__))+'/../work/'
img=Image.open(W+'tex_s8.jpg').convert('RGB')   # 1247x2490
dev='mps' if torch.backends.mps.is_available() else 'cpu'
for name,H in [('Small',1036),('Base',1036),('Base',1400)]:
    t=time.time()
    rid=f'depth-anything/Depth-Anything-V2-{name}-hf'
    proc=AutoImageProcessor.from_pretrained(rid,local_files_only=True)
    model=AutoModelForDepthEstimation.from_pretrained(rid,local_files_only=True).to(dev).eval()
    Wd=(H//2)//14*14
    inp=proc(images=img,return_tensors='pt',size={'height':H,'width':Wd},keep_aspect_ratio=False,ensure_multiple_of=14,do_resize=True)
    with torch.no_grad():
        d=model(pixel_values=inp['pixel_values'].to(dev)).predicted_depth[0].float().cpu().numpy()
    d=cv2.resize(d,img.size,interpolation=cv2.INTER_CUBIC)
    d=(d-d.min())/(d.max()-d.min())
    np.save(W+f'depth_{name}_{H}.npy',d.astype(np.float32))
    vis=cv2.applyColorMap((d*255).astype(np.uint8),cv2.COLORMAP_INFERNO)
    cv2.imwrite(W+f'depth_{name}_{H}.jpg',cv2.resize(vis,(623,1245)))
    print(name,H,inp['pixel_values'].shape,dev,'%.1fs'%(time.time()-t),flush=True)
    del model; torch.mps.empty_cache() if dev=='mps' else None
