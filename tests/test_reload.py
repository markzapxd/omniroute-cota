import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]

class ReloadTests(unittest.TestCase):
    def run_reload(self, desktop):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            log = path/'calls'
            for name in ['systemctl','gnome-extensions']:
                script = path/name
                script.write_text('#!/bin/sh\nprintf "%s\\n" "'+name+' $*" >> "$CALL_LOG"\n')
                script.chmod(0o755)
            env = dict(os.environ, PATH=str(path)+':'+os.environ['PATH'], CALL_LOG=str(log),XDG_CURRENT_DESKTOP=desktop)
            result = subprocess.run(['bash',str(ROOT/'scripts/reload-user.sh')],env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            return log.read_text()
    def test_gnome_only_toggles_extension(self):
        calls = self.run_reload('GNOME')
        self.assertIn('restart omniquota.service',calls)
        self.assertIn('gnome-extensions disable omniquota@local',calls)
        self.assertIn('gnome-extensions enable omniquota@local',calls)
        self.assertNotIn('plasma-plasmashell',calls)
    def test_kde_only_restarts_plasma(self):
        calls = self.run_reload('KDE')
        self.assertIn('restart plasma-plasmashell.service',calls)
        self.assertNotIn('gnome-extensions',calls)
