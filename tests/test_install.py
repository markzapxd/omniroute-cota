import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]

class InstallTests(unittest.TestCase):
    def test_install_is_idempotent_and_preserves_config(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home/'.config/omniquota/config.json'
            config.parent.mkdir(parents=True); config.write_text('preserve-me')
            env = dict(os.environ,HOME=directory,XDG_DATA_HOME=str(home/'.local/share'),XDG_CONFIG_HOME=str(home/'.config'),OMNIQUOTA_NO_ACTIVATE='1')
            env['GI_TYPELIB_PATH'] = '/synthetic/typelibs'
            for _ in range(2):
                subprocess.run(['bash',str(ROOT/'scripts/install-user.sh'),'--service','--gnome'],env=env,check=True,capture_output=True)
            self.assertIn('/synthetic/typelibs',(home/'.local/bin/omniquota-service').read_text())
            self.assertIn('/synthetic/typelibs',(home/'.local/bin/omniquota-settings').read_text())
            self.assertEqual(config.read_text(),'preserve-me')
            self.assertTrue((home/'.local/share/dbus-1/services/io.github.omniquota.Service.service').exists())
            self.assertTrue((home/'.local/share/gnome-shell/extensions/omniquota@local/extension.js').exists())
            unit = (home/'.config/systemd/user/omniquota.service').read_text()
            self.assertIn('omniquota-service',unit)
            subprocess.run(['bash',str(home/'.local/bin/omniquota-service'),'--help'],env=env,check=True,capture_output=True)
