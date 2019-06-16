import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

aes_sbox = np.array([99, 124, 119, 123, 242, 107, 111, 197, 48, 1, 103, 43, 254, 215, 171, 118, 202, 130, 201, 125, 250, 89, 71, 240, 173, 212, 162, 175, 156, 164, 114, 192, 183, 253, 147, 38, 54, 63, 247, 204, 52, 165, 229, 241, 113, 216, 49, 21, 4, 199, 35, 195, 24, 150, 5, 154, 7, 18, 128, 226, 235, 39, 178, 117, 9, 131, 44, 26, 27, 110, 90, 160, 82, 59, 214, 179, 41, 227, 47, 132, 83, 209, 0, 237, 32, 252, 177, 91, 106, 203, 190, 57, 74, 76, 88, 207, 208, 239, 170, 251, 67, 77, 51, 133, 69, 249, 2, 127, 80, 60, 159, 168, 81, 163, 64, 143, 146, 157, 56, 245, 188, 182, 218, 33, 16, 255, 243, 210, 205, 12, 19, 236, 95, 151, 68, 23, 196, 167, 126, 61, 100, 93, 25, 115, 96, 129, 79, 220, 34, 42, 144, 136, 70, 238, 184, 20, 222, 94, 11, 219, 224, 50, 58, 10, 73, 6, 36, 92, 194, 211, 172, 98, 145, 149, 228, 121, 231, 200, 55, 109, 141, 213, 78, 169, 108, 86, 244, 234, 101, 122, 174, 8, 186, 120, 37, 46, 28, 166, 180, 198, 232, 221, 116, 31, 75, 189, 139, 138, 112, 62, 181, 102, 72, 3, 246, 14, 97, 53, 87, 185, 134, 193, 29, 158, 225, 248, 152, 17, 105, 217, 142, 148, 155, 30, 135, 233, 206, 85, 40, 223, 140, 161, 137, 13, 191, 230, 66, 104, 65, 153, 45, 15, 176, 84, 187, 22])
aes_gmul2 = np.array([0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72, 74, 76, 78, 80, 82, 84, 86, 88, 90, 92, 94, 96, 98, 100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128, 130, 132, 134, 136, 138, 140, 142, 144, 146, 148, 150, 152, 154, 156, 158, 160, 162, 164, 166, 168, 170, 172, 174, 176, 178, 180, 182, 184, 186, 188, 190, 192, 194, 196, 198, 200, 202, 204, 206, 208, 210, 212, 214, 216, 218, 220, 222, 224, 226, 228, 230, 232, 234, 236, 238, 240, 242, 244, 246, 248, 250, 252, 254, 27, 25, 31, 29, 19, 17, 23, 21, 11, 9, 15, 13, 3, 1, 7, 5, 59, 57, 63, 61, 51, 49, 55, 53, 43, 41, 47, 45, 35, 33, 39, 37, 91, 89, 95, 93, 83, 81, 87, 85, 75, 73, 79, 77, 67, 65, 71, 69, 123, 121, 127, 125, 115, 113, 119, 117, 107, 105, 111, 109, 99, 97, 103, 101, 155, 153, 159, 157, 147, 145, 151, 149, 139, 137, 143, 141, 131, 129, 135, 133, 187, 185, 191, 189, 179, 177, 183, 181, 171, 169, 175, 173, 163, 161, 167, 165, 219, 217, 223, 221, 211, 209, 215, 213, 203, 201, 207, 205, 195, 193, 199, 197, 251, 249, 255, 253, 243, 241, 247, 245, 235, 233, 239, 237, 227, 225, 231, 229])
aes_gmul3 = np.array([0, 3, 6, 5, 12, 15, 10, 9, 24, 27, 30, 29, 20, 23, 18, 17, 48, 51, 54, 53, 60, 63, 58, 57, 40, 43, 46, 45, 36, 39, 34, 33, 96, 99, 102, 101, 108, 111, 106, 105, 120, 123, 126, 125, 116, 119, 114, 113, 80, 83, 86, 85, 92, 95, 90, 89, 72, 75, 78, 77, 68, 71, 66, 65, 192, 195, 198, 197, 204, 207, 202, 201, 216, 219, 222, 221, 212, 215, 210, 209, 240, 243, 246, 245, 252, 255, 250, 249, 232, 235, 238, 237, 228, 231, 226, 225, 160, 163, 166, 165, 172, 175, 170, 169, 184, 187, 190, 189, 180, 183, 178, 177, 144, 147, 150, 149, 156, 159, 154, 153, 136, 139, 142, 141, 132, 135, 130, 129, 155, 152, 157, 158, 151, 148, 145, 146, 131, 128, 133, 134, 143, 140, 137, 138, 171, 168, 173, 174, 167, 164, 161, 162, 179, 176, 181, 182, 191, 188, 185, 186, 251, 248, 253, 254, 247, 244, 241, 242, 227, 224, 229, 230, 239, 236, 233, 234, 203, 200, 205, 206, 199, 196, 193, 194, 211, 208, 213, 214, 223, 220, 217, 218, 91, 88, 93, 94, 87, 84, 81, 82, 67, 64, 69, 70, 79, 76, 73, 74, 107, 104, 109, 110, 103, 100, 97, 98, 115, 112, 117, 118, 127, 124, 121, 122, 59, 56, 61, 62, 55, 52, 49, 50, 35, 32, 37, 38, 47, 44, 41, 42, 11, 8, 13, 14, 7, 4, 1, 2, 19, 16, 21, 22, 31, 28, 25, 26])

# AES AddRoundKey
def AES_AddRoundKey(x,y):
	return np.bitwise_xor(x,y)

# AES S-box
def AES_Sbox(x):
	return aes_sbox[x]

# AES ShiftRows
def AES_ShiftRows(x):
	return x[:,[0, 5, 10, 15, 4, 9, 14, 3, 8, 13, 2, 7, 12, 1, 6, 11]]

# AES MixColumns
def AES_MixColumns(x):
	y = np.zeros((x.shape[0],16), dtype=int)
	for i in range(4):
		x0 = x[:,i*4]
		x1 = x[:,i*4+1]
		x2 = x[:,i*4+2]
		x3 = x[:,i*4+3]
		y[:,i*4]   = np.bitwise_xor(np.bitwise_xor(aes_gmul2[x0],aes_gmul3[x1]),np.bitwise_xor(x2,x3))
		y[:,i*4+1] = np.bitwise_xor(np.bitwise_xor(x0,aes_gmul2[x1]),np.bitwise_xor(aes_gmul3[x2],x3))
		y[:,i*4+2] = np.bitwise_xor(np.bitwise_xor(x0,x1),np.bitwise_xor(aes_gmul2[x2],aes_gmul3[x3]))
		y[:,i*4+3] = np.bitwise_xor(np.bitwise_xor(aes_gmul3[x0],x1),np.bitwise_xor(x2,aes_gmul2[x3]))
	return y

# conversion of integer values into base-z vectors (z=2 by default)
def dec2vec(d,n,z=2):
	d = d.reshape((d.size,1))
	v = z**(np.arange(1-n,1,1,dtype='float'))
	v = v.reshape((1,v.size))
	v = np.floor(np.matmul(d,v))
	v = np.remainder(v,z)
	return v

# computation of hamming weigth
def hamming_weigth(d):
	nr = d.shape[0]
	hw = np.sum(dec2vec(d,8,2),axis=1)
	hw = np.reshape(hw,(nr,int(hw.size/nr)))
	return hw

# computation of Pearson's correlation
def corr(x,y):
	xn = (x-np.mean(x,axis=0))/np.std(x,axis=0)
	yn = (y-np.mean(y,axis=0))/np.std(y,axis=0)
	r = np.matmul(xn.T,yn)/x.shape[0]
	return r

# Gaussian probability density function
# x: observation
# m: mean
# s: standard deviation
def normpdf(x,m,s):
	den = np.sqrt(2*np.pi*s**2)
	num = np.exp(-(x-m)**2/(2*s**2))
	return num/den

# generation of simulated traces (output of the S-box in the first round only)
def generate_traces(plaintexts, keys, noise_std=1):
	y = AES_AddRoundKey(plaintexts, keys)
	z = AES_Sbox(y)
	# compute hamming weigth
	traces = np.reshape(hamming_weigth(z),(z.shape[0],z.shape[1]))
	# add noise
	traces += np.random.normal(0,noise_std,(traces.shape[0],traces.shape[1]))
	return traces

# signal-to-noise ratio
def SNR(m_x,s_x):
	snr = np.var(m_x,axis=0)/np.mean(s_x**2,axis=0)
	return snr

def kaiser_LP_filter(traces, fs, cutoff, width, attenuation):
	numtaps, beta = signal.kaiserord(attenuation, width/(0.5*fs))
	taps = signal.firwin(numtaps, cutoff/(0.5*fs), window=('kaiser', beta))
	traces_filtered = signal.lfilter(taps, [1.0], traces)
	return traces_filtered

def window_LP_filter(traces, fs, cutoff):
	if(len(traces.shape)==1):
		traces = np.reshape(traces,(1,traces.size))
	nl = traces.shape[1]
	frequencies = np.linspace(0,fs,nl)
	window_filter = np.ones(nl)
	window_filter[frequencies>cutoff] = 0
	traces_fft = np.fft.fft(traces,axis=1)
	traces_fft = window_filter[None,:]*traces_fft
	traces_filtered = np.abs(np.fft.ifft(traces_fft,axis=1))
	return traces_filtered

def window_HP_filter(traces, fs, cutoff):
	if(len(traces.shape)==1):
		traces = np.reshape(traces,(1,traces.size))
	nl = traces.shape[1]
	frequencies = np.linspace(0,fs,nl)
	window_filter = np.ones(nl)
	window_filter[frequencies<cutoff] = 0
	traces_fft = np.fft.fft(traces,axis=1)
	traces_fft = window_filter[None,:]*traces_fft
	traces_filtered = np.abs(np.fft.ifft(traces_fft,axis=1))
	return traces_filtered

def window_BP_filter(traces, fs, cutoff_low, cutoff_high):
	if(len(traces.shape)==1):
		traces = np.reshape(traces,(1,traces.size))
	nl = traces.shape[1]
	frequencies = np.linspace(0,fs,nl)
	window_filter = np.ones(nl)
	window_filter[frequencies<cutoff_low] = 0
	window_filter[frequencies>cutoff_high] = 0
	traces_fft = np.fft.fft(traces,axis=1)
	traces_fft = window_filter[None,:]*traces_fft
	traces_filtered = np.abs(np.fft.ifft(traces_fft,axis=1))
	return traces_filtered

def align_traces(trace, trace_ref, x_min, x_max, max_sep=5):
	nl = x_max-x_min
	nsep = 2*max_sep+1
	
	A = np.reshape(trace_ref[x_min:x_max],(nl,1))
	B = np.zeros((nl,nsep))

	sep = np.arange(-max_sep,max_sep+1)
	for i in sep:
		B[:,i] = trace[x_min+sep[i]:x_max+sep[i]]

	r = corr(A,B).ravel()

	# return r
	return sep[np.argmax(r)]

def projection_pursuite(traces, y, pois, n_iterations=500, n_deltas=50):

	nl = traces.shape[1]
	n_pois = pois.size

	yu = np.unique(y)
	traces_m = np.zeros((256,nl))
	traces_s = np.zeros((256,nl))

	tproj_m = np.zeros((256,n_deltas+1))
	tproj_s = np.zeros((256,n_deltas+1))

	# for yi in yu:
	# 	traces_y = traces[y==yi,:]
	# 	traces_m[yi,:] = np.mean(traces_y,axis=0)
	# 	traces_s[yi,:] = np.std(traces_y,axis=0)

	# snr = SNR(traces_m,traces_s)
	# snr_sorted = snr.argsort()[::-1]

	# z = AES_Sbox(y)
	# hw_z = hamming_weigth(z)
	# cpa = np.absolute(corr(hw_z,traces).ravel())
	# cpa_sorted = cpa.argsort()[::-1]

	# pois = snr_sorted[:n_pois]
	# pois = cpa_sorted[:n_pois]
	alpha = np.zeros(nl)
	alpha[pois] = 1/n_pois

	snr_progress = np.zeros(n_iterations)

	print('-- PROJECTION PURSUITE --')
	for i in range(n_iterations):
		print('\rProgression: %i%%' % np.ceil(i/n_iterations*100), end='')

		# alpha_i is drawn from a random permutation of the POIs in order to make
		# sure that each is tested at least once, as long as n_iterations > n_pois
		# the permutation is updated once all POIs were tested
		if((i%n_pois)==0):
			perm_pois = np.random.permutation(n_pois)

		alpha_i = perm_pois[i%n_pois]
		alphas = np.matmul(np.reshape(alpha[pois],(n_pois,1)),np.ones((1,n_deltas+1)))
		# deltas = np.linspace(-5*alpha[alpha_i],5*alpha[alpha_i],n_deltas)
		deltas = np.random.randn(n_deltas)*0.2
		alphas[alpha_i,:-1] += deltas
		alphas /= np.sum(np.absolute(alphas),axis=0)
		traces_projected = np.matmul(traces[:,pois],alphas)

		for yi in yu:
			tproj_y = traces_projected[y==yi,:]
			tproj_m[yi,:] = np.mean(tproj_y,axis=0)
			tproj_s[yi,:] = np.std(tproj_y,axis=0)

		snr = SNR(tproj_m,tproj_s)
		snr_ix = np.argmax(snr)
		snr_progress[i] = snr[snr_ix]

		alpha[pois] = alphas[:,snr_ix]
		# alpha = alpha/np.sum(np.absolute(alpha))

		plt.clf()
		plt.subplot(2,1,1)
		plt.plot(alpha)
		plt.subplot(2,1,2)
		plt.plot(snr_progress[:i])
		plt.draw()
		plt.pause(0.01)

	print()

	return alpha, snr_progress



def projection_pursuite_CPA(traces, y, pois, n_iterations=500, n_deltas=50):

	nl = traces.shape[1]
	n_pois = pois.size


	alpha = np.zeros(nl)
	alpha[pois] = 1/n_pois

	cpa_progress = np.zeros(n_iterations)

	print('-- PROJECTION PURSUITE --')
	for i in range(n_iterations):
		print('\rProgression: %i%%' % np.ceil(i/n_iterations*100), end='')

		# alpha_i is drawn from a random permutation of the POIs in order to make
		# sure that each is tested at least once, as long as n_iterations > n_pois
		# the permutation is updated once all POIs were tested
		if((i%n_pois)==0):
			perm_pois = np.random.permutation(n_pois)

		alpha_i = perm_pois[i%n_pois]
		alphas = np.matmul(np.reshape(alpha[pois],(n_pois,1)),np.ones((1,n_deltas+1)))
		# deltas = np.linspace(-5*alpha[alpha_i],5*alpha[alpha_i],n_deltas)
		deltas = np.random.randn(n_deltas)*0.2
		alphas[alpha_i,:-1] += deltas
		alphas /= np.sum(np.absolute(alphas),axis=0)
		traces_projected = np.matmul(traces[:,pois],alphas)

		z = AES_Sbox(y)
		hw_z = hamming_weigth(z).ravel()

		cpa = corr(hw_z,traces_projected)
		cpa_ix = np.argmax(cpa)
		cpa_progress[i] = cpa[cpa_ix]

		alpha[pois] = alphas[:,cpa_ix]
		# alpha = alpha/np.sum(np.absolute(alpha))

		plt.clf()
		plt.subplot(2,1,1)
		plt.plot(alpha)
		plt.subplot(2,1,2)
		plt.plot(cpa_progress[:i])
		plt.draw()
		plt.pause(0.01)

	print()

	return alpha, cpa_progress
