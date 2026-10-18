"""Headless regression checks for V27.6 commands."""
import unittest
from openpdf_commands_v276 import CommandRouter, COMMANDS

class Target:
    def __init__(self): self.calls=[]
    def __getattr__(self, name):
        if name.startswith('_') and name not in {'_save_editor','_merge','_compress','_split'}:
            raise AttributeError(name)
        return lambda: self.calls.append(name)

class RouterTests(unittest.TestCase):
    def setUp(self):
        self.target=Target(); self.busy=False
        self.router=CommandRouter(self.target,lambda:self.busy)
    def test_every_command_dispatches(self):
        for c in COMMANDS: self.assertTrue(self.router.dispatch(c.key))
        self.assertEqual(self.target.calls,[c.method for c in COMMANDS])
    def test_busy_prevents_commands(self):
        self.busy=True
        for c in COMMANDS:self.assertFalse(self.router.dispatch(c.key))
        self.assertEqual(self.target.calls,[])
    def test_unknown_command_rejected(self):
        with self.assertRaises(KeyError):self.router.dispatch('dangerous')
    def test_handler_error_propagates(self):
        class Broken:
            def add_files(self): raise RuntimeError('failure')
        with self.assertRaises(RuntimeError):CommandRouter(Broken(),lambda:False).dispatch('add')
    def test_unique_command_keys(self):
        self.assertEqual(len(COMMANDS),len({c.key for c in COMMANDS}))

if __name__=='__main__':unittest.main()
