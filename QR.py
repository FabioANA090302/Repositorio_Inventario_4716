import qrcode

url = "https://repositorio-inventario-4716.onrender.com"  # o Railway
qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data(url)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
img.save("codigo_qr.png")
