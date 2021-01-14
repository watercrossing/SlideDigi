import logsetup

from prompt_toolkit import HTML
from prompt_toolkit.key_binding.key_bindings import KeyBindings, merge_key_bindings
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import ProgressBar, yes_no_dialog
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.styles import BaseStyle
from prompt_toolkit.completion import Completer, CompleteEvent, Completion
from prompt_toolkit.document import Document


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

from typing import Any, Callable, List, Optional, Tuple, TypeVar, Iterable
from functools import partial
import datetime

import digitisationLogic as dl


def _create_app(dialog: AnyContainer, style: Optional[BaseStyle], customBindings: Optional[KeyBindings] = None) -> Application[Any]:
    # Key bindings.
    bindings = customBindings if customBindings else KeyBindings()
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

    kb = KeyBindings()

    @kb.add('q')
    def quithdl(event)-> None:
        get_app().exit(-1)

    @kb.add('o')
    def scanOne(event) -> None:
        get_app().layout.focus(btnOne)
        fp = dl.takePicture(camera)
        dl.getPictures(camera, fp)
    
    @kb.add('f')
    def moveForward(event) -> None:
        get_app().layout.focus(btnForward)
        asyncio.run_coroutine_threadsafe(dl.moveForward(), asyncio.get_event_loop())

    @kb.add('b')
    def moveBackward(event) -> None:
        get_app().layout.focus(btnBackward)
        asyncio.run_coroutine_threadsafe(dl.moveBackward(), asyncio.get_event_loop())
    
    @kb.add('s')
    def scanBatch(event):
        get_app().layout.focus(btnBatch)
        get_app().exit(batchSize[0])

    title = "Slide Digitalisation"

    width = len(title) + 4

    btnBatch = Button(text="[s]can batch", handler=partial(scanBatch, None), width=width, left_symbol="", right_symbol="")
    btnOne = Button(text="Scan [o]ne (w/o) moving", handler=partial(scanOne, None), width=width, left_symbol="", right_symbol="")
    btnForward = Button(text="[f]orward", handler=partial(moveForward, None), width=width, left_symbol="", right_symbol="")
    btnBackward = Button(text="[b]ackward", handler=partial(moveBackward, None), width=width, left_symbol="", right_symbol="")
    btnQuit = Button(text="[q]uit", handler=partial(quithdl, None), width=width, left_symbol="", right_symbol="")

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

    def hdlTextFieldChange(buf: Buffer):
        try:
            batchSize[0] = int(buf.text)
        except ValueError:
            pass

    validator = Validator.from_callable(is_valid, error_message='Numbers only')
    textfield = TextArea(
        text=str(batchSize[0]),
        multiline=False,
        password=False,
        validator=validator,
        accept_handler=accept
    )
    textfield.buffer.on_text_changed.add_handler(hdlTextFieldChange)

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
    
    return await _create_app(dialog, None, kb).run_async()

async def pauseDialog():
    
    kb = KeyBindings()

    @kb.add('f')
    def moveForward(event) -> None:
        get_app().layout.focus(btnForward)
        asyncio.run_coroutine_threadsafe(dl.moveForward(), asyncio.get_event_loop())

    @kb.add('b')
    def moveBackward(event) -> None:
        get_app().layout.focus(btnBackward)
        asyncio.run_coroutine_threadsafe(dl.moveBackward(), asyncio.get_event_loop())
    
    @kb.add('c')
    def continueScanning(event) -> None:
        get_app().exit(0)

    @kb.add('q')
    def quitScanning(event) -> None:
        get_app().exit(-1)

    title = "Paused"

    width = len(title) + 4

    btnContinue = Button(text="[c]ontinue", handler=partial(continueScanning, None), width=width, left_symbol="", right_symbol="")
    btnForward = Button(text="[f]orward", handler=partial(moveForward, None), width=width, left_symbol="", right_symbol="")
    btnBackward = Button(text="[b]ackward", handler=partial(moveBackward, None), width=width, left_symbol="", right_symbol="")
    btnQuit = Button(text="[q]uit", handler=partial(quitScanning, None), width=width, left_symbol="", right_symbol="")

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
    
    return await _create_app(dialog, None, kb).run_async()


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
    # application. Doesn't seem to work on Windows
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
                await dl.takeOneAndMove(camera, pause)
                scanProgress += 1
                pbc.item_completed()
                # Pause when the pause flag has been set.
                if pause[0]:
                    return batches[0], scanProgress, pbc.time_elapsed
                # Stop when the cancel flag has been set.
                if cancel[0]:
                    return batches[0], -1, None
            pbc.done = True
    return batches[0], -1, pbc.time_elapsed

async def main():
    batchSize = origBatchSize = 36
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
    dl.teardown()