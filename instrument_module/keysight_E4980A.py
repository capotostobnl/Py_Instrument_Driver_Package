"""This module is for implementing remote control of Keysight E4980A
series Precision LCR Meters.

M. Capotosto
8/29/2026
NSLS-II Diagnostics and Instrumentation
"""

from time import sleep
from .visa_utils import connect_ethernet_instrument

DELAY = 0.01  # 10ms delay


class KeysightE4980A:
    """Create LCR Meter Class"""

    MEASUREMENT_FUNCTIONS = (
        "CPD", "CPQ", "CPG", "CPRP",
        "CSD", "CSQ", "CSRS",
        "LPD", "LPQ", "LPG", "LPRP", "LPRD",
        "LSD", "LSQ", "LSRS", "LSRD",
        "RX", "ZTD", "ZTR", "GB", "YTD", "YTR", "VDID"
    )

    LOAD_CORRECTION_FUNCTIONS = (
        "CPD", "CPQ", "CPG", "CPRP",
        "CSD", "CSQ", "CSRS",
        "LPD", "LPQ", "LPG", "LPRP",
        "LSD", "LSQ", "LSRS",
        "RX", "ZTD", "ZTR", "GB", "YTD", "YTR"
    )

    MEASUREMENT_STATUS = {
        -1: "No data",
        0: "Normal",
        1: "Overload",
        3: "Signal source overloaded",
        4: "ALC unable to regulate",
    }

    # *************************************************************************
    # ******Initialize Connection******
    def __init__(self, connection_method, address):
        self.device = None
        self.address = address
        self.status = "Disconnected"
        self.connected_with = None

        if connection_method == "IP":
            self.device, self.address, self.status = \
                connect_ethernet_instrument(address)
            self.connected_with = 'Ethernet' \
                if self.status == "Connected" else None

    # *************************************************************************
    # ******Internal Helpers******
    def _write(self, command):
        """Write a SCPI command to the instrument."""
        response = self.device.write(command)
        sleep(DELAY)
        return response

    def _query(self, command):
        """Query the instrument and return the stripped response."""
        response = self.device.query(command)
        sleep(DELAY)
        return response.strip()

    @staticmethod
    def _state_value(state):
        """Convert a Python/string state to an SCPI ON/OFF value."""
        if state in (True, 1, "1", "ON", "On", "on"):
            return "ON"
        if state in (False, 0, "0", "OFF", "Off", "off"):
            return "OFF"
        raise ValueError("State must be ON/OFF, True/False, or 1/0.")

    @staticmethod
    def _parse_state(response):
        """Convert an instrument state response to a boolean."""
        value = response.strip().upper()
        if value in ("1", "ON"):
            return True
        if value in ("0", "OFF"):
            return False
        raise ValueError(f"Unexpected instrument state response: {response}")

    # *************************************************************************
    # ******IEEE 488.2 Common Commands******
    def idn(self):
        """Query the instrument identification string."""
        command = "*IDN?"
        idn_response = self._query(command)
        return idn_response

    def get_idn(self):
        """Query the instrument identification string."""
        return self.idn()

    def reset(self):
        """Reset the instrument to its default state."""
        command = "*RST"
        return self._write(command)

    def clear_status(self):
        """Clear the instrument status registers and error queue."""
        command = "*CLS"
        return self._write(command)

    def operation_complete(self):
        """Wait for pending operations to complete."""
        command = "*OPC?"
        opc = self._query(command)
        return bool(int(opc))

    def wait(self):
        """Wait for all pending commands to complete before continuing."""
        command = "*WAI"
        return self._write(command)

    def trigger_bus(self):
        """Generate an IEEE 488.2 bus trigger."""
        command = "*TRG"
        return self._write(command)

    def get_options(self):
        """Query installed instrument options."""
        command = "*OPT?"
        options = self._query(command)
        return options

    def get_status_byte(self):
        """Query the IEEE 488.2 status byte register."""
        command = "*STB?"
        status_byte = int(self._query(command))
        return status_byte

    def get_standard_event_status(self):
        """Query the IEEE 488.2 standard event status register."""
        command = "*ESR?"
        event_status = int(self._query(command))
        return event_status

    def self_test(self):
        """Run the instrument self-test and return the result."""
        command = "*TST?"
        test_result = int(self._query(command))
        return test_result

    # *************************************************************************
    # ******System Commands******
    def get_system_error(self):
        """Read one entry from the instrument error queue."""
        command = ":SYSTem:ERRor?"
        error = self._query(command)
        return error

    def get_all_system_errors(self):
        """Read the error queue until the instrument reports no error."""
        errors = []

        while True:
            error = self.get_system_error()
            errors.append(error)

            error_code = int(error.split(",", 1)[0])
            if error_code == 0:
                break

        return errors

    # *************************************************************************
    # ******Measurement Function******
    def set_measurement_function(self, function):
        """Set the impedance measurement function."""
        function = function.upper()

        if function not in self.MEASUREMENT_FUNCTIONS:
            raise ValueError(
                "Invalid measurement function. Valid functions are: "
                + ", ".join(self.MEASUREMENT_FUNCTIONS)
            )

        command = f":FUNCtion:IMPedance {function}"
        return self._write(command)

    def get_measurement_function(self):
        """Query the impedance measurement function."""
        command = ":FUNCtion:IMPedance?"
        function = self._query(command)
        return function.strip('"').upper()

    # *************************************************************************
    # ******Test Frequency******
    def set_frequency(self, frequency):
        """Set the measurement frequency in Hz."""
        command = f":FREQuency {frequency}"
        return self._write(command)

    def get_frequency(self):
        """Query the measurement frequency in Hz."""
        command = ":FREQuency?"
        frequency = float(self._query(command))
        return frequency

    # *************************************************************************
    # ******Measurement Signal Level******
    def set_voltage_level(self, voltage):
        """Set the AC test signal voltage level in volts."""
        command = f":VOLTage:LEVel {voltage}"
        return self._write(command)

    def get_voltage_level(self):
        """Query the AC test signal voltage level in volts."""
        command = ":VOLTage:LEVel?"
        voltage = float(self._query(command))
        return voltage

    def set_current_level(self, current):
        """Set the AC test signal current level in amperes."""
        command = f":CURRent:LEVel {current}"
        return self._write(command)

    def get_current_level(self):
        """Query the AC test signal current level in amperes."""
        command = ":CURRent:LEVel?"
        current = float(self._query(command))
        return current

    def set_alc(self, state):
        """Enable or disable automatic level control."""
        state = self._state_value(state)
        command = f":AMPLitude:ALC {state}"
        return self._write(command)

    def get_alc(self):
        """Query automatic level control state."""
        command = ":AMPLitude:ALC?"
        return self._parse_state(self._query(command))

    # *************************************************************************
    # ******Measurement Time / Averaging******
    def set_aperture(self, mode, averages=1):
        """Set measurement time mode and averaging rate."""
        mode_lookup = {
            "SHORT": "SHORt",
            "SHOR": "SHORt",
            "MEDIUM": "MEDium",
            "MED": "MEDium",
            "LONG": "LONG",
        }

        mode_key = str(mode).upper()

        if mode_key not in mode_lookup:
            raise ValueError("Mode must be SHORT, MEDIUM, or LONG.")

        averages = int(averages)

        if not 1 <= averages <= 256:
            raise ValueError("Averaging rate must be from 1 to 256.")

        command = f":APERture {mode_lookup[mode_key]},{averages}"
        return self._write(command)

    def get_aperture(self):
        """Query measurement time mode and averaging rate."""
        command = ":APERture?"
        response = self._query(command).replace('"', '')
        values = [value.strip() for value in response.split(",")]

        mode = values[0].upper()
        averages = int(float(values[1]))

        return mode, averages

    # *************************************************************************
    # ******Impedance Measurement Range******
    def set_impedance_range(self, impedance_range):
        """Set the impedance measurement range in ohms."""
        command = f":FUNCtion:IMPedance:RANGe {impedance_range}"
        return self._write(command)

    def get_impedance_range(self):
        """Query the impedance measurement range in ohms."""
        command = ":FUNCtion:IMPedance:RANGe?"
        impedance_range = float(self._query(command))
        return impedance_range

    def set_impedance_autorange(self, state):
        """Enable or disable impedance autoranging."""
        state = self._state_value(state)
        command = f":FUNCtion:IMPedance:RANGe:AUTO {state}"
        return self._write(command)

    def get_impedance_autorange(self):
        """Query impedance autoranging state."""
        command = ":FUNCtion:IMPedance:RANGe:AUTO?"
        return self._parse_state(self._query(command))

    # *************************************************************************
    # ******DC Bias******
    def set_dc_bias_state(self, state):
        """Enable or disable DC bias."""
        state = self._state_value(state)
        command = f":BIAS:STATe {state}"
        return self._write(command)

    def get_dc_bias_state(self):
        """Query DC bias state."""
        command = ":BIAS:STATe?"
        return self._parse_state(self._query(command))

    def set_dc_bias_voltage(self, voltage):
        """Set the DC bias voltage level in volts."""
        command = f":BIAS:VOLTage:LEVel {voltage}"
        return self._write(command)

    def get_dc_bias_voltage(self):
        """Query the DC bias voltage level in volts."""
        command = ":BIAS:VOLTage:LEVel?"
        voltage = float(self._query(command))
        return voltage

    def set_dc_bias_autorange(self, state):
        """Enable or disable DC bias autoranging."""
        state = self._state_value(state)
        command = f":BIAS:RANGe:AUTO {state}"
        return self._write(command)

    def get_dc_bias_autorange(self):
        """Query DC bias autoranging state."""
        command = ":BIAS:RANGe:AUTO?"
        return self._parse_state(self._query(command))

    # *************************************************************************
    # ******Trigger System******
    def abort(self):
        """Abort the current operation and return the trigger system to idle."""
        command = ":ABORt"
        return self._write(command)

    def set_initiate_continuous(self, state):
        """Enable or disable continuous measurement initiation."""
        state = self._state_value(state)
        command = f":INITiate:CONTinuous {state}"
        return self._write(command)

    def get_initiate_continuous(self):
        """Query continuous measurement initiation state."""
        command = ":INITiate:CONTinuous?"
        return self._parse_state(self._query(command))

    def initiate(self):
        """Move the trigger system from idle to the initiated state."""
        command = ":INITiate"
        return self._write(command)

    def trigger_immediate(self):
        """Generate an immediate trigger."""
        command = ":TRIGger"
        return self._write(command)

    def set_trigger_source(self, source):
        """Set the trigger source."""
        source_lookup = {
            "INTERNAL": "INternal",
            "INT": "INternal",
            "HOLD": "HOLD",
            "EXTERNAL": "EXternal",
            "EXT": "EXternal",
            "BUS": "BUS",
        }

        source_key = str(source).upper()

        if source_key not in source_lookup:
            raise ValueError(
                "Trigger source must be INTERNAL, HOLD, EXTERNAL, or BUS."
            )

        command = f":TRIGger:SOURce {source_lookup[source_key]}"
        return self._write(command)

    def get_trigger_source(self):
        """Query the trigger source."""
        command = ":TRIGger:SOURce?"
        source = self._query(command)
        return source.strip('"').upper()

    def set_trigger_delay(self, delay):
        """Set the trigger delay in seconds."""
        command = f":TRIGger:TDEL {delay}"
        return self._write(command)

    def get_trigger_delay(self):
        """Query the trigger delay in seconds."""
        command = ":TRIGger:TDEL?"
        delay = float(self._query(command))
        return delay

    def set_step_delay(self, delay):
        """Set the list-sweep step delay in seconds."""
        command = f":TRIGger:DELay {delay}"
        return self._write(command)

    def get_step_delay(self):
        """Query the list-sweep step delay in seconds."""
        command = ":TRIGger:DELay?"
        delay = float(self._query(command))
        return delay

    # *************************************************************************
    # ******Measurement Data******
    def fetch_formatted(self):
        """Fetch the latest formatted measurement.

        Returns:
            tuple: (primary_value, secondary_value, status)
        """
        command = ":FETCh:IMPedance:FORMatted?"
        response = self._query(command)
        values = [value.strip() for value in response.split(",")]

        primary_value = float(values[0])
        secondary_value = float(values[1])
        status = int(float(values[2]))

        return primary_value, secondary_value, status

    def fetch_formatted_with_status(self):
        """Fetch formatted data and include a text description of status."""
        primary_value, secondary_value, status = self.fetch_formatted()

        return {
            "primary": primary_value,
            "secondary": secondary_value,
            "status": status,
            "status_text": self.MEASUREMENT_STATUS.get(
                status, "Unknown measurement status"
            ),
        }

    def fetch_corrected_impedance(self):
        """Fetch corrected impedance as resistance and reactance.

        Returns:
            tuple: (resistance_ohms, reactance_ohms)
        """
        command = ":FETCh:IMPedance:CORRected?"
        response = self._query(command)
        values = [value.strip() for value in response.split(",")]

        resistance = float(values[0])
        reactance = float(values[1])

        return resistance, reactance

    # *************************************************************************
    # ******Signal Monitor******
    def set_vac_monitor(self, state):
        """Enable or disable AC voltage signal monitoring."""
        state = self._state_value(state)
        command = f":FUNCtion:SMONitor:VAC:STATe {state}"
        return self._write(command)

    def get_vac_monitor(self):
        """Query AC voltage signal monitoring state."""
        command = ":FUNCtion:SMONitor:VAC:STATe?"
        return self._parse_state(self._query(command))

    def set_iac_monitor(self, state):
        """Enable or disable AC current signal monitoring."""
        state = self._state_value(state)
        command = f":FUNCtion:SMONitor:IAC:STATe {state}"
        return self._write(command)

    def get_iac_monitor(self):
        """Query AC current signal monitoring state."""
        command = ":FUNCtion:SMONitor:IAC:STATe?"
        return self._parse_state(self._query(command))

    def set_vdc_monitor(self, state):
        """Enable or disable DC voltage signal monitoring."""
        state = self._state_value(state)
        command = f":FUNCtion:SMONitor:VDC:STATe {state}"
        return self._write(command)

    def get_vdc_monitor(self):
        """Query DC voltage signal monitoring state."""
        command = ":FUNCtion:SMONitor:VDC:STATe?"
        return self._parse_state(self._query(command))

    def set_idc_monitor(self, state):
        """Enable or disable DC current signal monitoring."""
        state = self._state_value(state)
        command = f":FUNCtion:SMONitor:IDC:STATe {state}"
        return self._write(command)

    def get_idc_monitor(self):
        """Query DC current signal monitoring state."""
        command = ":FUNCtion:SMONitor:IDC:STATe?"
        return self._parse_state(self._query(command))

    def fetch_vac(self):
        """Fetch the monitored AC voltage in volts."""
        command = ":FETCh:SMONitor:VAC?"
        voltage = float(self._query(command))
        return voltage

    def fetch_iac(self):
        """Fetch the monitored AC current in amperes."""
        command = ":FETCh:SMONitor:IAC?"
        current = float(self._query(command))
        return current

    def fetch_vdc(self):
        """Fetch the monitored DC voltage in volts."""
        command = ":FETCh:SMONitor:VDC?"
        voltage = float(self._query(command))
        return voltage

    def fetch_idc(self):
        """Fetch the monitored DC current in amperes."""
        command = ":FETCh:SMONitor:IDC?"
        current = float(self._query(command))
        return current

    # *************************************************************************
    # ******Correction******
    def set_cable_length(self, cable_length):
        """Set test cable length in meters."""
        if cable_length not in (0, 1, 2, 4):
            raise ValueError("Cable length must be 0, 1, 2, or 4 meters.")

        command = f":CORRection:LENGth {cable_length}"
        return self._write(command)

    def get_cable_length(self):
        """Query test cable length in meters."""
        command = ":CORRection:LENGth?"
        cable_length = float(self._query(command))
        return cable_length

    def set_correction_method(self, method):
        """Set correction method to SINGLE or MULTIPLE."""
        method_lookup = {
            "SINGLE": "SINGle",
            "SING": "SINGle",
            "MULTIPLE": "MULTiple",
            "MULT": "MULTiple",
        }

        method_key = str(method).upper()

        if method_key not in method_lookup:
            raise ValueError("Correction method must be SINGLE or MULTIPLE.")

        command = f":CORRection:METHod {method_lookup[method_key]}"
        return self._write(command)

    def get_correction_method(self):
        """Query the correction method."""
        command = ":CORRection:METHod?"
        method = self._query(command)
        return method.strip('"').upper()

    def execute_open_correction(self):
        """Execute an open correction and wait for it to complete."""
        command = ":CORRection:OPEN"
        self._write(command)
        return self.operation_complete()

    def set_open_correction_state(self, state):
        """Enable or disable open correction."""
        state = self._state_value(state)
        command = f":CORRection:OPEN:STATe {state}"
        return self._write(command)

    def get_open_correction_state(self):
        """Query open correction state."""
        command = ":CORRection:OPEN:STATe?"
        return self._parse_state(self._query(command))

    def execute_short_correction(self):
        """Execute a short correction and wait for it to complete."""
        command = ":CORRection:SHORt"
        self._write(command)
        return self.operation_complete()

    def set_short_correction_state(self, state):
        """Enable or disable short correction."""
        state = self._state_value(state)
        command = f":CORRection:SHORt:STATe {state}"
        return self._write(command)

    def get_short_correction_state(self):
        """Query short correction state."""
        command = ":CORRection:SHORt:STATe?"
        return self._parse_state(self._query(command))

    def set_load_correction_state(self, state):
        """Enable or disable load correction."""
        state = self._state_value(state)
        command = f":CORRection:LOAD:STATe {state}"
        return self._write(command)

    def get_load_correction_state(self):
        """Query load correction state."""
        command = ":CORRection:LOAD:STATe?"
        return self._parse_state(self._query(command))

    def set_load_correction_type(self, function):
        """Set the measurement function used for load correction."""
        function = function.upper()

        if function not in self.LOAD_CORRECTION_FUNCTIONS:
            raise ValueError(
                "Invalid load correction function. Valid functions are: "
                + ", ".join(self.LOAD_CORRECTION_FUNCTIONS)
            )

        command = f":CORRection:LOAD:TYPE {function}"
        return self._write(command)

    def get_load_correction_type(self):
        """Query the measurement function used for load correction."""
        command = ":CORRection:LOAD:TYPE?"
        function = self._query(command)
        return function.strip('"').upper()

    # *************************************************************************
    # ******Data Format******
    def set_data_format(self, data_format):
        """Set returned measurement data format to ASCII or REAL64."""
        data_format = str(data_format).upper()

        if data_format in ("ASCII", "ASC"):
            command = ":FORMat:DATA ASCii"
        elif data_format in ("REAL", "REAL64", "REAL,64"):
            command = ":FORMat:DATA REAL,64"
        else:
            raise ValueError("Data format must be ASCII or REAL64.")

        return self._write(command)

    def get_data_format(self):
        """Query returned measurement data format."""
        command = ":FORMat:DATA?"
        data_format = self._query(command)
        return data_format.strip('"').upper()

    def set_ascii_long(self, state):
        """Enable or disable long ASCII numeric formatting."""
        state = self._state_value(state)
        command = f":FORMat:ASCii:LONG {state}"
        return self._write(command)

    def get_ascii_long(self):
        """Query long ASCII numeric formatting state."""
        command = ":FORMat:ASCii:LONG?"
        return self._parse_state(self._query(command))

    def set_exponent_digits(self, digits):
        """Set ASCII exponent field to two or three digits.

        This command requires instrument firmware that supports
        :FORMat:EXPonent:DIGit.
        """
        digits = int(digits)

        if digits not in (2, 3):
            raise ValueError("Exponent digits must be 2 or 3.")

        command = f":FORMat:EXPonent:DIGit {digits}"
        return self._write(command)

    def get_exponent_digits(self):
        """Query the number of ASCII exponent digits."""
        command = ":FORMat:EXPonent:DIGit?"
        digits = int(self._query(command))
        return digits

    # *************************************************************************
    # ******Raw SCPI Access******
    def write_command(self, command):
        """Send a raw SCPI command."""
        return self._write(command)

    def query_command(self, command):
        """Send a raw SCPI query and return the response."""
        return self._query(command)
