import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

def generate_captcha():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    img = Image.new('RGB', (300, 120), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("GOTHAM-BOLD.TTF", 60)
    except:
        font = ImageFont.load_default()
    draw.text((40, 30), code, fill=(0, 0, 0), font=font)
    for _ in range(2):
        draw.line([(random.randint(0, 300), random.randint(0, 120)), 
                   (random.randint(0, 300), random.randint(0, 120))], 
                  fill=(200, 200, 200), width=1)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return code, buf

def generate_short_code(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
