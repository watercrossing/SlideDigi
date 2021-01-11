from unittest.mock import AsyncMock, MagicMock, Mock

import logsetup

import logging, time


GPIO = Mock()
gp = Mock()

def file_get(self, *args):
    logging.debug("Sleeping in mocked file_get")
    time.sleep(5)
    return Mock()

def capture(self, *args):
    time.sleep(3)
    m = Mock()
    m.name = "abcd.dmg"
    m.folder = "img"
    return m

def output(self, *args):
    logging.debug("Setting GPIO output to: %s" %repr(args))
    time.sleep(3)

GPIO.output = output

mockCam = Mock()
mockCam.file_get = file_get
mockCam.capture = capture
gp.Camera = lambda : mockCam
#gp.Camera.file_get = file_get

#cam = gp.Camera()
#print(cam)
#print(cam.file_get("a", 1, "2"))

#gphotoMock.Camera = MagicMock()

#gphotoMock.GPhoto2Error = Exception()

#import sys, asyncio, logging

#sys.modules['RPi'] = RPIMock
#sys.modules['gphoto2'] = gphotoMock

#logging.warning("Test file")

#import main
#asyncio.run(main.main())