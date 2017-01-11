#!/usr/bin/env python
# -*- coding:utf-8 -*-

from Util import Util

class RunnerFactory(object):
    def __init__(self):
        self.__runner = None
        pass

    @classmethod
    def getInstance(cls):
        if Util.is_mac():
            from MacRunner import MacRunner
            cls.runner = MacRunner()
        elif Util.is_win():
            from WinRunner import WinRunner
            cls.runner = WinRunner()
        else:
            from LinuxRunner import LinuxRunner
            cls.runner = LinuxRunner()
        return cls.runner
