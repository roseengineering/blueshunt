
import ustruct

REG_CONFIGURATION = 0x00
REG_SHUNT_VOLTAGE = 0x01
REG_BUS_VOLTAGE   = 0x02
REG_POWER         = 0x03
REG_CURRENT       = 0x04
REG_CALIBRATION   = 0x05

class INA219:
    def _read_word(self, register, signed=False):
        buf = self._i2c.readfrom_mem(self._addr, register, 2)
        return ustruct.unpack('!h' if signed else '!H', buf)[0]

    def _write_word(self, register, value):
        buf = ustruct.pack('!h', value)
        self._i2c.writeto_mem(self._addr, register, buf)

    def shunt_voltage(self):
        value = self._read_word(REG_SHUNT_VOLTAGE, signed=True)
        return value * 10e-6

    def bus_voltage(self):
        value = self._read_word(REG_BUS_VOLTAGE) >> 3
        return value * 4e-3

    def current(self):
        return self._read_word(REG_CURRENT, signed=True) * self._current_lsb

    def power(self):
        return self._read_word(REG_POWER) * 20 * self._current_lsb

    def __init__(self, 
                 i2c, 
                 rshunt=0.1, 
                 maxvolts=16,
                 maxamps=.1,
                 BADC=15,    # 128 12bit bus voltage samples
                 SADC=15,    # 128 12bit supply voltage samples
                 MODE=7,     # shunt and bus continuous
                 addr=0x40 
                 ):
        VBUS_RANGE = [ 16, 32 ]
        VSHUNT_RANGE = [ .04, .08, .16, 0.32 ]
        MAX_CAL = 0xFFFE
        self._i2c = i2c
        self._addr = addr
        self._current_lsb = 0.04096 / (MAX_CAL * rshunt)
        val = min(v for v in VBUS_RANGE if v >= maxvolts)
        BRNG = VBUS_RANGE.index(val)
        val = min(v for v in VSHUNT_RANGE if v >= maxamps * rshunt)
        PG = VSHUNT_RANGE.index(val)
        conf = (BRNG << 13) | (PG << 11) | (BADC << 7) | (SADC << 3) | MODE
        self._write_word(REG_CONFIGURATION, conf)
        self._write_word(REG_CALIBRATION, MAX_CAL)


