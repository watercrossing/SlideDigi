

import logsetup

import time, sys, logging, os, asyncio, concurrent
from functools import partial
from datetime import datetime

try:
    from RPi import GPIO
    import gphoto2 as gp
except ImportError:
    logging.warning("Not running on RPi / gphoto2 not installed, using mocks")
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
                # no camera, try again in 5 seconds
                logging.warning("Please connect the camera")
                asyncio.sleep(5)
                continue
            raise
        break
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAIS_1_GPIO, GPIO.OUT)

    return camera


async def moveForward():
    logging.info("Moving forward")
    GPIO.output(RELAIS_1_GPIO, GPIO.HIGH)
    await asyncio.sleep(0.1)
    GPIO.output(RELAIS_1_GPIO, GPIO.LOW)
    await asyncio.sleep(1.5)
    logging.info("Forward move complete")


async def moveBackward():
    logging.info("Moving backward")
    GPIO.output(RELAIS_1_GPIO, GPIO.HIGH)
    await asyncio.sleep(0.5)
    GPIO.output(RELAIS_1_GPIO, GPIO.LOW)
    await asyncio.sleep(1.5)
    logging.info("Backward move complete")


def takePicture(camera):
    logging.debug('Taking picture')
    file_path = camera.capture(gp.GP_CAPTURE_IMAGE)
    return file_path

def getPictures(camera, file_path):
    logging.debug('Camera file path: {0}/{1}'.format(file_path.folder, file_path.name))
    target = os.path.join(TARGETDIR, datetime.now().strftime("%Y%m%d-%H%M%S.") + file_path.name.split(".")[-1])
    logging.debug('Copying image to %s' %target)
    camera_file = camera.file_get(file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
    camera_file.save(target)
    logging.debug('Copying done')

async def takeOne():
    logging.info("TakeOne started")
    loop = asyncio.get_running_loop()
    camera = await setup()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        filepath = await loop.run_in_executor(pool, partial(takePicture, camera))
        gPFuture = loop.run_in_executor(pool, partial(getPictures, camera, filepath))
        #mfTask = asyncio.create_task(moveForward)
        await asyncio.gather(gPFuture, moveForward())
        logging.debug("Done in pool")

    #await asyncio.gather(getPictures(camera, filepath), moveForward())


if __name__ == '__main__':
    asyncio.run(takeOne())
