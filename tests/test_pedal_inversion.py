import unittest

from pedal_inversion import (
    apply_pedal_inversion,
    invert_axis_value,
    pedal_inversion_settings,
)


class InvertAxisValueTests(unittest.TestCase):
    def test_normalized_bipolar_axis(self):
        self.assertEqual(invert_axis_value(-0.25, -1.0, 1.0, True), 0.25)
        self.assertEqual(invert_axis_value(0.25, -1.0, 1.0, True), -0.25)
        self.assertEqual(invert_axis_value(0.0, -1.0, 1.0, True), 0.0)

    def test_unipolar_axis(self):
        self.assertAlmostEqual(invert_axis_value(0.2, 0.0, 1.0, True), 0.8)

    def test_byte_range(self):
        self.assertEqual(invert_axis_value(32, 0, 255, True), 223.0)

    def test_disabled_is_identity(self):
        self.assertEqual(invert_axis_value(0.2, 0.0, 1.0, False), 0.2)

    def test_invalid_range(self):
        with self.assertRaises(ValueError):
            invert_axis_value(0.2, 1.0, 1.0, True)

    def test_profile_flags_default_to_false(self):
        self.assertEqual(
            pedal_inversion_settings({"invert_brake": True}),
            {"throttle": False, "brake": True, "clutch": False},
        )

    def test_profile_selects_only_requested_pedal(self):
        profile = {"invert_throttle": True, "invert_brake": False}
        self.assertAlmostEqual(
            apply_pedal_inversion("throttle", 0.2, 0.0, 1.0, profile),
            0.8,
        )
        self.assertAlmostEqual(
            apply_pedal_inversion("brake", 0.2, 0.0, 1.0, profile),
            0.2,
        )

    def test_unknown_pedal_rejected(self):
        with self.assertRaises(ValueError):
            apply_pedal_inversion("steering", 0.2, 0.0, 1.0, {})


if __name__ == "__main__":
    unittest.main()
