import os, time, sys
import numpy as np
import matplotlib.pyplot as plt
import scipy.io as sio
from scipy import signal
sys.path.insert(0,'../lib/')
import scalib as sca

# for executing amplitude demodulation on the power traces
demodulation = False

filename = '../traces/profiling_set_nt_5000.mat'
mat_contents = sio.loadmat(filename)
traces = mat_contents['traces']

# number of time samples
nl = traces.shape[1]

if demodulation:
    fs = 125 # sampling frequency [MHz]
    cutoff = 10 # cutoff frequency [MHz]
    width = 4 # transition width [MHz]
    attenuation = 65 # stop band attenuation [dB]
    traces = sca.kaiser_LP_filter(np.absolute(traces),fs=fs,cutoff=cutoff,width=width,attenuation=attenuation)

traces_avg = np.mean(traces,axis=0)

plt.figure()
plt.plot(traces_avg)
plt.yticks([])
plt.ylabel('power',fontsize=14)
plt.xlabel(r'$\rightarrow$ time samples',fontsize=14)
plt.show()
