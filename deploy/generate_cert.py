"""Self-signed HTTPS sertifikası üretir (ev LAN'ı için).

Mikrofon erişimi tarayıcıda HTTPS gerektirir. Bu, domain/Let's Encrypt
olmadan, kendi PC'n için geçerli bir sertifika üretir. Fully Kiosk'ta
'sertifika hatalarını yoksay' açıkken sorunsuz çalışır.

Çalıştır:  python deploy/generate_cert.py
Çıktı:     backend/certs/cert.pem , backend/certs/key.pem
"""
import datetime
import ipaddress
import socket
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

CERT_DIR = Path(__file__).resolve().parent.parent / "backend" / "certs"


def local_ip() -> str:
    """Bu makinenin LAN IPv4'ünü tahmin et."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def main():
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    ip = local_ip()
    print(f"Sertifika şu IP için üretiliyor: {ip}")

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "tablet-dock")])
    # SAN: tabletin bağlanacağı her adres burada olmalı.
    san = x509.SubjectAlternativeName([
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
        x509.IPAddress(ipaddress.ip_address(ip)),
    ])

    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=3650))  # 10 yıl
        .add_extension(san, critical=False)
        # CA:TRUE -> Android bunu "güvenilir CA" olarak kurabilsin (Chrome güvenir).
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, key_cert_sign=True, crl_sign=True,
                key_encipherment=True, content_commitment=False,
                data_encipherment=False, key_agreement=False,
                encipher_only=False, decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    (CERT_DIR / "key.pem").write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    (CERT_DIR / "cert.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    print(f"Yazıldı:\n  {CERT_DIR / 'cert.pem'}\n  {CERT_DIR / 'key.pem'}")
    print(f"\nTablet bu adrese bağlanacak:  https://{ip}:8000")


if __name__ == "__main__":
    main()
