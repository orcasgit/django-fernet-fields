

def make_image_bytes(fmt):
    buf = BytesIO()
    img = Image.new('RGB', (1, 1))
    img.save(buf, fmt)
    buf.seek(0)
    return buf.read()


def make_image(name='test.png'):
    fmt = name.split('.')[-1]
    return SimpleUploadedFile(name, make_image_bytes(fmt))
