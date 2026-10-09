import numpy as np, cv2
d=np.load('work_ds2_raw.npy')
g=cv2.cvtColor(d,cv2.COLOR_RGB2GRAY).astype(float)
# precise borders at ds2
cm=g[2000:8000].mean(0); rm=g[:,500:4500].mean(1)
print('left',[ (i,int(cm[i])) for i in range(55,95,3)])
print('right',[ (i,int(cm[i])) for i in range(5040,5090,3)])
print('top',[ (i,int(rm[i])) for i in range(50,90,3)])
print('bot',[ (i,int(rm[i])) for i in range(10010,10050,3)])
