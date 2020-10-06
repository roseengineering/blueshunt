from micropython import const
import struct
import bluetooth
import machine
import ina219
import time

# gatt advertising

_ADV_TYPE_FLAGS = const(0x01)
_ADV_TYPE_NAME = const(0x09)
_ADV_TYPE_UUID16_COMPLETE = const(0x3)
_ADV_TYPE_UUID32_COMPLETE = const(0x5)
_ADV_TYPE_UUID128_COMPLETE = const(0x7)
_ADV_TYPE_APPEARANCE = const(0x19)
_ADV_APPEARANCE_GENERIC_COMPUTER = const(128)

def advertising_payload(
        limited_disc=False, 
        br_edr=False, 
        name=None, 
        services=None, 
        appearance=0):
    payload = bytearray()
    def _append(adv_type, value):
        nonlocal payload
        payload += struct.pack("BB", len(value) + 1, adv_type) + value
    _append(
        _ADV_TYPE_FLAGS,
        struct.pack("B", (0x01 if limited_disc else 0x02) + 
                         (0x18 if br_edr else 0x04))
    )
    if name:
        _append(_ADV_TYPE_NAME, name)
    if services:
        for uuid in services:
            b = bytes(uuid)
            if len(b) == 2:
                _append(_ADV_TYPE_UUID16_COMPLETE, b)
            elif len(b) == 4:
                _append(_ADV_TYPE_UUID32_COMPLETE, b)
            elif len(b) == 16:
                _append(_ADV_TYPE_UUID128_COMPLETE, b)
    _append(_ADV_TYPE_APPEARANCE, struct.pack("<h", appearance))
    return payload

# gatt service

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX,)
)

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)

class BLEUART:
    def __init__(self, ble, name):
        self._connections = set()
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(handler=self._irq)
        ((self._tx_handle,),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._payload = advertising_payload(
            name=name, 
            appearance=_ADV_APPEARANCE_GENERIC_COMPUTER)
        self._advertise()

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            self._advertise()

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def write(self, data):
        self._ble.gatts_write(self._tx_handle, data)  # FLAG_READ
        for conn_handle in self._connections:         # FLAG_NOTIFY
            self._ble.gatts_notify(conn_handle, self._tx_handle, data)

##################################

# I2C IDS:   0  1
# ---------------
# SCL GPIO: 18 25
# SDA GPIO: 19 26

# ESP32 30 PINS
#             ------------
#             EN        23
# input only  VP        22
# input only  VN         1  tx pin
# input only  34         3  rx pin
# input only  35        21
# crystal     32        19
# crystal     33        18
#             25         5  bootstraping
#             26        17
#             27        16
# bootstrap   12         4
#             13         2  on-board led / bootstraping
#             GND      GND
#             VIN      3V3
# ------------
# GPIO0: low for bootloader / high for execution mode

NAME = "blueshunt"
I2C_ID = 1     # SCL: GPIO25, SDA: GPIO26
LED_GPIO = 2   # GPIO2 is wired to LED1 (blue)
RSHUNT = .1    # shunt resistor value
MAXVOLTS = 16
MAXAMPS = .1

pin = machine.Pin(LED_GPIO, machine.Pin.OUT)  # initially zero (led off)
i2c = machine.I2C(I2C_ID)
ina = ina219.INA219(i2c, rshunt=RSHUNT, maxvolts=MAXVOLTS, maxamps=MAXAMPS)
ble = bluetooth.BLE()
blue = BLEUART(ble, NAME)

while True:
    pin.value(not pin.value()) 
    bv = ina.bus_voltage()
    buf = "{:6.3f}V {:7.2f}mA".format(
        ina.bus_voltage(), 
        ina.current() * 1000)
    print(buf)
    blue.write(buf)
    time.sleep_ms(1000)


