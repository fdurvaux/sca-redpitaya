import sys
import serial
import time
import socket
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import scipy.io as sio
import redpitaya_scpi as scpi
import scalib as sca

filtering = True

# connection info to Red Pitaya
rp_addr = 'rp-f0520c.local'
# rp_addr = '192.168.1.40'
rp_port = 5000
rp_timeout = 5
rp_s = scpi.scpi(rp_addr, timeout=rp_timeout, port=rp_port)
rp_s.tx_txt('ACQ:RST')

# connection info to Arduino
ser_port = '/dev/tty.usbmodem1421'
# ser_port = 'COM3'
ser_baud = 19200
ser_timeout = 5
ser = serial.Serial(ser_port, ser_baud, timeout=ser_timeout)
s = ser.readline()
print(s.decode())

# projection profiles
filename = 'data/model/PP_CPA.mat'
mat_contents = sio.loadmat(filename)
alphas = mat_contents['alphas']

print('\n==================================')
print('=                                =')
print('=     LIVE ATTACK OF AES-256     =')
print('=                                =')
print('==================================\n')

input('Press enter to proceed...\n')

ENC_TXT = bytes([0x10])

nl = 16384 # number of samples per trace
n_attack_traces = 100
n_bytes = 16

fs = 125 # sampling frequency [MHz]
cutoff = 10 # cutoff frequency [MHz]
width = 4 # transition width [MHz]
attenuation = 65 # stop band attenuation [dB]

# variables for correlations
traces = np.zeros((n_attack_traces,32))
hw = np.zeros((n_attack_traces,256,32))

# accumulators for correlation
sum_x = np.zeros(32) # projected trace
sum_x2 = np.zeros(32)
sum_y = np.zeros((256,32)) # model
sum_y2 = np.zeros((256,32))
sum_xy = np.zeros((256,32))

r = np.zeros((256,32))

key_hyp = np.arange(256,dtype=int)

best_keys_r0 = np.zeros(16,dtype=int)
best_keys_r1 = np.zeros(16,dtype=int)

# for handling timeout with red pitaya commands
maxTimeoutInARow = 5

for i in range(n_attack_traces):

	#########################
	### TRACE ACQUISITION ###
	#########################

	print('-------------------------')
	print('Trace ' + str(i+1))
	print('-------------------------')

	timeoutInARow = 0
	acquisitionDone = False

	while acquisitionDone==False:
		try:
			# oscilloscope configuration
			rp_s.tx_txt('ACQ:START')
			rp_s.tx_txt('ACQ:DEC 1')
			rp_s.tx_txt('ACQ:SOUR1:GAIN HV')
			rp_s.tx_txt('ACQ:SOUR2:GAIN LV')
			rp_s.tx_txt('ACQ:TRIG:LEV 200 mV')
			rp_s.tx_txt('ACQ:TRIG:LEV?')
			data = rp_s.rx_txt()
			# print('Trigger level ' + data)
			rp_s.tx_txt('ACQ:TRIG:DLY 8000')
			rp_s.tx_txt('ACQ:TRIG:DLY?')
			data = rp_s.rx_txt()
			# print('Trigger delay ' + data)
			rp_s.tx_txt('ACQ:TRIG CH2_PE')
			rp_s.tx_txt('ACQ:TRIG:STAT?')
			data = rp_s.rx_txt()
			# print('Trigger status ' + data)

			# sending plaintext
			plaintext = np.random.bytes(16)
			ser.write(ENC_TXT)
			s = ser.readline()
			ser.write(plaintext)

			# ciphertext recovery
			ciphertext = ser.read(16)

			# check if triggered
			rp_s.tx_txt('ACQ:TRIG:STAT?')
			data = rp_s.rx_txt()
			if data != 'TD':
				print("Error: no trigger detected. Stopping acquisition.")
				exit()

			# trace acquisition
			rp_s.tx_txt('ACQ:SOUR1:DATA?')
			data = rp_s.rx_txt()
			data = data.strip('{}\n\r')
			trace = np.fromstring(data, dtype=float, sep=',')

			# stopping acquisition
			rp_s.tx_txt('ACQ:STOP')
			acquisitionDone = True

		except socket.timeout:
			# this exception handling is there because of (so far) unexpected
			# loss of TCP connection with the Red Pitaya: it stops answering
			# requests and a timeout exception is issued
			#
			# the only solution I found is to re-open the connection
			# with the Red Pitaya (max 5 times)

			rp_s.close()
			rp_s = scpi.scpi(rp_addr, timeout=rp_timeout, port=rp_port)

			acquisitionDone = False
			timeoutInARow += 1
			if timeoutInARow >= maxTimeoutInARow:
				print('Something is fishy, too many timeouts!')
				exit()
			else:
				print('Timeout during acquisition! Re-trying...')

	######################
	### PRE-PROCESSING ###
	######################

	if(filtering):
		trace = sca.kaiser_LP_filter(trace,fs,cutoff,width,attenuation)

	#############################
	### ATTACK ON FIRST ROUND ###
	#############################

	x_r0 = np.frombuffer(plaintext, dtype=np.uint8).astype(int)

	for target_byte in np.arange(n_bytes):

		y = sca.AES_AddRoundKey(key_hyp,x_r0[target_byte])
		z = sca.AES_Sbox(y)
		hw_z = sca.hamming_weigth(z).ravel()

		tr = np.matmul(trace[None,:],alphas[:,target_byte])

		hw[i,:,target_byte] = hw_z
		traces[i,target_byte] = tr

		A = hw[:i,:,target_byte]
		B = traces[:i,target_byte]

		if(i>=3):
			r[:,target_byte] = sca.corr(A,B)

		# sum_x[target_byte] += tr
		# sum_x2[target_byte] += tr**2
		# sum_y[:,target_byte] += hw_z
		# sum_y2[:,target_byte] += hw_z**2
		# sum_xy[:,target_byte] += tr*hw_z

		# if(i>=5):
		# 	num = (i+1)*sum_xy[:,target_byte] - sum_x[target_byte]*sum_y[:,target_byte]
		# 	den = np.sqrt(((i+1)*sum_x2[target_byte])-(sum_x[target_byte]**2))
		# 	den *= np.sqrt(((i+1)*sum_y2[:,target_byte])-(sum_y[:,target_byte]**2))
		# 	r[:,target_byte] = num/den

		best_keys_r0[target_byte] = np.argmax(np.absolute(r[:,target_byte]))

	

	##############################
	### ATTACK ON SECOND ROUND ###
	##############################

	y_r0 = sca.AES_AddRoundKey(best_keys_r0,x_r0)
	z_r0 = sca.AES_Sbox(y_r0)
	w_r0 = sca.AES_ShiftRows(z_r0[None,:])
	x_r1 = sca.AES_MixColumns(w_r0).ravel()

	for target_byte in np.arange(n_bytes):

		y = sca.AES_AddRoundKey(key_hyp,x_r1[target_byte])
		z = sca.AES_Sbox(y)
		hw_z = sca.hamming_weigth(z).ravel()

		tr = np.matmul(trace[None,:],alphas[:,target_byte+16])

		hw[i,:,target_byte+16] = hw_z
		traces[i,target_byte+16] = tr

		A = hw[:i,:,target_byte+16]
		B = traces[:i,target_byte+16]

		if(i>=3):
			r[:,target_byte+16] = sca.corr(A,B)

		# sum_x[target_byte+16] += tr
		# sum_x2[target_byte+16] += tr**2
		# sum_y[:,target_byte+16] += hw_z
		# sum_y2[:,target_byte+16] += hw_z**2
		# sum_xy[:,target_byte+16] += tr*hw_z

		# if(i>=5):
		# 	num = (i+1)*sum_xy[:,target_byte+16] - sum_x[target_byte+16]*sum_y[:,target_byte+16]
		# 	den = np.sqrt(((i+1)*sum_x2[target_byte+16])-(sum_x[target_byte+16]**2))
		# 	den *= np.sqrt(((i+1)*sum_y2[:,target_byte+16])-(sum_y[:,target_byte+16]**2))
		# 	r[:,target_byte+16] = num/den

		best_keys_r1[target_byte] = np.argmax(np.absolute(r[:,target_byte+16]))

	#######################
	### DISPLAY RESULTS ###
	#######################

	best_keys = np.concatenate((best_keys_r0,best_keys_r1))

	if(i>=3):

		s_hex = ''.join('%02x ' % b for b in best_keys_r0)
		print('ROUND KEY 1: ' + s_hex)

		s_hex = ''.join('%02x ' % b for b in best_keys_r1)
		print('ROUND KEY 2: ' + s_hex)

		s_hex = str(bytes(best_keys.astype('uint8')))
		print('\nBest key guess: ' + s_hex)

	print()

# key_prob = np.concatenate((key_prob_r0,key_prob_r1),axis=1)

# s = bytes(best_keys.astype('uint8')).decode()
s = str(bytes(best_keys.astype('uint8')))
print('\n***************************************\n')
print('KEY FOUND: ' + s)
print('\n***************************************\n')

# plt.plot(key_prob)
plt.show()


