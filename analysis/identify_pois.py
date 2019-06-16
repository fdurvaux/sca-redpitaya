import os, time, sys
import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
from scipy import signal
sys.path.insert(0,'../lib/')
import scalib as sca

# THIS SCRIPT IS USED TO IDENTIFY THE POINTS OF INTEREST

demodulation = True

filename = '../traces/profiling_set_nt_10000.mat'
mat_contents = sio.loadmat(filename)
traces = mat_contents['traces']
keys = mat_contents['keys'].astype(int)
plaintexts = mat_contents['plaintexts'].astype(int)
nt = traces.shape[0] # number of traces
nl = traces.shape[1] # number of samples per trace

# computation parameters
n_bytes = 32
n_pois = 1000

# variables for computing a global SNR
sum_x = np.zeros((256,nl,n_bytes))
sum_x2 = np.zeros((256,nl,n_bytes))
x_n = np.zeros((256,n_bytes))
snr = np.zeros((nl,n_bytes))

# variables for computing a global CPA targeting the S-box output
sum_a = np.zeros((nl,n_bytes))
sum_a2 = np.zeros((nl,n_bytes))
sum_b = np.zeros(n_bytes)
sum_b2 = np.zeros(n_bytes)
sum_ab = np.zeros((nl,n_bytes))
r_z = np.zeros((nl,n_bytes))

# variables for storing the Points-of-Interest (POIs)
pois_snr = np.zeros((n_pois,n_bytes),dtype=int)
pois_r_z = np.zeros((n_pois,n_bytes),dtype=int)

if(demodulation):
    print('Demodulation of traces')
    fs = 125
    cutoff = 10 # cutoff frequency [MHz]
    width = 4 # transition width [MHz]
    attenuation = 65 # stop band attenuation [dB]
    traces = sca.kaiser_LP_filter(np.absolute(traces),fs=fs,cutoff=cutoff,width=width,attenuation=attenuation)

keys_r0 = keys[:,:16]
keys_r1 = keys[:,16:]

y_r0 = sca.AES_AddRoundKey(keys_r0,plaintexts)
z_r0 = sca.AES_Sbox(y_r0)
w_r0 = sca.AES_ShiftRows(z_r0)
x_r1 = sca.AES_MixColumns(w_r0)
y_r1 = sca.AES_AddRoundKey(keys_r1,x_r1)
z_r1 = sca.AES_Sbox(y_r1)

y = np.concatenate((y_r0,y_r1),axis=1)
z = np.concatenate((z_r0,z_r1),axis=1)

for target_byte in range(n_bytes):
    print('- byte ' + str(target_byte))

    # accumulators for mean and variance
    yu = np.unique(y[:,target_byte])
    for yi in yu:
        traces_y = traces[y[:,target_byte]==yi,:]
        sum_x[yi,:,target_byte] += np.sum(traces_y,axis=0)
        sum_x2[yi,:,target_byte] += np.sum(traces_y**2,axis=0)
        x_n[yi,target_byte] += traces_y.shape[0]

    # accumulators for CPA
    hw_z = sca.hamming_weigth(z[:,target_byte]).ravel()
    sum_a[:,target_byte] += np.sum(traces,axis=0)
    sum_a2[:,target_byte] += np.sum(traces**2,axis=0)
    sum_b[target_byte] += np.sum(hw_z)
    sum_b2[target_byte] += np.sum(hw_z**2)
    sum_ab[:,target_byte] += np.sum(traces*hw_z[:,None],axis=0)




for target_byte in range(n_bytes):
    # SNR computation
    traces_m = sum_x[:,:,target_byte]/x_n[:,None,target_byte]
    traces_s = np.sqrt(sum_x2[:,:,target_byte]/x_n[:,None,target_byte]-traces_m**2)
    snr[:,target_byte] = sca.SNR(traces_m,traces_s)

    snr_sorted = snr[:,target_byte].argsort()[::-1]
    pois_snr[:,target_byte] = snr_sorted[:n_pois]

    # CPA computation
    num = nt*sum_ab[:,target_byte] - sum_a[:,target_byte]*sum_b[target_byte]
    den = np.sqrt(nt*sum_a2[:,target_byte]-sum_a[:,target_byte]**2)
    den *= np.sqrt(nt*sum_b2[target_byte]-sum_b[target_byte]**2)
    r_z[:,target_byte] = num/den

    r_z_sorted = np.absolute(r_z[:,target_byte]).argsort()[::-1]
    pois_r_z[:,target_byte] = r_z_sorted[:n_pois]

    plt.figure()
    plt.subplot(2,1,1)
    plt.title('Byte ' + str(target_byte))
    plt.plot(snr[:,target_byte])

    plt.subplot(2,1,2)
    plt.plot(np.absolute(r_z[:,target_byte]))




filename = '../traces/POIs.mat'

sio.savemat(filename, dict([
    ('fs', fs),
    ('nl', nl),
    ('snr', snr),
    ('pois_snr', pois_snr),
    ('r_z', r_z),
    ('pois_r_z', pois_r_z)]))

print('\nPOIs successfully saved to ' + filename + '\n')

plt.show()

