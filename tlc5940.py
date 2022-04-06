import machine

class TLC5940():
    """Simple interface to set data on the tlc5940"""

    def __init__(self, gsclk, blank, vprg, xlat, sclk, sin, sout=None, spi_id=-1):
        """Initialize all GPIO pins and SPI pins

        Args:
            gsclk (int): Pulse Width Modulation clock (no actual PWM implemented)
            blank (int): Disable all outputs
            vprg (int): Set programming mode
            xlat (int): Latch values after programming

            sclk (int): Serial clock
            sin (int): Serial data to the TLC5940
            sout (int): Serial data from the TLC5940
            spi_type (int, optional): Determines SPI implementation to use (-1 software. 0, 1 etc for hardware). Defaults to -1.

        (See documentation for specific board implementations)
        """ # pylint: disable=line-too-long

        self.__gsclk = machine.Pin(gsclk, machine.Pin.OUT, value=0)
        self.__blank = machine.pin(blank, machine.Pin.OUT, value=1) # Disable all outputs
        self.__vprg = machine.pin(vprg, machine.Pin.OUT, value=0)
        self.__xlat = machine.pin(xlat, machine.Pin.OUT, value=0)
        self.__spi = machine.SPI(spi_id, baudrate=10000000, bits=8,
            sck=machine.Pin(sclk),
            mosi=machine.Pin(sin),
            miso=machine.Pin(sout) if sout is not None else None,
        )

    def set_data(self, byte_array):
        """Set data from byte_array in tlc5940(s)

        Each tlc5940 accepts 16 x 12-bit (192-bit) data before
        sending any further data to SOUT.

        To be able to send data to multiple tlc5940s,
        connect SOUT to SIN in series.
        """

        self.__spi.write(byte_array) # Send grey scale data on SPI
        self.__blank.value(1) # Disable all outputs
        self.__xlat.value(1) # Latch data
        self.__xlat.value(0)
        self.__blank.value(0) # Enable outputs
        self.__gsclk.value(1) # Pulse PWM clock once to activate data
        self.__gsclk.value(0)

def bit_string_to_byte_array(bit_string):
    """Convert tlc5940 bit string to byte array for SPI"""

    byte_array = bytearray()
    byte = ""
    for bit in bit_string:
        byte += bit
        if len(byte) == 8:
            byte_array.append(int("0b{}".format(byte)))  # pylint: disable=consider-using-f-string
            byte = ""
    return byte_array

def simple_byte_array(outputs):
    """Convert a simple string of outputs to a tlc5940 byte array

    The tlc5940 requires 12-bit grey scale data for each output.
    This function allows on/off inputs instead.

    Tlc5940 grey scale data format is Big-Endian, so the byte array
    is reversed compared to the input.

    Ex. single tlc5940:
        outputs = "1010000000000000"
    activates OUT0 and OUT2 at 100 % brightness

    Ex. 2 x tlc5940 in series:
        outputs = "10100000000000001100000000000000"
    activates OUT0 and OUT2 on the first tlc5940,
    and activates OUT0 and OUT1 on the second tlc5940
    """

    def bit_string_generator(outputs):
        for i in reversed(outputs):
            for bit in range(12):
                yield i

    return bit_string_to_byte_array(bit_string_generator(outputs))
