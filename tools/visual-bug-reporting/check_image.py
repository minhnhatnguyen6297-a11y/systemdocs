"""Validate actual exported PNG pixels, not string-search of compressed bytes."""
import json
import os
from pathlib import Path
from PIL import Image

root = Path(os.environ.get('G1_VISUAL_SPIKE_TEST_DIR',
    Path(__file__).resolve().parents[2] / '_bmad-output/tmp/visual-bug-reporting/checks'))
results = json.loads((root / 'evidence/e2e-results.json').read_text())
report = json.loads((root / results['reports'][1]).read_text())
im = Image.open(root / Path(*results['reports'][1].split('/')[:-1]) / report['screenshot']['file']).convert('RGB')
# White field, gray outlines, red selection, and their exact half-pixel blends.
allowed = {(255, 255, 255), (176, 176, 176), (255, 0, 0), (255, 128, 128), (215, 88, 88)}
colors = {color for count, color in im.getcolors(im.width * im.height)}
assert colors <= allowed, colors - allowed
# Inside the magenta fixture containing personal text, away from outlined controls.
assert im.getpixel((250, 270)) == (255, 255, 255)
record = {'passed': True, 'image': report['screenshot']['file'],
          'colors': sorted(colors), 'private_fixture_region': 'white',
          'scope': 'Executed at 100 percent display scale; fixture text and magenta background omitted'}
(root / 'evidence/image-check.json').write_text(json.dumps(record, indent=2))
print('PASS: exported native PNG contains only wireframe pixels; private fixture is white')
