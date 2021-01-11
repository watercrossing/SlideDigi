#!/usr/bin/env python

"""Toy problem - is there a proper way?"""
import time

from prompt_toolkit import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import ProgressBar, yes_no_dialog
from prompt_toolkit.application.current import AppSession, create_app_session

def progress():
#with create_app_session() as session:
    bottom_toolbar = HTML(
        ' Press <b>[p]</b> to pause'
    )
    kb = KeyBindings()
    paused = [False]

    @kb.add("p")
    def _(event):
        paused[0] = True

    with ProgressBar(key_bindings=kb, bottom_toolbar=bottom_toolbar) as pb:
        for i in pb(range(800)):
            if paused[0]:
                result = yes_no_dialog(
                    title="Paused.", text="Do you want to continue?"
                ).run()
                if result:
                    paused[0] = False
                else:
                    break
            time.sleep(0.1)

def main():
    progress()


if __name__ == "__main__":
    main()
