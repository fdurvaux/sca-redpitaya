import os, time, sys
import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
from scipy import signal
sys.path.insert(0,'../lib/')
import scalib as sca

plt.ion()
plt.show()

demodulation = True

filename = '../traces/profiling_set_nt_10000.mat'
mat_contents = sio.loadmat(filename)
traces = mat_contents['traces']
keys = mat_contents['keys'].astype(int)
plaintexts = mat_contents['plaintexts'].astype(int)
nt = traces.shape[0] # number of traces
nl = traces.shape[1] # number of samples per trace

if(demodulation):
    print('Demodulation of traces')
    fs = 125
    cutoff = 10 # cutoff frequency [MHz]
    width = 4 # transition width [MHz]
    attenuation = 65 # stop band attenuation [dB]
    traces = sca.kaiser_LP_filter(np.absolute(traces),fs=fs,cutoff=cutoff,width=width,attenuation=attenuation)

filename = '../traces/POIs.mat'
mat_contents = sio.loadmat(filename)
r_z = mat_contents['r_z']
pois_r_z = mat_contents['pois_r_z'].astype(int)

n_bytes = 32
n_pois = 400

k_r0 = keys[:,:16]
k_r1 = keys[:,16:]

x_r0 = plaintexts
y_r0 = sca.AES_AddRoundKey(k_r0,x_r0)
z_r0 = sca.AES_Sbox(y_r0)
w_r0 = sca.AES_ShiftRows(z_r0)
x_r1 = sca.AES_MixColumns(w_r0)
y_r1 = sca.AES_AddRoundKey(k_r1,x_r1)
z_r1 = sca.AES_Sbox(y_r1)

y = np.concatenate((y_r0,y_r1),axis=1)

alphas = np.zeros((nl,32))

for target_byte in range(n_bytes):
    print('Improving byte: ' + str(target_byte))

    pois = pois_r_z[:n_pois,target_byte]
    tr = traces[:,pois]
    y_b = y[:,target_byte]

    [alpha,cpa_prog] = sca.projection_pursuite_CPA(tr, y_b, np.arange(n_pois), n_iterations=2*n_pois, n_deltas=50)

    alphas[pois,target_byte] = alpha


filename = '../traces/PP_CPA.mat'

sio.savemat(filename, dict([('alphas', alphas)]))

print('\nProjection profiles successfully saved to ' + filename + '\n')

plt.ioff()

plt.figure()
plt.plot(alphas)

plt.show()
