
from bluepy.btle import Scanner, DefaultDelegate

found = {}

class ScanDelegate(DefaultDelegate):
    def handleDiscovery(self, dev, isNewDev, isNewData):
        if dev.addr not in found: 
            print(dev.addr)
            for d in dev.getScanData():
                print('                    {}: {}'.format(d[1], d[2]))
        found[dev.addr] = dev.addr

scanner = Scanner().withDelegate(ScanDelegate())

# listen for ADV_IND packages for 10s, then exit
scanner.scan(10.0, passive=True)

