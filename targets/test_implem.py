import sys
import serial
import time
import numpy as np

# ser_port = '/dev/tty.usbmodem1421'
ser_port = 'COM10'
ser_baud = 19200
ser_timeout = 5

ser = serial.Serial(ser_port, ser_baud, timeout=ser_timeout)
print('Serial connection open on ' + ser.name)

LOAD_KEY = bytes([0x01])
STOR_KEY = bytes([0x02])
ENC_TXT = bytes([0x10])
DEC_TXT = bytes([0x11])
REQ_VER = bytes([0xff])

s = ser.readline()
print(s[:-1].decode())

ser.write(REQ_VER)
s = ser.readline()
print(s)

key256 = bytes([0x08, 0x09, 0x0A, 0x0B, 0x0D, 0x0E, 0x0F, 0x10, 0x12, 0x13, 0x14, 0x15, 0x17, 0x18, 0x19, 0x1A, 0x1C, 0x1D, 0x1E, 0x1F, 0x21, 0x22, 0x23, 0x24, 0x26, 0x27, 0x28, 0x29, 0x2B, 0x2C, 0x2D, 0x2E])
plaintext256 = bytes([0x06, 0x9A, 0x00, 0x7F, 0xC7, 0x6A, 0x45, 0x9F, 0x98, 0xBA, 0xF9, 0x17, 0xFE, 0xDF, 0x95, 0x21])
ciphertext256 = bytes([0x08, 0x0e, 0x95, 0x17, 0xeb, 0x16, 0x77, 0x71, 0x9a, 0xcf, 0x72, 0x80, 0x86, 0x04, 0x0a, 0xe3])

key = np.random.bytes(32)
ser.write(LOAD_KEY)
s = ser.readline()
print(s)
ser.write(key256)
s = ser.readline()
print(s)

ser.write(ENC_TXT)
s = ser.readline()
print(s)
ser.write(plaintext256)

s = ser.read(16)

nt = 10000

if(s==ciphertext256):
    print("AES-256 ready!")
    print("Plaintext successfully encrypted.\n")

    for i in range(nt):
        print('REQ ' + str(i) + ' on ' + str(nt-1))

        key = np.random.bytes(32)
        s_hex = ["key: " + "".join('%02x ' % b for b in key)]
        print(s_hex)
        
        ser.write(LOAD_KEY)
        s = ser.readline()
        ser.write(key)
        s = ser.readline()

        plaintext = np.random.bytes(16)
        s_hex = ["plaintext: " + "".join('%02x ' % b for b in plaintext)]
        print(s_hex)

        ser.write(ENC_TXT)
        s = ser.readline()
        ser.write(plaintext)
        ciphertext = ser.read(16)

        s_hex = ["ciphertext: " + "".join('%02x ' % b for b in ciphertext)]
        print(s_hex)

        # ser.write(DEC_TXT)
        # s = ser.readline()
        # ser.write(ciphertext)
        # plaintext = ser.read(16)
        
        # s_hex = ["plaintext: " + "".join('%02x ' % b for b in plaintext)]
        # print(s_hex)

        print('\n')

        time.sleep(.50)

else:
    print("Ooops... Something is not right.")
    print("Please reset the Arduino board.")



ser.close()
