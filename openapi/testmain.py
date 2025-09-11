import unittest
from os import path

__dir__ = path.dirname(__file__)
discover = unittest.defaultTestLoader.discover(path.join(__dir__, "tests"), pattern="*_test.py")
runner = unittest.TextTestRunner()
runner.run(discover)
