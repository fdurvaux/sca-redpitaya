# SCA-Pitaya

The purpose of this project is to demonstrate how state-of-the-art side-channel attacks exploiting power leakages can be conducted on platforms representative of IoT devices.

## Repository organisation

The repo is organised with the following folders
1. _analysis_ holds the scripts necessary to perform the side-channel analyses and attacks.
2. _docs_ holds the extra documentation for helping in the design of the probe/pre-amplifier front-end.
3. _lib_ contains the libraries necessary for interfacing with the Red Pitaya platform as well as functions used in the side-channel analyses.
4. _targets_ holds the demonstration code adapted for the Arduino Uno and Arduino Due platforms.
5. _traces_ is the folder where all the traces and intermediate data are stored.

## Step-by-step walkthrough

### Setup preparation

1. Power up the Red Pitaya, identify its IP address, and turn on the SCPI server.
2. Connect the Arduino Uno/Due to the host computer, and identify the serial port it is connected to.
3. Place the EM probe next to a power supply pin of the target.
4. Connect the pre-amplifier output to the the fast analog input 1.
5. Connect a scope probe to the digital I/O 13 of the Arduino board (the ground must be connected too).
On the scope side, the probe should be connected on the fast analog input 2.

### Trace acquisition



### Analyses and attacks
