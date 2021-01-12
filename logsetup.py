
import logging 

logFormatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
#callback_obj = gp.check_result(gp.use_python_logging())

rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)

fileHandler = logging.FileHandler("slideDigi.log", mode='a', encoding='utf-8')
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
#consoleHandler.setLevel(logging.WARNING)
rootLogger.addHandler(consoleHandler)
