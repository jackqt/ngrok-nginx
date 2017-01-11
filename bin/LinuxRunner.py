#!/usr/bin/env python
# -*- coding:utf-8 -*-

from subprocess import call
import os
from Runner import Runner

class LinuxRunner(Runner):
    def __init__(self):
        pass
    def config(self):
        print("I'm LinuxRunner")
        pass
    def run(self):
        print("I'm run on Linux")
        pass
