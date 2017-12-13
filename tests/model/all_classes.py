import unittest
import inspect

import ogn.model


class TestStringMethods(unittest.TestCase):
    def test_string(self):

        try:
            for name, obj in inspect.getmembers(ogn.model):
                print("Testing: {}".format(name))
                if inspect.isclass(obj):
                    print(obj())
        except AttributeError as e:
            raise AssertionError(e)

if __name__ == '__main__':
    unittest.main()
