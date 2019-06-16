import os, time, sys
import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
from scipy import signal
sys.path.insert(0,'../lib/')
import scalib as sca

n_attack_traces = 250

demodulation = True

filename = '../traces/attack_set_nt_500.mat'
mat_contents = sio.loadmat(filename)
traces = mat_contents['traces']
plaintexts = mat_contents['plaintexts'].astype(np.int_)
traces = traces[:n_attack_traces,:]
plaintexts = plaintexts[:n_attack_traces,:]

nl = traces.shape[1] # number of samples per trace

if(demodulation):
    fs = 125
    cutoff = 10 # cutoff frequency [MHz]
    width = 4 # transition width [MHz]
    attenuation = 65 # stop band attenuation [dB]
    traces = sca.kaiser_LP_filter(np.absolute(traces),fs=fs,cutoff=cutoff,width=width,attenuation=attenuation)

n_bytes = 16

key_hyp = np.matmul(np.ones((n_attack_traces,1)),np.reshape(np.arange(256),(1,256))).astype(int)
best_keys = np.zeros(32, dtype=int)

print('\n=================================')
print('=                               =')
print('=     CPA ATTACK ON AES-256     =')
print('=                               =')
print('=================================\n')

input('Press enter to proceed...\n')

print('FIRST ROUND:\t', end='')

tic = time.time()

for target_byte in range(n_bytes):

    # print('Attacking byte ' + str(target_byte) + ': ', end='')
    x = plaintexts[:,target_byte]
    x = np.reshape(x,(x.shape[0],1))
    x = np.matmul(x,np.ones((1,256))).astype(int)

    y = sca.AES_AddRoundKey(key_hyp,x)
    z = sca.AES_Sbox(y)

    hw_z = sca.hamming_weigth(z)

    r = sca.corr(hw_z,traces)
    scores = np.amax(np.absolute(r),axis=1)
    best_keys[target_byte] = np.argmax(scores)

    print('%02X ' % best_keys[target_byte], end='', flush=True)

print()

key_r0 = np.matmul(np.ones((n_attack_traces,1)),np.reshape(best_keys[:16],(1,16))).astype(int)
y_r0 = sca.AES_AddRoundKey(key_r0,plaintexts)
z_r0 = sca.AES_Sbox(y_r0)
w_r0 = sca.AES_ShiftRows(z_r0)
x_r1 = sca.AES_MixColumns(w_r0)

print('SECOND ROUND:\t', end='')

for target_byte in range(n_bytes):

    # print('Attacking byte ' + str(target_byte+16) + ': ', end='')
    x = x_r1[:,target_byte]
    x = np.reshape(x,(x.shape[0],1))
    x = np.matmul(x,np.ones((1,256))).astype(int)

    y = sca.AES_AddRoundKey(key_hyp,x)
    z = sca.AES_Sbox(y)

    hw_z = sca.hamming_weigth(z)

    r = sca.corr(hw_z,traces)
    scores = np.amax(np.absolute(r),axis=1)
    best_keys[target_byte+16] = np.argmax(scores)

    print('%02X ' % best_keys[target_byte+16], end='', flush=True)

toc = time.time()

print()

s_hex = str(bytes(best_keys.astype('uint8')))

print('\n\n***************************************************************\n')
print('THE KEY IS:\t' + s_hex)
print('\n***************************************************************\n')

print('Elapsed time: %f seconds' % (toc-tic))
print()
