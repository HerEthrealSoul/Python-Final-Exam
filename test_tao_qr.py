import qrcode
img = qrcode.make('3')

# Lưu thành file ảnh
img.save('qr_id3.png')
print("Đã tạo mã QR thành công!")