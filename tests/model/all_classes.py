import os
from enum import EnumMeta

import unittest
import inspect

os.environ["OGN_CONFIG_MODULE"] = "config/test.py"

import app.model  # noqa: E402


class TestStringMethods(unittest.TestCase):
    def test_string(self):
        failures = 0
        for name, obj in inspect.getmembers(app.model):
            try:
                if inspect.isclass(obj) and not isinstance(obj, EnumMeta):
                    print(obj())
            except AttributeError as e:
                print("Failed: {}".format(name))
                failures += 1

        if failures > 0:
            raise AssertionError("Not all classes are good")


if __name__ == "__main__":
    unittest.main()
