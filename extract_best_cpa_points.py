import os, time
import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
from scipy import signal
import scalib as sca


plt.ion()
plt.show()

fs = 125 # sampling frequency [MHz]
cutoff = 10 # cutoff frequency [MHz]
width = 4 # transition width [MHz]
attenuation = 65 # stop band attenuation [dB]


filename = 'data/model/POIs_ABCDEFGHIJ.mat'
mat_contents = sio.loadmat(filename)
r_z = mat_contents['r_z']
pois_r_z = mat_contents['pois_r_z'].astype(int)

sets = ['F','G','H','I']
ns = 5000
nt = len(sets)*ns
nl = 16384

traces = np.zeros((nt,nl))
keys = np.zeros((nt,32),dtype=int)
plaintexts = np.zeros((nt,16),dtype=int)

print('Loading profiling sets')
for i in range(len(sets)):
	print('Set ' + sets[i] + '\t', end='')
	filename = 'data/profiling_set_nt_5000_' + sets[i] + '.mat'
	mat_contents = sio.loadmat(filename)

	print('Filtering')
	tr = mat_contents['traces']
	tr = sca.kaiser_LP_filter(tr,fs,cutoff,width,attenuation)

	traces[i*ns:(i+1)*ns,:] = tr
	keys[i*ns:(i+1)*ns,:] = mat_contents['keys'].astype(int)
	plaintexts[i*ns:(i+1)*ns,:] = mat_contents['plaintexts'].astype(int)


# print('Filtering of traces')
# traces = sca.kaiser_LP_filter(traces,fs,cutoff,width,attenuation)

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


filename = 'data/model/PP_CPA.mat'

sio.savemat(filename, dict([('alphas', alphas)]))

print('\nTemplates successfully saved to ' + filename + '\n')

plt.ioff()

plt.figure()
plt.plot(alphas)

plt.show()
