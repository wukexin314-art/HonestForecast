import json
import re
import unittest
from pathlib import Path

import honestforecast

ROOT = Path(__file__).resolve().parents[1]


class SkillPackagingTests(unittest.TestCase):
    def test_skill_and_plugin_metadata_stay_consistent(self):
        skill = (ROOT / "skills" / "honest-forecast" / "SKILL.md").read_text()
        front = re.match(r"---\nname: (\S+)\ndescription: (.+?)\n---\n", skill, re.S)
        self.assertIsNotNone(front)
        plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        self.assertEqual(front.group(1), plugin["name"])
        self.assertEqual(plugin["version"], honestforecast.__version__)
        self.assertIn(plugin["name"], [entry["name"] for entry in market["plugins"]])
        # Every reference the skill links to must exist.
        for link in re.findall(r"\]\((references/[^)]+)\)", skill):
            self.assertTrue((ROOT / "skills" / "honest-forecast" / link).is_file(), link)


if __name__ == "__main__":
    unittest.main()
