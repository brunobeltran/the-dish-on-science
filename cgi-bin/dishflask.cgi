#!/usr/bin/env python
from __future__ import print_function
# debug mode modules
# import sys
# sys.stderr = sys.stdout
# import cgitb; cgitb.enable()
import traceback
# import logging
# from logging import FileHandler

from wsgiref.handlers import CGIHandler

import dishflask
app = dishflask.app

try:
    CGIHandler().run(app)
    # logging.info("running app")
except Exception as e:
    print(traceback.format_exc())
    # logging.info(traceback.format_exc([10]))
    # logging.info('Problem in cgiappserver-prod with CGIHandler().run(): %s' % e)
