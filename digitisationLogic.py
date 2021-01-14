

import logsetup

import time, sys, logging, os, asyncio, concurrent
from functools import partial
from datetime import datetime

logger = logging.getLogger("digitisationLogic")

try:
    from RPi import GPIO
    import gphoto2 as gp
except ImportError:
    logger.warning("Not running on RPi / gphoto2 not installed, using mocks")
    from mockedLibs import GPIO, gp
    #from unittest.mock import MagicMock
    #RPIMock = MagicMock()
    #gphotoMock = MagicMock()    
    #sys.modules['RPi'] = RPIMock
    #sys.modules['gphoto2'] = gphotoMock
    #from RPi import GPIO
    #import gphoto2 as gp


RELAIS_1_GPIO = 17

TARGETDIR = '/mnt/fotos-ablage/'

async def setup():
    camera = gp.Camera()
    while True:
        try:
            camera.init()
        except gp.GPhoto2Error as ex:
            if ex.code == gp.GP_ERROR_MODEL_NOT_FOUND:
                # no camera, try again in 3 seconds
                logger.warning("Please connect the camera")
                await asyncio.sleep(3)
                continue
            raise
        break
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAIS_1_GPIO, GPIO.OUT)

    return camera

def teardown():
    logger.debug("Teardown.")
    GPIO.cleanup()

async def moveForward():
    logger.info("Moving forward")
    GPIO.output(RELAIS_1_GPIO, GPIO.HIGH)
    await asyncio.sleep(0.1)
    GPIO.output(RELAIS_1_GPIO, GPIO.LOW)
    await asyncio.sleep(1.8)
    logger.info("Forward move complete")

async def forwardAfterWait(shouldPause):
    logger.debug("Sleeping before moving forward.")
    await asyncio.sleep(1.5)
    ## should not moveForward if pause button pressed
    if not shouldPause[0]:
        await moveForward()

async def moveBackward():
    logger.info("Moving backward")
    GPIO.output(RELAIS_1_GPIO, GPIO.HIGH)
    await asyncio.sleep(1)
    GPIO.output(RELAIS_1_GPIO, GPIO.LOW)
    await asyncio.sleep(1.8)
    logger.info("Backward move complete")


def takePicture(camera):
    logger.debug('Taking picture')
    file_path = camera.capture(gp.GP_CAPTURE_IMAGE)
    return file_path

def getPictures(camera, file_path):
    logger.debug('Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))
    target = os.path.join(TARGETDIR, datetime.now().strftime("%Y%m%d-%H%M%S.") + file_path.name.split(".")[-1])
    logger.debug('Copying image to %s' %target)
    camera_file = camera.file_get(file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
    camera_file.save(target)
    logger.debug('Copying done')

def takeAndDownload(camera):
    fp = takePicture(camera)
    getPictures(camera, fp)

async def takeOneAndMove(camera, shouldPause):
    #logger.info("TakeOne started")
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        tpFuture = loop.run_in_executor(pool, partial(takeAndDownload, camera))
        await asyncio.gather(tpFuture, forwardAfterWait(shouldPause))

async def takeOne():
    logsetup.consoleHandler.setLevel(logging.DEBUG)
    logger.info("TakeOne started")
    loop = asyncio.get_running_loop()
    camera = await setup()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        await loop.run_in_executor(pool, partial(takeAndDownload, camera))
    teardown()
    logger.info("TakeOne finished")

if __name__ == '__main__':
    asyncio.run(takeOne())
