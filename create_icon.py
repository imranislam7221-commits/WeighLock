from PIL import Image, ImageDraw, ImageFont
import os

# Create a simple icon for Weigh Lock
img = Image.new('RGBA', (256, 256), (15, 23, 42))
draw = ImageDraw.Draw(img)

# Draw a scale icon
# Base
draw.rectangle([60, 180, 196, 200], fill=(30, 41, 59))
# Platform left
draw.rectangle([60, 150, 90, 180], fill=(51, 65, 85))
draw.rectangle([90, 120, 110, 150], fill=(100, 116, 139))
# Platform right
draw.rectangle([166, 150, 196, 180], fill=(51, 65, 85))
draw.rectangle([146, 120, 166, 150], fill=(100, 116, 139))
# Beam
draw.rectangle([80, 100, 176, 120], fill=(71, 85, 105))
# Pointer
draw.polygon([(128, 100), (118, 70), (138, 70)], fill=(0, 255, 136))
# Weight text
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
except:
    font = ImageFont.load_default()
draw.text((128, 205), "Weigh Lock", fill=(0, 255, 136), anchor="mm", font=font)

# Save as ICO
img.save(os.path.join(os.path.dirname(__file__), "icon.ico"), format="ICO", sizes=[(256,256), (128,128), (64,64), (32,32), (16,16)])
print("Icon created: icon.ico")