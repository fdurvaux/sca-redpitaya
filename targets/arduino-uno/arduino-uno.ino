/*
#
#	SIMPLE AES V5
#	AES-256
#	Re-configurable key
#	francois.durvaux@gmail.com
#	7/10/18
#
*/

#include <stdint.h>
#include <EEPROM.h>

typedef unsigned char byte;

byte state[16];
byte key[32];

const int IDLE = 0x00;
const int LOAD_KEY = 0x01; // to load key in SRAM
const int STOR_KEY = 0x02; // to load key in EEPROM
const int ENC_TXT = 0x10; // to encrypt a plaintext
const int DEC_TXT = 0x11; // to decrypt a ciphertext
const int REQ_VER = 0xff; // to request the code version

int chip_state = IDLE;
unsigned char *opcode;

byte plaintext256[] = {0x06, 0x9A, 0x00, 0x7F, 0xC7, 0x6A, 0x45, 0x9F, 0x98, 0xBA, 0xF9, 0x17, 0xFE, 0xDF, 0x95, 0x21};
byte key256[] = {0x08, 0x09, 0x0A, 0x0B, 0x0D, 0x0E, 0x0F, 0x10, 0x12, 0x13, 0x14, 0x15, 0x17, 0x18, 0x19, 0x1A, 0x1C, 0x1D, 0x1E, 0x1F, 0x21, 0x22, 0x23, 0x24, 0x26, 0x27, 0x28, 0x29, 0x2B, 0x2C, 0x2D, 0x2E};
byte ciphertext256[] = {0x08, 0x0e, 0x95, 0x17, 0xeb, 0x16, 0x77, 0x71, 0x9a, 0xcf, 0x72, 0x80, 0x86, 0x04, 0x0a, 0xe3};

const unsigned char sbox[256] = 
{
	0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76,
	0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0,
	0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15,
	0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75,
	0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84,
	0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF,
	0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8,
	0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2,
	0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73,
	0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB,
	0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79,
	0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08,
	0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A,
	0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E,
	0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF,
	0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16
};

const unsigned char sbox_i[256] = 
{
	0x52, 0x09, 0x6A, 0xD5, 0x30, 0x36, 0xA5, 0x38, 0xBF, 0x40, 0xA3, 0x9E, 0x81, 0xF3, 0xD7, 0xFB,
	0x7C, 0xE3, 0x39, 0x82, 0x9B, 0x2F, 0xFF, 0x87, 0x34, 0x8E, 0x43, 0x44, 0xC4, 0xDE, 0xE9, 0xCB,
	0x54, 0x7B, 0x94, 0x32, 0xA6, 0xC2, 0x23, 0x3D, 0xEE, 0x4C, 0x95, 0x0B, 0x42, 0xFA, 0xC3, 0x4E,
	0x08, 0x2E, 0xA1, 0x66, 0x28, 0xD9, 0x24, 0xB2, 0x76, 0x5B, 0xA2, 0x49, 0x6D, 0x8B, 0xD1, 0x25,
	0x72, 0xF8, 0xF6, 0x64, 0x86, 0x68, 0x98, 0x16, 0xD4, 0xA4, 0x5C, 0xCC, 0x5D, 0x65, 0xB6, 0x92,
	0x6C, 0x70, 0x48, 0x50, 0xFD, 0xED, 0xB9, 0xDA, 0x5E, 0x15, 0x46, 0x57, 0xA7, 0x8D, 0x9D, 0x84,
	0x90, 0xD8, 0xAB, 0x00, 0x8C, 0xBC, 0xD3, 0x0A, 0xF7, 0xE4, 0x58, 0x05, 0xB8, 0xB3, 0x45, 0x06,
	0xD0, 0x2C, 0x1E, 0x8F, 0xCA, 0x3F, 0x0F, 0x02, 0xC1, 0xAF, 0xBD, 0x03, 0x01, 0x13, 0x8A, 0x6B,
	0x3A, 0x91, 0x11, 0x41, 0x4F, 0x67, 0xDC, 0xEA, 0x97, 0xF2, 0xCF, 0xCE, 0xF0, 0xB4, 0xE6, 0x73,
	0x96, 0xAC, 0x74, 0x22, 0xE7, 0xAD, 0x35, 0x85, 0xE2, 0xF9, 0x37, 0xE8, 0x1C, 0x75, 0xDF, 0x6E,
	0x47, 0xF1, 0x1A, 0x71, 0x1D, 0x29, 0xC5, 0x89, 0x6F, 0xB7, 0x62, 0x0E, 0xAA, 0x18, 0xBE, 0x1B,
	0xFC, 0x56, 0x3E, 0x4B, 0xC6, 0xD2, 0x79, 0x20, 0x9A, 0xDB, 0xC0, 0xFE, 0x78, 0xCD, 0x5A, 0xF4,
	0x1F, 0xDD, 0xA8, 0x33, 0x88, 0x07, 0xC7, 0x31, 0xB1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xEC, 0x5F,
	0x60, 0x51, 0x7F, 0xA9, 0x19, 0xB5, 0x4A, 0x0D, 0x2D, 0xE5, 0x7A, 0x9F, 0x93, 0xC9, 0x9C, 0xEF,
	0xA0, 0xE0, 0x3B, 0x4D, 0xAE, 0x2A, 0xF5, 0xB0, 0xC8, 0xEB, 0xBB, 0x3C, 0x83, 0x53, 0x99, 0x61,
	0x17, 0x2B, 0x04, 0x7E, 0xBA, 0x77, 0xD6, 0x26, 0xE1, 0x69, 0x14, 0x63, 0x55, 0x21, 0x0C, 0x7D
};

const unsigned char gmul2[256] =
{
	0x00, 0x02, 0x04, 0x06, 0x08, 0x0a, 0x0c, 0x0e, 0x10, 0x12, 0x14, 0x16, 0x18, 0x1a, 0x1c, 0x1e,
	0x20, 0x22, 0x24, 0x26, 0x28, 0x2a, 0x2c, 0x2e, 0x30, 0x32, 0x34, 0x36, 0x38, 0x3a, 0x3c, 0x3e,
	0x40, 0x42, 0x44, 0x46, 0x48, 0x4a, 0x4c, 0x4e, 0x50, 0x52, 0x54, 0x56, 0x58, 0x5a, 0x5c, 0x5e,
	0x60, 0x62, 0x64, 0x66, 0x68, 0x6a, 0x6c, 0x6e, 0x70, 0x72, 0x74, 0x76, 0x78, 0x7a, 0x7c, 0x7e,
	0x80, 0x82, 0x84, 0x86, 0x88, 0x8a, 0x8c, 0x8e, 0x90, 0x92, 0x94, 0x96, 0x98, 0x9a, 0x9c, 0x9e,
	0xa0, 0xa2, 0xa4, 0xa6, 0xa8, 0xaa, 0xac, 0xae, 0xb0, 0xb2, 0xb4, 0xb6, 0xb8, 0xba, 0xbc, 0xbe,
	0xc0, 0xc2, 0xc4, 0xc6, 0xc8, 0xca, 0xcc, 0xce, 0xd0, 0xd2, 0xd4, 0xd6, 0xd8, 0xda, 0xdc, 0xde,
	0xe0, 0xe2, 0xe4, 0xe6, 0xe8, 0xea, 0xec, 0xee, 0xf0, 0xf2, 0xf4, 0xf6, 0xf8, 0xfa, 0xfc, 0xfe,
	0x1b, 0x19, 0x1f, 0x1d, 0x13, 0x11, 0x17, 0x15, 0x0b, 0x09, 0x0f, 0x0d, 0x03, 0x01, 0x07, 0x05,
	0x3b, 0x39, 0x3f, 0x3d, 0x33, 0x31, 0x37, 0x35, 0x2b, 0x29, 0x2f, 0x2d, 0x23, 0x21, 0x27, 0x25,
	0x5b, 0x59, 0x5f, 0x5d, 0x53, 0x51, 0x57, 0x55, 0x4b, 0x49, 0x4f, 0x4d, 0x43, 0x41, 0x47, 0x45,
	0x7b, 0x79, 0x7f, 0x7d, 0x73, 0x71, 0x77, 0x75, 0x6b, 0x69, 0x6f, 0x6d, 0x63, 0x61, 0x67, 0x65,
	0x9b, 0x99, 0x9f, 0x9d, 0x93, 0x91, 0x97, 0x95, 0x8b, 0x89, 0x8f, 0x8d, 0x83, 0x81, 0x87, 0x85,
	0xbb, 0xb9, 0xbf, 0xbd, 0xb3, 0xb1, 0xb7, 0xb5, 0xab, 0xa9, 0xaf, 0xad, 0xa3, 0xa1, 0xa7, 0xa5,
	0xdb, 0xd9, 0xdf, 0xdd, 0xd3, 0xd1, 0xd7, 0xd5, 0xcb, 0xc9, 0xcf, 0xcd, 0xc3, 0xc1, 0xc7, 0xc5,
	0xfb, 0xf9, 0xff, 0xfd, 0xf3, 0xf1, 0xf7, 0xf5, 0xeb, 0xe9, 0xef, 0xed, 0xe3, 0xe1, 0xe7, 0xe5
};

const unsigned char gmul3[256] =
{
	0x00, 0x03, 0x06, 0x05, 0x0c, 0x0f, 0x0a, 0x09, 0x18, 0x1b, 0x1e, 0x1d, 0x14, 0x17, 0x12, 0x11,
	0x30, 0x33, 0x36, 0x35, 0x3c, 0x3f, 0x3a, 0x39, 0x28, 0x2b, 0x2e, 0x2d, 0x24, 0x27, 0x22, 0x21,
	0x60, 0x63, 0x66, 0x65, 0x6c, 0x6f, 0x6a, 0x69, 0x78, 0x7b, 0x7e, 0x7d, 0x74, 0x77, 0x72, 0x71,
	0x50, 0x53, 0x56, 0x55, 0x5c, 0x5f, 0x5a, 0x59, 0x48, 0x4b, 0x4e, 0x4d, 0x44, 0x47, 0x42, 0x41,
	0xc0, 0xc3, 0xc6, 0xc5, 0xcc, 0xcf, 0xca, 0xc9, 0xd8, 0xdb, 0xde, 0xdd, 0xd4, 0xd7, 0xd2, 0xd1,
	0xf0, 0xf3, 0xf6, 0xf5, 0xfc, 0xff, 0xfa, 0xf9, 0xe8, 0xeb, 0xee, 0xed, 0xe4, 0xe7, 0xe2, 0xe1,
	0xa0, 0xa3, 0xa6, 0xa5, 0xac, 0xaf, 0xaa, 0xa9, 0xb8, 0xbb, 0xbe, 0xbd, 0xb4, 0xb7, 0xb2, 0xb1,
	0x90, 0x93, 0x96, 0x95, 0x9c, 0x9f, 0x9a, 0x99, 0x88, 0x8b, 0x8e, 0x8d, 0x84, 0x87, 0x82, 0x81,
	0x9b, 0x98, 0x9d, 0x9e, 0x97, 0x94, 0x91, 0x92, 0x83, 0x80, 0x85, 0x86, 0x8f, 0x8c, 0x89, 0x8a,
	0xab, 0xa8, 0xad, 0xae, 0xa7, 0xa4, 0xa1, 0xa2, 0xb3, 0xb0, 0xb5, 0xb6, 0xbf, 0xbc, 0xb9, 0xba,
	0xfb, 0xf8, 0xfd, 0xfe, 0xf7, 0xf4, 0xf1, 0xf2, 0xe3, 0xe0, 0xe5, 0xe6, 0xef, 0xec, 0xe9, 0xea,
	0xcb, 0xc8, 0xcd, 0xce, 0xc7, 0xc4, 0xc1, 0xc2, 0xd3, 0xd0, 0xd5, 0xd6, 0xdf, 0xdc, 0xd9, 0xda,
	0x5b, 0x58, 0x5d, 0x5e, 0x57, 0x54, 0x51, 0x52, 0x43, 0x40, 0x45, 0x46, 0x4f, 0x4c, 0x49, 0x4a,
	0x6b, 0x68, 0x6d, 0x6e, 0x67, 0x64, 0x61, 0x62, 0x73, 0x70, 0x75, 0x76, 0x7f, 0x7c, 0x79, 0x7a,
	0x3b, 0x38, 0x3d, 0x3e, 0x37, 0x34, 0x31, 0x32, 0x23, 0x20, 0x25, 0x26, 0x2f, 0x2c, 0x29, 0x2a,
	0x0b, 0x08, 0x0d, 0x0e, 0x07, 0x04, 0x01, 0x02, 0x13, 0x10, 0x15, 0x16, 0x1f, 0x1c, 0x19, 0x1a
};

const unsigned char rcon[16] = {
	0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36, 0x6c, 0xd8, 0xab, 0x4d, 0x9a
};

void KeySchedule(byte *expandedKey, int NROUNDS, int KEY_BYTES)
{
	int rcon_i = 1;
	int bytes_done = KEY_BYTES;

	while (bytes_done < (NROUNDS+1)*16) {
		if (bytes_done % KEY_BYTES == 0) {
			expandedKey[bytes_done] = sbox[expandedKey[bytes_done-3]] ^ rcon[rcon_i];
			expandedKey[bytes_done+1] = sbox[expandedKey[bytes_done-2]];
			expandedKey[bytes_done+2] = sbox[expandedKey[bytes_done-1]];
			expandedKey[bytes_done+3] = sbox[expandedKey[bytes_done-4]];
			rcon_i++;
		}
		else {
			for (int i=0; i<4; i++) {
				expandedKey[bytes_done+i] = expandedKey[bytes_done-4+i];
			}
		}
		if ((KEY_BYTES == 32) && (bytes_done % KEY_BYTES == 16)) {
			for (int i=0; i<4; i++) {
				expandedKey[bytes_done+i] = sbox[expandedKey[bytes_done+i]];	
			}
		}
		for (int i=0; i<4; i++) {
			expandedKey[bytes_done+i] ^= expandedKey[bytes_done-KEY_BYTES+i];	
		}
		bytes_done += 4;
	}
}

void AddRoundKey(byte *state, byte *roundKey)
{
	for (int i=0; i<16; i++) {
		state[i] ^= roundKey[i];
	}
}

void SubBytes(byte *state)
{
	for (int i=0; i<16; i++) {
		state[i] = sbox[state[i]];
	}
}

void SubBytes_i(byte *state)
{
	for (int i=0; i<16; i++) {
		state[i] = sbox_i[state[i]];
	}
}

void ShiftRows(byte *state)
{
	//  _____________
	// |0	4	8	12
	// |1	5	9	13
	// |2	6	10	14
	// |3	7	11	15

	byte t;

	// second row << 1
	t = state[1];
	state[1] = state[5];
	state[5] = state[9];
	state[9] = state[13];
	state[13] = t;

	// third row << 2
	t = state[2];
	state[2] = state[10];
	state[10] = t;
	t = state[6];
	state[6] = state[14];
	state[14] = t;

	// fourth row << 3
	t = state[3];
	state[3] = state[15];
	state[15] = state[11];
	state[11] = state[7];
	state[7] = t;
}

void ShiftRows_i(byte *state)
{
	//  _____________
	// |0	4	8	12
	// |1	5	9	13
	// |2	6	10	14
	// |3	7	11	15

	byte t;

	// second row >> 1
	t = state[13];
	state[13] = state[9];
	state[9] = state[5];
	state[5] = state[1];
	state[1] = t;

	// third row >> 2
	t = state[14];
	state[14] = state[6];
	state[6] = t;
	t = state[10];
	state[10] = state[2];
	state[2] = t;

	// fourth row >> 3
	t = state[15];
	state[15] = state[3];
	state[3] = state[7];
	state[7] = state[11];
	state[11] = t;
}

void MixColumns(byte *state)
{
	byte c[4];

	for (int i=0; i<4; i++) {
		c[0] = state[i*4];
		c[1] = state[i*4+1];
		c[2] = state[i*4+2];
		c[3] = state[i*4+3];
		state[i*4] = gmul2[c[0]] ^ gmul3[c[1]] ^ c[2] ^ c[3];
		state[i*4+1] = c[0] ^ gmul2[c[1]] ^ gmul3[c[2]] ^ c[3];
		state[i*4+2] = c[0] ^ c[1] ^ gmul2[c[2]] ^ gmul3[c[3]];
		state[i*4+3] = gmul3[c[0]] ^ c[1] ^ c[2] ^ gmul2[c[3]];
	}
}

void MixColumns_i(byte *state)
{
	byte c[4];

	for (int i=0; i<4; i++) {
		c[0] = state[i*4];
		c[1] = state[i*4+1];
		c[2] = state[i*4+2];
		c[3] = state[i*4+3];

		state[i*4] =	gmul2[gmul2[gmul2[c[3]]]] ^ c[3] // gmul9
						^ gmul2[gmul2[gmul2[c[1]]] ^ c[1]] ^ c[1] // gmul11
						^ gmul2[gmul2[gmul2[c[2]] ^ c[2]]] ^ c[2] // gmul13
						^ gmul2[gmul2[gmul2[c[0]] ^ c[0]] ^ c[0]]; // gmul14

		state[i*4+1] =	gmul2[gmul2[gmul2[c[0]]]] ^ c[0] // gmul9
						^ gmul2[gmul2[gmul2[c[2]]] ^ c[2]] ^ c[2] // gmul11
						^ gmul2[gmul2[gmul2[c[3]] ^ c[3]]] ^ c[3] // gmul13
						^ gmul2[gmul2[gmul2[c[1]] ^ c[1]] ^ c[1]]; // gmul14

		state[i*4+2] =	gmul2[gmul2[gmul2[c[1]]]] ^ c[1] // gmul9
						^ gmul2[gmul2[gmul2[c[3]]] ^ c[3]] ^ c[3] // gmul11
						^ gmul2[gmul2[gmul2[c[0]] ^ c[0]]] ^ c[0] // gmul13
						^ gmul2[gmul2[gmul2[c[2]] ^ c[2]] ^ c[2]]; // gmul14

		state[i*4+3] =	gmul2[gmul2[gmul2[c[2]]]] ^ c[2] // gmul9
						^ gmul2[gmul2[gmul2[c[0]]] ^ c[0]] ^ c[0] // gmul11
						^ gmul2[gmul2[gmul2[c[1]] ^ c[1]]] ^ c[1] // gmul13
						^ gmul2[gmul2[gmul2[c[3]] ^ c[3]] ^ c[3]]; // gmul14
	}
}

void Rounds(byte *state, byte *expandedKey, int NROUNDS)
{
	for (int r_i=0; r_i<NROUNDS; r_i++) {
		AddRoundKey(state, &expandedKey[r_i*16]);
		SubBytes(state);
		ShiftRows(state);
		if(r_i<NROUNDS-1) {
			MixColumns(state);
		}
	}
	AddRoundKey(state, &expandedKey[NROUNDS*16]);
}

void Rounds_i(byte *state, byte *expandedKey, int NROUNDS)
{
	for (int r_i=0; r_i<NROUNDS; r_i++) {
		AddRoundKey(state, &expandedKey[(NROUNDS-r_i)*16]);
		if(r_i>0) {
			MixColumns_i(state);
		}
		ShiftRows_i(state);
		SubBytes_i(state);
	}
	AddRoundKey(state, &expandedKey[0]);
}

int AES_Encrypt(byte *state, byte *key, int keySize)
{
	int NROUNDS;
	int KEY_BYTES;

	switch (keySize) {
		case 128:
			NROUNDS = 10;
			KEY_BYTES = 16;
			break;
		case 192:
			NROUNDS = 12;
			KEY_BYTES = 24;
			break;
		case 256:
			NROUNDS = 14;
			KEY_BYTES = 32;
			break;
		default:
			return -1;
			break;
	}

	// Key expansion
	byte expandedKey[16*(NROUNDS+1)];
	for (int i=0; i<KEY_BYTES; i++) {
		expandedKey[i] = key[i];
	}
	KeySchedule(expandedKey,NROUNDS,KEY_BYTES);

	// Set trigger to high
	digitalWrite(13,HIGH);

	// Rounds
	Rounds(state,expandedKey,NROUNDS);

	return 0;
}

int AES_Decrypt(byte *state, byte *key, int keySize)
{
	int NROUNDS;
	int KEY_BYTES;

	switch (keySize) {
		case 128:
			NROUNDS = 10;
			KEY_BYTES = 16;
			break;
		case 192:
			NROUNDS = 12;
			KEY_BYTES = 24;
			break;
		case 256:
			NROUNDS = 14;
			KEY_BYTES = 32;
			break;
		default:
			return -1;
			break;
	}

	// Key expansion
	byte expandedKey[16*(NROUNDS+1)];
	for (int i=0; i<KEY_BYTES; i++) {
		expandedKey[i] = key[i];
	}
	KeySchedule(expandedKey,NROUNDS,KEY_BYTES);

	// Set trigger to high
	digitalWrite(13,HIGH);

	// Rounds
	Rounds_i(state,expandedKey,NROUNDS);

	return 0;
}

void setup() {

	pinMode(13, OUTPUT);
	digitalWrite(13,LOW);

	// loading of the key stored in EEPROM (used STOR_KEY to change this value)
	for(int k_i=0; k_i<32; k_i++) {
		key[k_i] = EEPROM[k_i];
	}

	Serial.begin(19200);
	while (!Serial) {
		; // wait for serial port to connect. Needed for native USB
	}
	Serial.write("Arduino is ready!\n");

}

void loop() {

	int tmp = 0;

	switch(chip_state) {
		case IDLE:
			if(Serial.available() == 1) {
				Serial.readBytes(opcode,1);
				switch(*opcode) {
					case LOAD_KEY:
						Serial.write("ACK: LOAD KEY\n");
						chip_state = LOAD_KEY;
						break;
					case STOR_KEY:
						Serial.write("ACK: STORE KEY\n");
						chip_state = STOR_KEY;
						break;
					case ENC_TXT:
						Serial.write("ACK: ENCRYPT TEXT\n");
						chip_state = ENC_TXT;	
						break;
					case DEC_TXT:
						Serial.write("ACK: DECRYPT TEXT\n");
						chip_state = DEC_TXT;	
						break;
					case REQ_VER:
						Serial.write("ACK: SIMPLE AES V5\n");
						chip_state = IDLE;
						break;
					default:
						Serial.write("ERR: unknown opcode ");
						Serial.write(*opcode);
						Serial.write("\n");
						chip_state = IDLE;
				}
			}
			break;

		case LOAD_KEY:
			if(Serial.available() == 32) {
				Serial.readBytes(key,32);
				Serial.write("ACK: KEY SUCCESSFULLY LOADED IN SRAM\n");
				chip_state = IDLE;
			}
			break;

		case STOR_KEY:
			if(Serial.available() == 32) {
				Serial.readBytes(key,32);
				for(int k_i=0; k_i<32; k_i++) {
					EEPROM[k_i] = key[k_i];
				}
				Serial.write("ACK: KEY SUCCESSFULLY STORED IN EEPROM\n");
				chip_state = IDLE;
			}
			break;

		case ENC_TXT:
			if(Serial.available() == 16) {

				Serial.readBytes(state,16);

				AES_Encrypt(state,key,256);

				// Set trigger to low
				digitalWrite(13,LOW);

				Serial.write(state,16);

				chip_state = IDLE;
			}
			break;

		case DEC_TXT:
			if(Serial.available() == 16) {

				Serial.readBytes(state,16);

				AES_Decrypt(state,key,256);

				// Set trigger to low
				digitalWrite(13,LOW);

				Serial.write(state,16);

				chip_state = IDLE;
			}
			break;

		default:
			chip_state = IDLE;
	}
	
}
