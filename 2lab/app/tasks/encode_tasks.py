from app.services.huffman import HuffmanCoding
from app.services.xor import XORCipher
from app.core.celery_config import celery_app


@celery_app.task(bind=True)
def encode_task(self, text: str, key: str):
    try:
        # Обновление статуса задачи
        self.update_state(state='PROGRESS', meta={'status': 'Huffman encoding...'})

        # 1. Сжатие Хаффмана
        frequency = HuffmanCoding.build_frequency_dict(text)
        tree = HuffmanCoding.build_huffman_tree(frequency)
        codes = HuffmanCoding.build_codes(tree)
        encoded_text, padding = HuffmanCoding.encode_text(text, codes)

        # Обновление статуса
        self.update_state(state='PROGRESS', meta={'status': 'XOR encryption...'})

        # 2. XOR шифрование
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
        # Обновление статуса
        self.update_state(state='PROGRESS', meta={'status': 'XOR decryption...'})

        # 1. XOR расшифровка
        decrypted_data = XORCipher.decrypt(encoded_data, key)

        # Обновление статуса
        self.update_state(state='PROGRESS', meta={'status': 'Huffman decoding...'})

        # 2. Распаковка Хаффмана
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
    """Пример простой задачи для тестирования Celery"""
    return x + y