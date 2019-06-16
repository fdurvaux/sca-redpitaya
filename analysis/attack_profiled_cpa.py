import sys
sys.path.insert(0,'../lib/')
sys.path.insert(0,'../lib/')
import serial
import time
import socket
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import scipy.io as sio
import redpitaya_scpi as scpi
import scalib as sca

demodulation = True
plotting = False

rp_addr = '192.168.1.6'
rp_port = 5000
rp_timeout = 5
rp_s = scpi.scpi(rp_addr, timeout=rp_timeout, port=rp_port)
rp_s.tx_txt('ACQ:RST')

# connection info to Arduino
ser_port = 'COM5'
ser_baud = 19200
ser_timeout = 5
ser = serial.Serial(ser_port, ser_baud, timeout=ser_timeout)
s = ser.readline()
print(s.decode())

# projection profiles
filename = '../traces/PP_CPA.mat'
mat_contents = sio.loadmat(filename)
alphas = mat_contents['alphas']

print('\n==================================')
print('=                                =')
print('=     LIVE ATTACK OF AES-256     =')
print('=                                =')
print('==================================\n')

# input('Press enter to proceed...\n')

ENC_TXT = bytes([0x10])

n_attack_traces = 100
n_bytes = 16

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
acquisitionDone = False
timeoutInARow = 0
maxTimeoutInARow = 5

# print('-------------------------')
# print('      Attack start       ')
# print('-------------------------')
# print()

if plotting:
    plt.figure(1,figsize=(10,5))

traces_sum = np.zeros(alphas.shape[0])

for i in range(n_attack_traces):

    #########################
    ### TRACE ACQUISITION ###
    #########################

    # print('-------------------------')
    # print('Trace ' + str(i+1))
    # print('-------------------------')

    timeoutInARow = 0
    acquisitionDone = False

    while acquisitionDone==False:
        try:

            # oscilloscope configuration
            rp_s.tx_txt('ACQ:START')
            rp_s.tx_txt('ACQ:DEC 1')
            rp_s.tx_txt('ACQ:SOUR1:GAIN LV')
            rp_s.tx_txt('ACQ:SOUR2:GAIN LV')
            rp_s.tx_txt('ACQ:TRIG:LEV 300 mV')
            rp_s.tx_txt('ACQ:TRIG:LEV?')
            data = rp_s.rx_txt()
            # print('Trigger level ' + data)
            rp_s.tx_txt('ACQ:TRIG:DLY 8000')
            # rp_s.tx_txt('ACQ:TRIG:DLY 0')
            rp_s.tx_txt('ACQ:TRIG:DLY?')
            data = rp_s.rx_txt()
            # print('Trigger delay ' + data)
            rp_s.tx_txt('ACQ:TRIG CH2_PE')
            rp_s.tx_txt('ACQ:TRIG:STAT?')
            data = rp_s.rx_txt()

            # sending plaintext
            plaintext = np.random.randint(0,256,16)
            # plaintext = np.random.bytes(16)
            ser.write(ENC_TXT)
            s = ser.readline()
            # ser.write(plaintext)
            ser.write(plaintext.astype(dtype=np.uint8).tobytes())

            time.sleep(0.01)

            # ciphertext recovery
            ciphertext = ser.read(16)

            # check if triggered
            rp_s.tx_txt('ACQ:TRIG:STAT?')
            data = rp_s.rx_txt()
            if data == 'TD':
                print()
            else:
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

    if(demodulation):
        trace = sca.kaiser_LP_filter(np.absolute(trace),fs=125,cutoff=10,width=4,attenuation=65)

    #############################
    ### ATTACK ON FIRST ROUND ###
    #############################

    x_r0 = plaintext

    for target_byte in np.arange(n_bytes):

        y = sca.AES_AddRoundKey(key_hyp,x_r0[target_byte])
        z = sca.AES_Sbox(y)
        hw_z = sca.hamming_weigth(z).ravel()

        tr = np.matmul(trace[None,:],alphas[:,target_byte])

        hw[i,:,target_byte] = hw_z
        traces[i,target_byte] = tr

        A = hw[:i,:,target_byte]
        B = traces[:i,target_byte]

        if(i>=8):
            r[:,target_byte] = sca.corr(A,B)

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

        if(i>=8):
            r[:,target_byte+16] = sca.corr(A,B)

        best_keys_r1[target_byte] = np.argmax(np.absolute(r[:,target_byte+16]))

    #######################
    ### DISPLAY RESULTS ###
    #######################

    traces_sum += trace.ravel()
    traces_avg = traces_sum/(i+1)

    if plotting:
        plt.clf()
        plt.subplot(2,1,1)
        plt.plot(trace.ravel())
        plt.title('Trace ' + str(i+1) + ' (' + str(n_attack_traces) + ')',fontsize=20)
        plt.ylabel('current',fontsize=15)
        plt.xlabel('time samples',fontsize=15)
        plt.subplot(2,1,2)
        plt.plot(traces_avg)
        plt.ylabel('average',fontsize=15)
        plt.xlabel('time samples',fontsize=15)
        plt.draw()
        plt.pause(0.01)

    best_keys = np.concatenate((best_keys_r0,best_keys_r1))

    if(i>=8):

        s_hex = ''.join('%02x ' % b for b in best_keys_r0)
        # print('ROUND KEY 1: ' + s_hex)

        s_hex = ''.join('%02x ' % b for b in best_keys_r1)
        # print('ROUND KEY 2: ' + s_hex)

        s_hex = str(bytes(best_keys.astype('uint8')))
        # s_hex += ' '*30
        # print('\nBest key guess: ' + s_hex)

        print('Trace: %d of %d' % (i+1, n_attack_traces))
        # print(s_hex[1:-1])
        print('Key found: ' + s_hex[2:-1])
        # print('Key found (' + str(i+1) + '/' + str(n_attack_traces) + '): ' + s_hex, end='', flush=True)

print('\n')

s = str(bytes(best_keys.astype('uint8')))
print('\n***************************************\n')
print('KEY FOUND: ' + s)
print('\n***************************************\n')

ser.close()

if plotting:
    plt.show()
