from app.services.huffman import HuffmanCoding
from app.services.xor import XORCipher
from app.core.celery_config import celery_app


@celery_app.task(bind=True)
def encode_task(self, text: str, key: str):
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Huffman encoding...'}) # Обновление статуса задачи

        # сжатие хаффмана
        frequency = HuffmanCoding.build_frequency_dict(text)
        tree = HuffmanCoding.build_huffman_tree(frequency)
        codes = HuffmanCoding.build_codes(tree)
        encoded_text, padding = HuffmanCoding.encode_text(text, codes)

        self.update_state(state='PROGRESS', meta={'status': 'XOR encryption...'})

        # xor шифрование
        encrypted_data = XORCipher.encrypt(encoded_text, key)

        return {
            'status': 'SUCCESS',
            'result': {
                "encoded_data": encrypted_data,
                "key": key,
                "huffman_codes": codes,
                "padding": padding
            }
        }
    except Exception as e:
        return {
            'status': 'FAILURE',
            'error': str(e)
        }


@celery_app.task(bind=True)
def decode_task(self, encoded_data: str, key: str, huffman_codes: dict, padding: int):
    try:
        self.update_state(state='PROGRESS', meta={'status': 'XOR decryption...'})

        # xor расшифровка
        decrypted_data = XORCipher.decrypt(encoded_data, key)

        self.update_state(state='PROGRESS', meta={'status': 'Huffman decoding...'})

        # распаковка хаффмана
        decoded_text = HuffmanCoding.decode_text(
            decrypted_data,
            huffman_codes,
            padding
        )

        return {
            'status': 'SUCCESS',
            'result': {
                "decoded_text": decoded_text
            }
        }
    except Exception as e:
        return {
            'status': 'FAILURE',
            'error': str(e)
        }


# Тестовая задача для проверки Celery
@celery_app.task
def test_task(x: int, y: int) -> int:
    return x + y