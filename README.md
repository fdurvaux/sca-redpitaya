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
This signal is used for triggering the acquisition.

__Note:__ The key held in the Arduino Uno can be configured (i.e. the one recovered with the attack).
For this purpose, use the "set_key.py" script that is located in the "targets" folder.

### Trace acquisition

Traces are recorded with the script called "capture_traces.py" in the "analysis" folder.

Before starting the acquisition, make sure the the following parameters are correctly set in the script:
1. On-the-fly plotting of the traces with the "plotting" parameter.
2. The Red Pitaya IP address.
3. The serial port on the Arduino target.

The acquisition is then started by executing the script with the following arguments:
1. _set_type_: "attack" or "profiling".
In the "attack" case, random plaintexts are sent to the target, the key is unknown.
In the "profiling" case, random plaintexts and random keys are sent to the target.
The latter is necessary for the training phase (see the following).
2. _n_traces_: number of traces to be acquired (integer value)
3. _ext_ (optional): extension to be added on the output file.

The output file containing the acquired traces is stored in "traces/" folder in the ".mat" format (e.g. _profiling_set_nt_10000_A.mat_).

The average trace can be inspected using the "plot_average.py" script.
Make sure that the "demodulation" and "filename" parameters are correctly set.

### Off-line CPA attack

This attack only requires that an "attack" set of traces has been taken.
It is done by executing the "attack_cpa.py" script.

First make sure that the following parameters are correctly set:
1. _n_attack_traces_: the number of traces used for the attack.
It must be lower or equal to the number of traces held in the file.
2. _demodulation_: determines whether an amplitude demodulation must be applied or not (only useful for the Arduino Uno).
3. _filename_: the name of the file in which the attack traces are held.

### On-line CPA attack

This attack requires that a "profiling" set of traces has been taken.
This set is further used during a _training phase_ which is performed by executing the following scripts:
1. "identify_pois.py": this script is used to determine the time samples that hold useful information for the attack.
First, make sure that the "demodulation" (only useful for the Arduino Uno) and "filename" parameters are correctly set.
The points-of-interest are stored in a file "POIs.mat" in the "traces/" folder. 
2. "extract_best_cpa_points.py": this script is used to find a liner projection of the POIs held in "traces/POIs.mat" in order to maximise the efficiency of a CPA attack. First, make sure that the "demodulation" (only useful for the Arduino Uno) and "filename" (of the profiling set) parameters are correctly set.
The projection profiles are stored in "traces/PP_CPA.mat".

Once the two previous scripts have been executed, the on-line attack is possible.

