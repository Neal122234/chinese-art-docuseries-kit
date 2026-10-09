import torch, numpy as np, cv2, time, sys
from transformers import AutoImageProcessor, AutoModelForDepthEstimation
name=sys.argv[1]; H=int(sys.argv[2])
t=time.time()
proc=AutoImageProcessor.from_pretrained(name); model=AutoModelForDepthEstimation.from_pretrained(name).to('mps').eval()
img=cv2.cvtColor(cv2.imread('P8.png'),cv2.COLOR_BGR2RGB)
h,w=img.shape[:2]; W=int(round(w*H/h/14))*14
x=cv2.resize(img,(W,H),interpolation=cv2.INTER_AREA).astype(np.float32)/255
mean=np.array([0.485,0.456,0.406]);std=np.array([0.229,0.224,0.225])
x=((x-mean)/std).transpose(2,0,1)[None].astype(np.float32)
with torch.no_grad():
    out=model(pixel_values=torch.from_numpy(x).to('mps')).predicted_depth
d=out[0].float().cpu().numpy()
d=cv2.resize(d,(w,h),interpolation=cv2.INTER_CUBIC)
tag=name.split('-')[-2].lower()+f'_{H}'
np.save(f'depth_{tag}.npy',d)
v=(d-d.min())/(d.max()-d.min())
cv2.imwrite(f'depth_{tag}.png',(v*255).astype(np.uint8))
print(tag,d.shape,d.min(),d.max(),'time',time.time()-t)
