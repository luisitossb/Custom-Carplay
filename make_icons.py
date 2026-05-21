from PIL import Image, ImageDraw
import os

os.makedirs('assets/icons', exist_ok=True)
W = 64

def new():
    return Image.new('RGBA', (W, W), (0, 0, 0, 0))

def save(img, name):
    img.save(f'assets/icons/{name}.png')
    print(f'  saved {name}.png')

WHITE = (255, 255, 255, 255)
DIM   = (180, 180, 180, 255)

# --- PLAY (right-pointing triangle) ---
img = new(); d = ImageDraw.Draw(img)
d.polygon([(18, 12), (18, 52), (52, 32)], fill=WHITE)
save(img, 'play')

# --- PAUSE (two vertical bars) ---
img = new(); d = ImageDraw.Draw(img)
d.rectangle([14, 12, 26, 52], fill=WHITE)
d.rectangle([38, 12, 50, 52], fill=WHITE)
save(img, 'pause')

# --- NEXT (triangle + bar on right) ---
img = new(); d = ImageDraw.Draw(img)
d.polygon([(12, 14), (12, 50), (42, 32)], fill=WHITE)
d.rectangle([44, 14, 52, 50], fill=WHITE)
save(img, 'next')

# --- PREV (bar on left + triangle pointing left) ---
img = new(); d = ImageDraw.Draw(img)
d.rectangle([12, 14, 20, 50], fill=WHITE)
d.polygon([(52, 14), (52, 50), (22, 32)], fill=WHITE)
save(img, 'prev')

print('done')
