from fastapi import APIRouter, Depends
from app.services.huffman import HuffmanCoding
from app.services.xor import XORCipher
from app.schemas.encode import EncodeRequest, EncodeResponse, DecodeRequest, DecodeResponse

router = APIRouter()


@router.post("/encode", response_model=EncodeResponse)
async def encode_text(request: EncodeRequest):
    # Шаг 1: Сжатие Хаффмана
    frequency = HuffmanCoding.build_frequency_dict(request.text)
    tree = HuffmanCoding.build_huffman_tree(frequency)
    codes = HuffmanCoding.build_codes(tree)
    encoded_text, padding = HuffmanCoding.encode_text(request.text, codes)

    # Шаг 2: XOR шифрование
    encrypted_data = XORCipher.encrypt(encoded_text, request.key)

    return EncodeResponse(
        encoded_data=encrypted_data,
        key=request.key,
        huffman_codes=codes,
        padding=padding
    )


@router.post("/decode", response_model=DecodeResponse)
async def decode_text(request: DecodeRequest):
    # Шаг 1: XOR расшифровка
    decrypted_data = XORCipher.decrypt(request.encoded_data, request.key)

    # Шаг 2: Распаковка Хаффмана
    decoded_text = HuffmanCoding.decode_text(
        decrypted_data,
        request.huffman_codes,
        request.padding
    )

    return DecodeResponse(decoded_text=decoded_text)