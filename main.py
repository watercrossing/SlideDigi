#!/usr/bin/env python

import asyncio, sys

if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logsetup
from displayLogic import main

if __name__ == '__main__':
    asyncio.run(main())