import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PIL import Image

TOOL = Path(__file__).resolve().parents[1] / 'crop_backgrounds.py'

class CropTests(unittest.TestCase):
    def test_batch_and_rejections(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src = root / 'src'
            src.mkdir()
            Image.new('RGBA', (240, 120), (40, 80, 120, 100)).save(src / '원본.png')
            preset = root / 'list.json'
            preset.write_text(json.dumps([{'code': 'hall', 'name': '로비', 'source': '원본.png'}]))
            out = root / 'out'
            args = [sys.executable, str(TOOL), '--src', str(src), '--out', str(out), '--preset', str(preset), '--size', '128x64', '--no-badge', '--format', 'both', '--naming', '{code}']
            def run(extra=()):
                return subprocess.run(args + list(extra), capture_output=True, text=True)
            self.assertEqual(run(['--dry-run']).returncode, 0)
            self.assertFalse(out.exists())
            result = run()
            self.assertEqual(result.returncode, 0, result.stderr)
            for ext in ('webp', 'png'):
                with Image.open(out / f'hall.{ext}') as img:
                    self.assertEqual(img.size, (128, 64))
                    self.assertEqual(img.getpixel((64, 32))[3], 100)
            self.assertNotEqual(run().returncode, 0)
            self.assertNotEqual(run(['--overwrite', '--size', '0x10']).returncode, 0)
            self.assertNotEqual(run(['--naming', '../escape']).returncode, 0)
            self.assertEqual(run(['--overwrite']).returncode, 0)
            preset.write_text(json.dumps([{'name': 'missing'}]))
            self.assertNotEqual(run(['--dry-run']).returncode, 0)

    def test_badge(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / 'src'
            src.mkdir()
            Image.new('RGB', (1200, 800), 'navy').save(src / '로비.png')
            out = Path(folder) / 'out'
            result = subprocess.run([sys.executable, str(TOOL), '--src', str(src), '--out', str(out), '--format', 'png'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            with Image.open(next(out.glob('*.png'))) as img:
                self.assertNotEqual(img.getpixel((50, 360)), img.getpixel((500, 200)))

if __name__ == '__main__':
    unittest.main()
