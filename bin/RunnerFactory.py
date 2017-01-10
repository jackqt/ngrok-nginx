#!/usr/bin/env python
# -*- coding:utf-8 -*-

class RunnerFactory(object):
    def __init__(self):
        self.__runner = None
        pass

    @classmethod
    def getInstance(cls):
        from Util import Util
        from Runner import MacRunner, WinRunner, LinuxRunner
        if Util.is_mac():
            cls.runner = MacRunner()
        elif Util.is_win():
            cls.runner = WinRunner()
        else:
            cls.runner = LinuxRunner()
        return cls.runner
