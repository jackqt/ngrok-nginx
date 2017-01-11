#!/usr/bin/env python
# -*- coding:utf-8 -*-

from subprocess import call
import os
from Runner import Runner

class WinRunner(Runner):
    def __init__(self):
        pass
    def config(self):
        print("I'm WinRunner")
        pass
    def run(self):
        print("I'm run on Windows")
        pass
