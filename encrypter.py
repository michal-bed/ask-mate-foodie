from cryptography.fernet import Fernet

key = Fernet.generate_key()  # key which encrypts and decrypts


def encrypt(value):
    return Fernet(key).encrypt(value.encode())


def decrypt(token):
    return Fernet(key).decrypt(token).decode()
