import base64

class XORCipher:
    @staticmethod
    def encrypt(text: str, key: str) -> str:
        encrypted = []
        key_len = len(key)
        for i, char in enumerate(text):
            key_char = key[i % key_len]
            encrypted_char = chr(ord(char) ^ ord(key_char))
            encrypted.append(encrypted_char)
        return base64.b64encode(''.join(encrypted).encode()).decode()

    @staticmethod
    def decrypt(encrypted_text: str, key: str) -> str:
        decoded = base64.b64decode(encrypted_text).decode()
        decrypted = []
        key_len = len(key)
        for i, char in enumerate(decoded):
            key_char = key[i % key_len]
            decrypted_char = chr(ord(char) ^ ord(key_char))
            decrypted.append(decrypted_char)
        return ''.join(decrypted)