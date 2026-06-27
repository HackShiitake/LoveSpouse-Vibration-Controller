import unittest

from lovespouse_controller.models import VibrationCommand


class VibrationCommandTests(unittest.TestCase):
    def test_parse_millisecond_command(self):
        command = VibrationCommand.parse("5-250ms")

        self.assertEqual(command.strength, 5)
        self.assertEqual(command.duration_seconds, 0.25)
        self.assertEqual(command.original_duration, "250ms")

    def test_parse_second_command_with_decimal_duration(self):
        command = VibrationCommand.parse("3-1.5s")

        self.assertEqual(command.strength, 3)
        self.assertEqual(command.duration_seconds, 1.5)
        self.assertEqual(command.original_duration, "1.5s")

    def test_strength_is_clamped(self):
        command = VibrationCommand.parse("99-1s")

        self.assertEqual(command.strength, 9)

    def test_rejects_invalid_command(self):
        with self.assertRaises(ValueError):
            VibrationCommand.parse("oops")


if __name__ == "__main__":
    unittest.main()
