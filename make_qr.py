import pyotp
import qrcode
secret = "LF5BJMSQCA42TARRLTLSXPBB63JUA44G"
username = "dr_jane"
uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="SPRMS")
print("Manual entry key (if QR scan fails):", secret)
print("URI:", uri)
img = qrcode.make(uri)
img.save("totp_qr.png")
print("Saved QR code to totp_qr.png - open it and scan with Google Authenticator")