#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys

class Util:
    @staticmethod
    def is_mac():
        return sys.platform == "darwin"

    @staticmethod
    def is_win():
        return sys.platform == "win32"

    @staticmethod
    def is_linux():
        return sys.platform == "linux"
