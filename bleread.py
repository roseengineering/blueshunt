
from bluepy import btle

service_uuid = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
char_uuid = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

class MyDelegate(btle.DefaultDelegate):
    def __init__(self, chandle):
        self.chandle = chandle
        btle.DefaultDelegate.__init__(self)

    def handleNotification(self, chandle, data):
        if self.chandle == chandle:
            print(data.decode())

def initialize(mac):
    print('connecting to bluetooth device:', mac)
    per = btle.Peripheral(mac, addrType=btle.ADDR_TYPE_PUBLIC)
    svc = per.getServiceByUUID(service_uuid)
    ch = svc.getCharacteristics(char_uuid)[0]
    chandle = ch.getHandle()
    delegate = MyDelegate(chandle)
    per.setDelegate(delegate)
    return per

def main(mac='f0:08:d1:60:39:0e'):
    done = False
    while not done:
        try:
            per = initialize(mac)
            while True:
                per.waitForNotifications(1.0)
        except btle.BTLEDisconnectError:
            print('bluetooth device connection dropped...')
        except KeyboardInterrupt:
            print('keyboard interrupt while connected')
            done = True
        finally:
            print('disconnecting from bluetooth device')
            per.disconnect()


if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])

