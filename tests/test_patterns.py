import tempfile
import unittest
from pathlib import Path

from lovespouse_controller.patterns import PatternRepository


class PatternRepositoryTests(unittest.TestCase):
    def test_loads_pattern_files(self):
        with tempfile.TemporaryDirectory() as directory:
            pattern_file = Path(directory) / "sample.vibepattern"
            pattern_file.write_text(
                '{"name": "Sample", "author": "QA"}\n'
                "1-100ms\n"
                "4-0.5s\n",
                encoding="utf-8",
            )

            patterns = PatternRepository(Path(directory)).load()

        self.assertIn("Sample by QA", patterns)
        self.assertEqual([command.strength for command in patterns["Sample by QA"].commands], [1, 4])


if __name__ == "__main__":
    unittest.main()
