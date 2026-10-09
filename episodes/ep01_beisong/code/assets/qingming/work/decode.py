# Decode both Qingming sources to raw RGB + small previews for alignment.
import numpy as np, time
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
D='/Users/mr.ni/claude-projects/china-art/series/assets/qingming/'
t=time.time()
im=Image.open(D+'src_alongtheriver_38414x1800.jpg'); print(im.mode, im.size, flush=True)
im=im.convert('RGB')
a=np.asarray(im); a.tofile(D+'work/src_raw_38414x1800.rgb'); print('src raw', a.shape, time.time()-t, flush=True)
sm=im.resize((38414//8, 1800//8), Image.LANCZOS); sm.save(D+'work/src_ds8.png')
del a, im, sm
im=Image.open(D+'ref_minghuaji_21844x1109.png'); print(im.mode, im.size, flush=True)
im=im.convert('RGB')
sm=im.resize((21844*225//1109, 225), Image.LANCZOS); sm.save(D+'work/ref_h225.png')
sm2=im.resize((21844//4, 1109//4), Image.LANCZOS); sm2.save(D+'work/ref_ds4.png')
print('done', time.time()-t, flush=True)
