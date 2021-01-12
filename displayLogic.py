import logsetup

from prompt_toolkit import HTML
from prompt_toolkit.key_binding.key_bindings import KeyBindings, merge_key_bindings
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import ProgressBar, yes_no_dialog
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.styles import BaseStyle


from prompt_toolkit.application import Application, create_app_session
from prompt_toolkit.application.current import get_app

from prompt_toolkit.widgets import Dialog, Button, Label, TextArea, ValidationToolbar
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import AnyContainer, HSplit, VSplit
from prompt_toolkit.layout.dimension import Dimension as D

from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.defaults import load_key_bindings

from prompt_toolkit.validation import Validator


import time, os, signal, sys, asyncio, logging, concurrent

from typing import Any, Callable, List, Optional, Tuple, TypeVar
from functools import partial
import datetime

import digitisationLogic as dl


def _create_app(dialog: AnyContainer, style: Optional[BaseStyle]) -> Application[Any]:
    # Key bindings.
    bindings = KeyBindings()
    bindings.add("tab")(focus_next)
    bindings.add("s-tab")(focus_previous)
    bindings.add("down")(focus_next)
    bindings.add("up")(focus_previous)

    return Application(
        layout=Layout(dialog),
        key_bindings=merge_key_bindings([load_key_bindings(), bindings]),
        mouse_support=True,
        style=style,
        full_screen=False,
        erase_when_done=True
    )


async def mainDialog(camera, batchSize):

    batchSize = [batchSize]

    def buttonhdl(button: int)-> None:
        get_app().exit(result=button)

    def scanOne() -> None:
        fp = dl.takePicture(camera)
        dl.getPictures(camera, fp)

    def moveForward() -> None:
        asyncio.run_coroutine_threadsafe(dl.moveForward(), asyncio.get_event_loop())

    def moveBackward() -> None:
        asyncio.run_coroutine_threadsafe(dl.moveBackward(), asyncio.get_event_loop())
    
    def startScanning():
        get_app().exit(batchSize[0])

    title = "Slide Digitalisation"

    width = len(title) + 4

    btnBatch = Button(text="Scan batch", handler=startScanning, width=width)
    btnOne = Button(text="Scan one (w/o) moving", handler=scanOne, width=width)
    btnForward = Button(text="Forward", handler=moveForward, width=width)
    btnBackward = Button(text="Backward", handler=moveBackward, width=width)
    btnQuit = Button(text="Quit", handler=partial(buttonhdl, -1), width=width)

    def accept(buf: Buffer) -> bool:
        get_app().layout.focus(btnBatch)
        batchSize[0] = int(buf.text)
        return True  # Keep text.

    def is_valid(text):
        try:
            batchSize[0] = int(text)
            return True
        except ValueError:
            return False

    validator = Validator.from_callable(is_valid, error_message='Numbers only')
    textfield = TextArea(
        text=str(batchSize[0]),
        multiline=False,
        password=False,
        validator=validator,
        accept_handler=accept,
    )

    dialog = Dialog(
        title=title,
        body=HSplit([Label(text="Please select:"),
            btnBatch,
            btnOne,
            btnForward,
            btnBackward,
            VSplit([Label(text="Batch size:"), textfield,]),
            ValidationToolbar(), 
            btnQuit          
        ],
        padding=0),
        #padding=D(preferred=1, max=1)),
        buttons=[],
        with_background=True
    )
    
    return await _create_app(dialog, None).run_async()



async def pauseDialog():
    
    def moveForward() -> None:
        asyncio.run_coroutine_threadsafe(dl.moveForward(), asyncio.get_event_loop())

    def moveBackward() -> None:
        asyncio.run_coroutine_threadsafe(dl.moveBackward(), asyncio.get_event_loop())
    
    def toReturn(bs):
        get_app().exit(bs)

    title = "Paused"

    width = len(title) + 4

    btnContinue = Button(text="Continue", handler=partial(toReturn, 0), width=width)
    btnForward = Button(text="Forward", handler=moveForward, width=width)
    btnBackward = Button(text="Backward", handler=moveBackward, width=width)
    btnQuit = Button(text="Quit", handler=partial(toReturn, -1), width=width)


    dialog = Dialog(
        title=title,
        body=HSplit([Label(text="Please select:"),
            btnContinue,
            btnForward,
            btnBackward,
            btnQuit          
        ],
        padding=0),
        #padding=D(preferred=1, max=1)),
        buttons=[],
        with_background=True
    )
    
    return await _create_app(dialog, None).run_async()


async def batchScanDialogue(camera, batchSize, scanProgress = 0, time_elapsed = datetime.timedelta(0)):
        

    bottom_toolbar = HTML('<b>[i/d]</b> Increment / decrement batch size <b>[p]</b> Pause <b>[a]</b> Abort batch')

    title = HTML('Slide scanning...')
    # Create custom key bindings first.
    kb = KeyBindings()
    cancel = [False]
    pause = [False]
    batches = [batchSize]

    @kb.add('i')
    def increment(event):
        batches[0] += 1

    
    @kb.add('d')
    def decrement(event):
        batches[0] -= 1

    @kb.add('p')
    def p(event):
        pause[0] = True

    @kb.add('a')
    def a(event):
        " Send Abort (control-c) signal. "
        cancel[0] = True
        #os.kill(os.getpid(), signal.SIGINT)

    # Use `patch_stdout`, to make sure that prints go above the
    # application.
    
    with patch_stdout():
        with ProgressBar(title=title, key_bindings=kb, bottom_toolbar=bottom_toolbar,) as pb:
            previousBatch = 0
            pbc = pb(total = batches[0])
            pbc.start_time -= time_elapsed
            pbc.items_completed = scanProgress
            if scanProgress > 0:
                pbc.progress_bar.invalidate()
            while scanProgress < batches[0]:
                logging.debug("At scanProgress: %d" %scanProgress)
                if batches[0] != previousBatch:
                    pbc.total = batches[0]
                    pbc.progress_bar.invalidate()
                    previousBatch = batches[0]
                # Do picture taking and transfer here
                loop = asyncio.get_running_loop()
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    filepath = await loop.run_in_executor(pool, partial(dl.takePicture, camera))
                    gPFuture = loop.run_in_executor(pool, partial(dl.getPictures, camera, filepath))
                    #mfTask = asyncio.create_task(moveForward)
                    await asyncio.gather(gPFuture, dl.moveForward())
                    logging.debug("File transfered, moving on!")
                scanProgress += 1
                pbc.item_completed()
                # Stop when the cancel flag has been set.
                if pause[0]:
                    return batches[0], scanProgress, pbc.time_elapsed
                if cancel[0]:
                    return batches[0], -1, None
            pbc.done = True
    return batches[0], -1, pbc.time_elapsed

async def main():
    batchSize = origBatchSize = 32
    camera = await dl.setup()
    while True:
        batchSize = await mainDialog(camera, batchSize)
        logging.debug("Main Dialog returned %d" %batchSize)
        if batchSize == -1:
            break
        scanProgress = 0
        time_elapsed = datetime.timedelta(0)
        while True:
            batchSize, scanProgress, time_elapsed = await batchScanDialogue(camera, batchSize, scanProgress, time_elapsed)
            if scanProgress == -1:
                break
            pausRes = await pauseDialog()
            if pausRes < 0:
                break
        if batchSize == 1:
            batchSize = origBatchSize
