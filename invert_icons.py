"""
Drop your downloaded pixel art PNGs into assets/icons/ with the right names,
then run this script to invert them to white (so they show on dark backgrounds).

Expected filenames: prev.png, play.png, pause.png, next.png
"""
from PIL import Image
import os

ICONS = ['prev.png', 'play.png', 'pause.png', 'next.png']
FOLDER = 'assets/icons'

for name in ICONS:
    path = os.path.join(FOLDER, name)
    if not os.path.exists(path):
        print(f'  missing: {path}')
        continue
    img = Image.open(path).convert('RGBA')
    r, g, b, a = img.split()
    # Invert RGB channels, keep alpha
    from PIL import ImageOps
    rgb = Image.merge('RGB', (r, g, b))
    rgb = ImageOps.invert(rgb)
    result = Image.merge('RGBA', (*rgb.split(), a))
    result.save(path)
    print(f'  inverted: {path}')

print('done')
