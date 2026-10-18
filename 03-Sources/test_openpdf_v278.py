"""Headless V27.8 UI policy tests. Abdelhalim Talbi."""
import unittest
from openpdf_commands_v276 import COMMANDS
from openpdf_ui_shell_v278 import SHORTCUTS, Shortcut, validate_shortcuts, command_enabled

class ShellTests(unittest.TestCase):
    def test_shortcuts_valid(self):
        self.assertEqual(len(validate_shortcuts(SHORTCUTS, {c.key for c in COMMANDS})), 5)
    def test_duplicate_shortcut_rejected(self):
        with self.assertRaises(ValueError):
            validate_shortcuts((Shortcut('<Control-o>', 'add'), Shortcut('<Control-o>', 'save')), {'add','save'})
    def test_unknown_command_rejected(self):
        with self.assertRaises(ValueError):
            validate_shortcuts((Shortcut('<Control-o>', 'missing'),), {'add'})
    def test_busy_disables_mutations(self):
        self.assertTrue(all(not command_enabled(c, True) for c in COMMANDS))
    def test_idle_enables_commands(self):
        self.assertTrue(all(command_enabled(c, False) for c in COMMANDS))

if __name__ == '__main__': unittest.main()
