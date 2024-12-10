# PDS Development Simulator

This application is provided for development purposes. It uses Python 3.10+ and Flask to 
provide an API similar to that of PDS so that it can be used with POS and ICAPS features running 
locally.

The only requirement in the development machine is Python 3.10+ which can be downloaded from the 
main Python website:

https://www.python.org/

## Install
```bash
install.bat
```

This will create a virtual environment if one did not exist before, then will install the python 
dependencies of the application.

## Run

```bash
run.bat
```

This will run the simulator in the port 9070.

## Usage
Once running, the simulator will display the data that PDS would receive for different calls and will
allow you to enter the data (for example date of birth), or select an option for the answers to send.

There are special cases to the data entered:

* A blank space simulates the user pressing "cancel" at the payment device
* Entering "zzz" simulates a "TERMINAL IN USE" reply from PDS back

Then you will see the message being sent back.
