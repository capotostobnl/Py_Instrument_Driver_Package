# instrument-package

A Python suite of instrument drivers for controlling lab equipment using PyVISA. This package centralizes drivers for various DMMs, power supplies, function generators, oscilloscopes, and more, allowing for clean, modular testing and automation scripts.

# Installation

This package is intended to be installed directly from its source repository (e.g., GitHub or a private Git server) as a Python package.

# Prerequisites

You must have PyVISA installed in your environment, and the necessary VISA library installed on your system (e.g., NI-VISA, Keysight IO Libraries).

pip install pyvisa


# Installing from Git

Install the package directly into your virtual environment from your Git repository using the editable install flag (-e) for development, or without it for production environments:

# Example command using GitHub:
pip install git+[https://github.com/YourUsername/YourRepoName.git](https://github.com/YourUsername/YourRepoName.git)


# Usage

Once installed, you can import any of the instrument classes directly from the top-level instrument_package namespace.

## Example: Controlling the Rigol DP800 Power Supply
```py
import instrument_suite
from instrument_suite import DP800
from instrument_suite.visa_utils import list_instruments

# 1. List available instruments to find the address
list_instruments()
# e.g., ADDRESS = 'TCPIP0::10.0.142.1::INSTR'

# 2. Instantiate the driver class
psu = DP800(connection_method="IP", address="10.0.142.1")

if psu.status == "Connected":
    print(f"Connected to PSU at {psu.address}")

    # 3. Use the driver methods
    psu.set_voltage(chan=1, val=5.0)
    psu.toggle_output(chan=1, val="ON")

    voltage = psu.meas_voltage(chan=1)
    print(f"Channel 1 measured voltage: {voltage} V")

    psu.toggle_output(chan=1, val="OFF")
else:
    print("Could not connect to instrument.")
```

# Included Instrument Modules

| Driver Class | Module File | Instrument Type | Supported Models | 
| ----- | ----- | ----- | ----- | 
| `Keithley2100` | `keithley_2100.py` | Digital Multimeter (DMM) | Keithley 2100 Series | 
| `DG4000` | `rigol_dg4000.py` | Function Generator | Rigol DG4000 Series | 
| `DP800` | `rigol_dp800.py` | Power Supply Unit (PSU) | Rigol DP800 Series | 
| `DPO4000` | `Tek_DPO4000.py` | Oscilloscope | Tektronix DPO/MSO 4000 Series | 
| `Keithley6221` | `keithley_6221.py` | V/I Source | Keithley 622x Series 
| `visa_utils` | `visa_utils.py` | Helper Module | N/A |


Version: 1.0.0
