
# Micropython INA219 High Side Current Sensor Library with ESP32 Bluetooth BLE App

![](output.png)

This repo contains a Bluetooth BLE app for reading from a INA219 I2C 
high-side current sensor using Micropython.  The readings
are sent over the nRF UART BLE serivce.  You can use the included bleread.py script or the nrfUART app on your phone to connect to it.  (see https://play.google.com/store/apps/details?id=com.nordicsemi.nrfUARTv2&hl=en&gl=US) Sensor readings are also printed to the Micropython console.

Included in the repo is the Micropython library the
app uses to read voltage, power, and current from the INA219 chip.

### Simple Example

A simple example of reading from a INA219, connected to I2C port/id 1, using the library follows:

```python
>>> from machine import I2C
>>> from ina219 import INA219
>>> i2c = I2C(1)
>>> rshunt = .1
>>> ina = INA219(i2c, rshunt=rshunt)
>>> print(ina.bus_voltage(), ina.power())
4.712 0.005125156
>>> print(ina.current(), ina.shunt_voltage() / rshunt)
0.001100034 0.0011
```

The class INA219 takes the following arguments:

```python
INA219(i2c, 
       rshunt=0.1,   # shunt resistance measured across by the INA219
       maxvolts=16,  # the max volts you expect at IN-
       maxamps=.1,   # the max amps you expect through rshunt
       BADC=15,      # average 128 12bit samples to get bus voltage
       SADC=15,      # average 128 12bit supply to get shunt voltage
       MODE=7,       # set sampling to shunt and bus continuous mode
       addr=0x40     # default i2c address for the INA219
      )
```

1. "maxvolts" sets the BRNG register for different VBUS ranges, namely
16V and 32V.  BRNG is set to the minimum voltage that maxvolts fits under.
2. "maxamps" sets the PG register for different VSHUNT ranges,
namely .04V, .08V, .16V, and 0.32V.  PG is set to the minimum
voltage that (maxamps * rshunt) fits under.
3. The BADC, SADC, and MODE variables are set according to the tables in 
the INA219 datasheet.
4. Internally the library sets the INA219 calibration value
to 0xFFFE for maximum precision when measuring current and power draw.

### The BLE/Console App

First copy the ina219.py library to the ESP32 as is.
Next copy blueshunt.py as main.py.
After a reset the BLE app should run and immediately start transmitting
and blinking the ESP32's led.
The App's BLE UART service will 
show up as "blueshunt".  The same values sent (or "notified") over BLE 
are also printed to the Micropython console.

The order of the comma separated output is volts,milliamps,milliwatts.

### Helper scripts

1. blescan.py - Run with sudo to scan for BLE devices.
2. bleread.py - Run to read from your blueshunt device.  Pass the mac address of the ESP32 you want to connect to as the command line argument.


