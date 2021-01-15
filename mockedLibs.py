from unittest.mock import AsyncMock, MagicMock, Mock

import logsetup

import logging, time

logger = logging.getLogger('mockedLibs')

GPIO = Mock()
gp = Mock()

def file_get(self, *args):
    logger.debug("Sleeping in mocked file_get")
    time.sleep(1.5)
    return Mock()

def capture(self, *args):
    time.sleep(5)
    m = Mock()
    m.name = "abcd.dmg"
    m.folder = "img"
    return m

def output(self, *args):
    logger.debug("Setting GPIO output to: %s" %repr(args))
    time.sleep(0.05)

GPIO.output = output


mockCam = Mock()
mockCam.file_get = file_get
mockCam.capture = capture
gp.Camera = lambda : mockCam

configMock = Mock()

class ShutterSpeedMock:
    def __init__(self):
        self.ss = '1/50'
    def get_value(self):
        return self.ss
    def set_value(self, val):
        self.ss = val

shutterSpeedMockins = ShutterSpeedMock()

configMock.get_child_by_name = lambda x: shutterSpeedMockins if x == 'shutterspeed' else Mock()
mockCam.get_config = lambda : configMock

#gp.Camera.file_get = file_get

#cam = gp.Camera()
#print(cam)
#print(cam.file_get("a", 1, "2"))

#gphotoMock.Camera = MagicMock()

#gphotoMock.GPhoto2Error = Exception()

#import sys, asyncio, logging

#sys.modules['RPi'] = RPIMock
#sys.modules['gphoto2'] = gphotoMock

#logger.warning("Test file")

#import main
#asyncio.run(main.main())