import base64
import nacl.utils
from nacl.secret import SecretBox


class UrlSafeSymmetricEncryptor:
    def __init__(self, raw_local_sym_key: str) -> None:
        self.secret_box: SecretBox = SecretBox(bytes.fromhex(raw_local_sym_key))

    def symm_encrypt(self, data: bytes) -> bytes:
        nonce: bytes = nacl.utils.random(SecretBox.NONCE_SIZE)
        encrypted_msg = self.secret_box.encrypt(data, nonce=nonce)
        payload: bytes = encrypted_msg.nonce + encrypted_msg.ciphertext
        return base64.urlsafe_b64encode(payload).rstrip(b"=")

    def symm_decrypt(self, payload: bytes) -> bytes:
        decoded_payload: bytes = base64.urlsafe_b64decode(payload + b"==")
        nonce: bytes = decoded_payload[: SecretBox.NONCE_SIZE]
        ciphertext: bytes = decoded_payload[SecretBox.NONCE_SIZE :]
        return self.secret_box.decrypt(ciphertext, nonce=nonce)
