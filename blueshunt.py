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
# =============
# LOLIN32 Lite
# =============
#           ------------
#    I,0,R  VP/36    3V3
#    I,0,R  VN/39     22  1,LED
#           EN        19  1
#    I,0,R  34        23  1
#    I,0,R  35        18  1
#      0,R  32         5  1,U,B
#      0,R  33        17  1
#      0,R  25        16  1
#      0,R  26         4  R,1,D
#      0,R  27         0  R,1,U,B
#      1,R  14         2  R,1,D,B
#  B,D,1,R  12        15  R,0
#           GND       13  R,1,D
#           ------------
# =============
# ESP32 30 PINS
# =============
#           ------------
#           EN        23  1
#    I,0,R  VP/36     22  1
#    I,0,R  VN/39      1  TX
#    I,0,R  34         3  RX
#    I,0,R  35        21  1
#      0,R  32        19  1
#      0,R  33        18  1
#      0,R  25         5  1,U,B
#      0,R  26        17  1
#      0,R  27        16  1
#  B,D,1,R  12         4  R,1,D
#    D,1,R  13         2  R,1,D,B,LED
#           GND      GND
#           VIN      3V3
#           ------------
# 0:     input disabled
# 1:     input enabled
# D:     pulldown
# U:     pullup
# R:     pad has RTC/analog functions via RTC_MUX
# B:     boot strapping pins (MTDI, MTDO, IO0, IO2, IO5)
# I:     pad can only be configured as input GPIO
# EN:    resets the ESP32
# IO0:   low for bootloader / high for execution mode
##################################

# ======================
# Micropython ID Matrix
# ======================
# I2C IDS:   0  1
# ---------------
# SCL GPIO: 18 25
# SDA GPIO: 19 26
# ---------------

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

print("V,mA,mW")
while True:
    pin.value(not pin.value()) 
    buf = "{:.2f},{:.1f},{:.1f}".format(
        ina.bus_voltage(), 
        ina.current() * 1000,
        ina.power() * 1000)
    print(buf)
    blue.write(buf)
    time.sleep_ms(1000)

