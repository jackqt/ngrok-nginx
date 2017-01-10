#!/usr/bin/env python
# -*- coding:utf-8 -*-

from RunnerFactory import RunnerFactory

def run():
    runner = RunnerFactory.getInstance()
    runner.config()
    runner.run()

if __name__ == '__main__':
    run()
