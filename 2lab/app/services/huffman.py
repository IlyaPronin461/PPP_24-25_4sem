import heapq
from collections import defaultdict
from typing import Dict, Tuple


class HuffmanCoding:
    @staticmethod
    def build_frequency_dict(text: str) -> Dict[str, int]:
        frequency = defaultdict(int)
        for char in text:
            frequency[char] += 1
        return frequency

    @staticmethod
    def build_huffman_tree(frequency: Dict[str, int]) -> Tuple:
        heap = [[weight, [char, ""]] for char, weight in frequency.items()]
        heapq.heapify(heap)

        while len(heap) > 1:
            lo = heapq.heappop(heap)
            hi = heapq.heappop(heap)
            for pair in lo[1:]:
                pair[1] = '0' + pair[1]
            for pair in hi[1:]:
                pair[1] = '1' + pair[1]
            heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])

        return heap[0]

    @staticmethod
    def build_codes(tree: Tuple) -> Dict[str, str]:
        codes = {}
        for pair in tree[1:]:
            char, code = pair
            codes[char] = code
        return codes

    @staticmethod
    def encode_text(text: str, codes: Dict[str, str]) -> Tuple[str, int]:
        encoded_text = ''.join([codes[char] for char in text])
        padding = 8 - len(encoded_text) % 8
        encoded_text += '0' * padding
        return encoded_text, padding

    @staticmethod
    def decode_text(encoded_text: str, codes: Dict[str, str], padding: int) -> str:
        if padding > 0:
            encoded_text = encoded_text[:-padding]

        reverse_codes = {v: k for k, v in codes.items()}
        current_code = ""
        decoded_text = []

        for bit in encoded_text:
            current_code += bit
            if current_code in reverse_codes:
                decoded_text.append(reverse_codes[current_code])
                current_code = ""

        return ''.join(decoded_text)