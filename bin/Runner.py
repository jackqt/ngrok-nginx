#!/usr/bin/env python
# -*- coding:utf-8 -*-

from abc import abstractmethod
import ConfigParser
import io

class Runner(object):

    _config_file = "../conf/main.cfg"

    def __init__(self):
        self.config_parser = ConfigParser.RawConfigParser(allow_no_value=True)
        self.config_parser.read(self._config_file)

    @staticmethod
    def logger(func):
        def inner(*args, **kvargs):
            print func.__name__, 'called, arguments: ', args, kvargs
            func(*args, **kvargs)
        return inner

    @abstractmethod
    def config(self):
        pass

    @abstractmethod
    def run(self):
        pass
