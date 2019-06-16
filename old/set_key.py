import sys
import serial

def LoadKey(ser_port, key):
	ser_baud = 19200
	ser_timeout = 5
	ser = serial.Serial(ser_port, ser_baud, timeout=ser_timeout)
	print('Serial connection open on ' + ser.name)
	s = ser.readline()

	key = key.encode('utf-8')


	if len(key) > 32:
		key = key[:32]
	elif len(key) < 32:
		key = key + bytes(' ','utf-8')*(32-len(key))

	STOR_KEY = bytes([0x02])
	ser.write(STOR_KEY)
	s = ser.readline()

	ser.write(key)
	s = ser.readline()

	if(s[:3].decode()=='ACK'):
		print('Key "' + key.decode() + '" successfully written on ' + ser_port + '!')
	else:
		print('Error while storing the key on ' + ser_port + '!')

	ser.close()

	print('Connection with ' + ser_port + ' closed.')



if __name__ == "__main__":
	if len(sys.argv) < 3 or len(sys.argv) >= 4:
		print('\n*** ERROR ***')
		print('Usage: "python set_key.py serial_port key_value"\n')
		print('Both arguments are strings:')
		print('\t- serial_port: e.g. "COM3" (Windows) or "/dev/tty.usbmodem1421" (OSX)')
		print('\t- key_value: e.g. "MySuperAwesomeKey"\n')
		exit()

	ser_port = sys.argv[1]
	key = sys.argv[2]
	
	LoadKey(ser_port, key)
