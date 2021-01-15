

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

def getShutterspeed(camera):
    logger.debug("Retrieving shutter speed")
    try:
        conf = camera.get_config()
        ss = conf.get_child_by_name('shutterspeed')
        val = ss.get_value()
    finally:
        camera.exit()
    logger.debug("Shutter speed is %s" %val)
    return val

def setShutterspeed(camera, shutterspeed):
    logger.debug("Setting shutter speed to %s" %shutterspeed)
    try:
        conf = camera.get_config()
        ss = conf.get_child_by_name('shutterspeed')
        ss.set_value(shutterspeed)
        camera.set_config(conf)
    finally:
        camera.exit()
    logger.debug("Shutter speed set.")

def takePicture(camera, willMoveForwardAutomatically=False):
    logger.debug('Taking picture')
    retry = 0
    while retry < 3:
        try:
            file_path = camera.capture(gp.GP_CAPTURE_IMAGE)
            break
        except gp.GPhoto2Error:
            logger.warning("Error in camera.capture, retrying %d" %retry)
            if retry == 0 and willMoveForwardAutomatically:
                asyncio.run(moveBackward())
            retry += 1
    if retry > 0 and willMoveForwardAutomatically:
        asyncio.run(moveForward())
    if retry > 2:
        raise gp.GPhoto2Error("Could not capture image")
    return file_path

def getPictures(camera, file_path):
    target = os.path.join(TARGETDIR, datetime.now().strftime("%Y%m%d-%H%M%S.") + file_path.name.split(".")[-1])
    logger.debug('Copying camera file path: {0}/{1} to {2}'.format(file_path.folder, file_path.name, target))
    retry = 0
    while retry < 3:
        try:
            camera_file = camera.file_get(file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
            camera_file.save(target)
            break
        except gp.GPhoto2Error:
            logger.warning("Error in file_get/save encoutered, retrying %d" %retry)
            retry += 1
    if retry > 2:
        raise gp.GPhoto2Error("Could not save camera file")
    logger.debug('Copying done')

def takeAndDownload(camera, willMoveForwardAutomatically=False):
    fp = takePicture(camera, willMoveForwardAutomatically)
    getPictures(camera, fp)

async def takeOneAndMove(camera, shouldPause):
    #logger.info("TakeOne started")
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        tpFuture = loop.run_in_executor(pool, partial(takeAndDownload, camera, True))
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
