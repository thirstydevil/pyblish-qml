import unittest

from pyblish_qml import app
from pyblish_qml.vendor.Qt import QtCore


class TestWindowGeometry(unittest.TestCase):
    def test_offscreen_window_is_centered_on_primary_screen(self):
        screen = QtCore.QRect(0, 0, 1920, 1080)
        result = app._fit_window_rect(
            QtCore.QRect(-5000, -5000, 800, 600),
            [screen],
        )

        self.assertEqual(result.size(), QtCore.QSize(800, 600))
        self.assertEqual(result.center(), screen.center())

    def test_partial_window_is_clamped_to_visible_screen(self):
        result = app._fit_window_rect(
            QtCore.QRect(1700, 900, 800, 600),
            [QtCore.QRect(0, 0, 1920, 1080)],
        )

        self.assertEqual(result.right(), 1919)
        self.assertEqual(result.bottom(), 1079)

    def test_window_is_reduced_to_available_screen_size(self):
        result = app._fit_window_rect(
            QtCore.QRect(0, 0, 3000, 2000),
            [QtCore.QRect(0, 0, 1280, 720)],
        )

        self.assertEqual(result, QtCore.QRect(0, 0, 1280, 720))

    def test_window_respects_minimum_size_when_possible(self):
        result = app._fit_window_rect(
            QtCore.QRect(10, 10, 100, 100),
            [QtCore.QRect(0, 0, 1920, 1080)],
            QtCore.QSize(430, 300),
        )

        self.assertEqual(result.size(), QtCore.QSize(430, 300))


if __name__ == "__main__":
    unittest.main()
