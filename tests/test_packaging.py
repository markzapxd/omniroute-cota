import json
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class PackagingTests(unittest.TestCase):
    def test_panel_ring(self):
        source = (ROOT/'kde/package/contents/ui/main.qml').read_text()
        self.assertIn('CompactView',source)
        compact = (ROOT/'kde/package/contents/ui/CompactView.qml').read_text()
        self.assertIn('QuotaRing',compact)
        self.assertIn('Layout.preferredWidth: implicitWidth',compact)
        self.assertIn('ringSize + percentageLabel.implicitWidth',compact)
        self.assertIn('clip: true',compact)
        ring = (ROOT/'kde/package/contents/ui/QuotaRing.qml').read_text()
        self.assertIn('remaining / 100',ring)
        self.assertIn('#2ecc71',ring)
    def test_gnome_metadata(self):
        meta = json.loads((ROOT/'gnome/omniquota@local/metadata.json').read_text())
        self.assertEqual(meta['uuid'],'omniquota@local')
        self.assertIn('45',meta['shell-version'])
    def test_kde_metadata(self):
        meta = json.loads((ROOT/'kde/package/metadata.json').read_text())
        self.assertEqual(meta['KPlugin']['Id'],'io.github.omniquota')
        self.assertEqual(meta['X-Plasma-API-Minimum-Version'],'6.0')
    def test_kde_bridge_contract(self):
        source = (ROOT/'kde/bridge/bridge.cpp').read_text()
        for method in ['GetState','Refresh','OpenSettings','Logout','StateChanged']:
            self.assertIn(method,source)
    def test_gnome_lifecycle(self):
        source = (ROOT/'gnome/omniquota@local/extension.js').read_text()
        self.assertIn('disable()',source)
        self.assertIn('disconnectSignal',source)
        self.assertIn('destroy()',source)
