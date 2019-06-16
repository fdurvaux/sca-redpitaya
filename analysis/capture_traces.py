import sys
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

# plotting traces on-the-fly takes resources and may lower the acquisition speed.
# set the "plotting" variable to "False" to disable it.
plotting = True

def capture_traces(profiling=False, n_traces=1000, ext=''):

    # for dynamic plotting of traces
    if(plotting):
        plt.ion()
        plt.show()

    print('\n==============================')
    print('=                            =')
    print('=     TRACES ACQUISITION     =')
    print('=                            =')
    print('==============================\n')

    if(ext != ''):
        print('Set extension: ' + ext)

    # input('Press enter to proceed...\n')

    if plotting:
        plt.figure(1)
        plt.xticks([])
        plt.yticks([])
        plt.text(0.4,0.5,'Press enter to proceed...')
        input('Press enter to proceed...\n')

    # connection info to Red Pitaya
    # SCPI server should run
    rp_addr = '192.168.1.6'
    rp_port = 5000
    rp_timeout = 5
    rp_s = scpi.scpi(rp_addr, timeout=rp_timeout, port=rp_port)
    rp_s.tx_txt('ACQ:RST')

    # connection info to Arduino
    # ser_port = '/dev/tty.usbmodem14101'
    ser_port = 'COM5'
    ser_baud = 19200
    ser_timeout = 5
    ser = serial.Serial(ser_port, ser_baud, timeout=ser_timeout)
    s = ser.readline()
    print(s.decode())

    # commands for Arduino
    LOAD_KEY = bytes([0x01])
    STOR_KEY = bytes([0x02])
    ENC_TXT = bytes([0x10])
    DEC_TXT = bytes([0x11])
    REQ_VER = bytes([0xff])

    # preparation of the demodulation parameters (only for display)
    fs = 125 # sampling frequency [MHz]
    cutoff = 10 # cutoff frequency [MHz]
    width = 4 # transition width [MHz]
    attenuation = 65 # stop band attenuation [dB]

    # trace acquisition parameters
    nt = n_traces # total number of traces
    nl = 16384 # number of samples per trace

    if(profiling):
        print('CAPTURING PROFILING TRACES')
        filename = '../traces/profiling_set_nt_' + str(nt) + ext + '.mat'
    else:
        print('CAPTURING ATTACK TRACES')
        filename = '../traces/attack_set_nt_' + str(nt) + ext + '.mat'

    traces = np.zeros((nt,nl))
    traces_sum = np.zeros(nl)
    traces_sum2 = np.zeros(nl)

    if(profiling):
        keys = np.zeros((nt,32))
    plaintexts = np.zeros((nt,16))
    ciphertexts = np.zeros((nt,16))

    # for handling timeout with red pitaya commands
    acquisitionDone = False
    timeoutInARow = 0
    maxTimeoutInARow = 5

    for i in range(nt):
        print('-------------------------')
        print('Trace ' + str(i+1) + ' (' + str(nt) + ')')
        print('-------------------------')

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
                rp_s.tx_txt('ACQ:TRIG:DLY?')
                data = rp_s.rx_txt()
                # print('Trigger delay ' + data)
                rp_s.tx_txt('ACQ:TRIG CH2_PE')
                rp_s.tx_txt('ACQ:TRIG:STAT?')
                data = rp_s.rx_txt()
                # print('Trigger status ' + data)

                # sending key
                if(profiling):
                    key = np.random.bytes(32)
                    ser.write(LOAD_KEY)
                    s = ser.readline()
                    print(s.decode()[:-1])
                    ser.write(key)
                    s = ser.readline()
                    print(s.decode()[:-1])
                    s_hex = "KEY: " + "".join('%02x ' % b for b in key)
                    print(s_hex)

                # sending plaintext
                plaintext = np.random.bytes(16)
                ser.write(ENC_TXT)
                s = ser.readline()
                print(s.decode()[:-1])
                ser.write(plaintext)
                ptx = "".join('%02x ' % b for b in plaintext)
                s_hex = "PTX: " + ptx
                print(s_hex)

                # waiting 1ms to make the AES execution is complete
                time.sleep(0.001)

                # ciphertext recovery
                ciphertext = ser.read(16)
                ctx = "".join('%02x ' % b for b in ciphertext)
                s_hex = "CTX: " + ctx
                print(s_hex)

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

        if(profiling):
            keys[i,:] = np.frombuffer(key, dtype=np.uint8).astype(float)
        plaintexts[i,:] = np.frombuffer(plaintext, dtype=np.uint8).astype(float)
        ciphertexts[i,:] = np.frombuffer(ciphertext, dtype=np.uint8).astype(float)

        traces[i,:] = trace
        
        # trace demodulation (only for display)
        trace_demodulated = sca.kaiser_LP_filter(np.absolute(trace),fs,cutoff,width,attenuation)

        traces_sum += trace_demodulated
        traces_sum2 += trace_demodulated**2
        traces_avg = traces_sum/(i+1)
        traces_var = traces_sum2/(i+1)-traces_avg**2

        if(plotting):  
            
            plt.figure(1)
            plt.clf()

            plt.subplot(2,1,1)
            plt.title('Trace ' + str(i) + ' (' + str(nt) + ')',fontsize=20)
            plt.axis([0,nl,0,0.06])
            plt.plot(trace_demodulated)
            plt.ylabel('demodulated',fontsize=15)
            plt.tick_params(axis='both', which='both', bottom=False, top=False, left = False, right = False, labelleft = False, labelbottom=False)
            
            plt.subplot(2,1,2)
            plt.axis([0,nl,0,0.05])
            plt.plot(traces_avg)
            plt.ylabel('average',fontsize=15)
            plt.xlabel('time samples',fontsize=15)
            plt.tick_params(axis='both', which='both', bottom=False, top=False, left = False, right = False, labelleft = False, labelbottom=False)

            plt.draw()
            plt.pause(0.01)

    if(profiling):
      sio.savemat(filename, dict([
          ('nt', nt),
          ('nl', nl),
          ('keys', keys),
          ('plaintexts', plaintexts),
          ('ciphertexts', ciphertexts),
          ('traces', traces)]))
    else:
      sio.savemat(filename, dict([
          ('nt', nt),
          ('nl', nl),
          ('plaintexts', plaintexts),
          ('ciphertexts', ciphertexts),
          ('traces', traces)]))

    print('\nTraces saved in ' + filename + '\n')

    ser.close()



if __name__ == "__main__":
    if (len(sys.argv) < 3 or len(sys.argv) > 4):
        print('Usage: "python capture_traces.py set_type n_traces ext"\n')
        print('Arguments are of the following type:')
        print('\t- set_type: "attack" or "profiling", any other is rejected')
        print('\t- n_traces: number of traces (integer), e.g. 5000')
        print('\t- ext (optional): output file extension, e.g. "_A"\n')
        exit()

    set_type = sys.argv[1]
    n_traces = int(sys.argv[2])

    profiling = False
    if(set_type=='profiling'):
        profiling = True
    elif(set_type=='attack'):
        profiling = False
    else:
        print('Unknwon set_type. Only "attack" or "profiling" are recognised as valid.')
        exit()

    if (len(sys.argv) < 4):
        ext = ''
    else:
        ext = sys.argv[3]

    capture_traces(profiling, n_traces, ext)
