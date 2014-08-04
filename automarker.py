#!/usr/bin/env python

import interface_lib
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s:" + logging.BASIC_FORMAT)
logging.info("Automarker beginning execution")

interface = interface_lib.InterrigatorInterface()
