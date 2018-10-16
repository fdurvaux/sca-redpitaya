import os, time
import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
from scipy import signal
import scalib as sca

nt = 1000 # number of traces
nl = 16384 # number of samples per trace
n_attack_traces = 1000

filtering = True
projection = True

fs = 125 # sampling frequency [MHz]
cutoff = 10 # cutoff frequency [MHz]
width = 4 # transition width [MHz]
attenuation = 65 # stop band attenuation [dB]

if(projection):
	filename = 'data/model/PP_CPA.mat'
	mat_contents = sio.loadmat(filename)
	alphas = mat_contents['alphas']

filename = 'data/attack_set_nt_' + str(nt) + '.mat' # output file
mat_contents = sio.loadmat(filename)
traces = mat_contents['traces']
plaintexts = mat_contents['plaintexts'].astype(np.int_)

traces = traces[:n_attack_traces,:]
plaintexts = plaintexts[:n_attack_traces,:]


if(filtering):
	traces = sca.kaiser_LP_filter(traces,fs,cutoff,width,attenuation)

n_bytes = 16

key_hyp = np.matmul(np.ones((n_attack_traces,1)),np.reshape(np.arange(256),(1,256))).astype(int)
best_keys = np.zeros(32, dtype=int)

# os.system('cls' if os.name == 'nt' else 'clear')

print('\n=================================')
print('=                               =')
print('=     CPA ATTACK ON AES-256     =')
print('=                               =')
print('=================================\n')

input('Press enter to proceed...\n')

print('\n')
print('---------------------')
print('ATTACK ON FIRST ROUND')
print('---------------------')
print('\n')

print('Key bytes:\n')

for target_byte in range(n_bytes):

	# print('Attacking byte ' + str(target_byte) + ': ', end='')
	x = plaintexts[:,target_byte]
	x = np.reshape(x,(x.shape[0],1))
	x = np.matmul(x,np.ones((1,256))).astype(int)

	y = sca.AES_AddRoundKey(key_hyp,x)
	z = sca.AES_Sbox(y)

	hw_z = sca.hamming_weigth(z)

	if(projection):
		tr = np.matmul(traces,alphas[:,target_byte])
		r = sca.corr(hw_z,tr)
		best_keys[target_byte] = np.argmax(np.absolute(r))
	else:
		r = sca.corr(hw_z,traces)
		scores = np.amax(np.absolute(r),axis=1)
		best_keys[target_byte] = np.argmax(scores)

	s = ''.join('%02X ' % best_keys[j] for j in range(target_byte+1))
	print(s,end='\r')

	# print('%02X' % best_keys[target_byte])

	# time.sleep(0.1)

	# if(target_byte==0):
	# 	plt.subplot(2,1,1)
	# 	plt.plot(np.arange(256),scores)
	# 	plt.subplot(2,1,2)
	# 	plt.plot(np.absolute(r[best_keys[0],:]))
	# 	plt.show()

print()

key_r0 = np.matmul(np.ones((n_attack_traces,1)),np.reshape(best_keys[:16],(1,16))).astype(int)
y_r0 = sca.AES_AddRoundKey(key_r0,plaintexts)
z_r0 = sca.AES_Sbox(y_r0)
w_r0 = sca.AES_ShiftRows(z_r0)
x_r1 = sca.AES_MixColumns(w_r0)

print('\n')
print('----------------------')
print('ATTACK ON SECOND ROUND')
print('----------------------')
print('\n')

print('Key bytes:\n')

for target_byte in range(n_bytes):

	# print('Attacking byte ' + str(target_byte+16) + ': ', end='')
	x = x_r1[:,target_byte]
	x = np.reshape(x,(x.shape[0],1))
	x = np.matmul(x,np.ones((1,256))).astype(int)

	y = sca.AES_AddRoundKey(key_hyp,x)
	z = sca.AES_Sbox(y)

	hw_z = sca.hamming_weigth(z)

	if(projection):
		tr = np.matmul(traces,alphas[:,target_byte+16])
		r = sca.corr(hw_z,tr)
		best_keys[target_byte+16] = np.argmax(np.absolute(r))
	else:
		r = sca.corr(hw_z,traces)
		scores = np.amax(np.absolute(r),axis=1)
		best_keys[target_byte+16] = np.argmax(scores)

	s = ''.join('%02X ' % best_keys[j] for j in np.arange(16,target_byte+16+1))
	print(s,end='\r')

	# print('%02X ' % best_keys[target_byte+16])

# s_hex = ["key: " + "".join('%02x ' % b for b in best_keys)]
# print(s_hex)

print()

s_hex = str(bytes(best_keys.astype('uint8')))
# s_hex = bytes(best_keys.astype('uint8')).decode()

print('\n\n***************************************************************\n')
print('THE KEY IS:\t' + s_hex)
print('\n***************************************************************\n')
