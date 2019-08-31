import os

import unittest
import inspect

os.environ["OGN_CONFIG_MODULE"] = "config/test.py"

import app.model  # noqa: E402


class TestStringMethods(unittest.TestCase):
    def test_string(self):

        try:
            for name, obj in inspect.getmembers(app.model):
                print("Testing: {}".format(name))
                if inspect.isclass(obj):
                    print(obj())
        except AttributeError as e:
            raise AssertionError(e)


if __name__ == "__main__":
    unittest.main()
