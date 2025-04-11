import os
import logging
import json
import socket
import argparse
import tempfile
import shutil

class Client:
    def __init__(self, host='localhost', port=8899):
        self.host = host
        self.port = port
        self.connection = None
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(script_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        self.result_dir = os.path.join(script_dir, 'output')
        os.makedirs(self.result_dir, exist_ok=True)
        self.temp_dir = os.path.join(script_dir, 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'client.log')
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.log = logging.getLogger(__name__)
        self.log.info('Клиент инициализирован')
        self.log.info(f'Выходные файлы: {self.result_dir}')
        self.log.info(f'Временные файлы: {self.temp_dir}')

    def connect_to_server(self):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.log.info(f'Подключение к {self.host}:{self.port}')
            self.connection.connect((self.host, self.port))
            return True
        except Exception as e:
            self.log.error(f'Ошибка подключения: {str(e)}', exc_info=True)
            return False

    def download_audio_segment(self, track_name, segment_idx, save_path):
        if not self.connection:
            if not self.connect_to_server():
                return False
        temp_path = None
        try:
            save_dir = os.path.dirname(save_path)
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)

            request = {
                'command': 'get_part_of_audio',
                'file_name': track_name,
                'segment_idx': segment_idx
            }
            self.log.info(f'Отправка запроса на получение части аудио: {request}')
            self.connection.send(json.dumps(request).encode('utf-8'))

            size_info = self.connection.recv(8)
            if not size_info:
                return False
            data_size = int.from_bytes(size_info, byteorder='big')
            temp_file, temp_path = tempfile.mkstemp(dir=self.temp_dir, suffix='.mp3.temp')
            self.log.debug(f'Создан временный файл: {temp_path}')

            received = 0
            with os.fdopen(temp_file, 'wb') as tmp:
                while received < data_size:
                    chunk_size = min(4096, data_size - received)
                    data_chunk = self.connection.recv(chunk_size)
                    if not data_chunk:
                        self.log.error('Соединение прервано')
                        break
                    tmp.write(data_chunk)
                    received += len(data_chunk)

            if received == data_size:
                shutil.move(temp_path, save_path)
                self.log.info(f'Аудио файл успешно сохранен в {save_path}')
                return True
            else:
                self.log.error(f'Получено неверное количество данных: {received} из {data_size}')
                return False
        except Exception as e:
            self.log.error(f'Ошибка при получении части аудио: {str(e)}', exc_info=True)
            return False
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    self.log.debug(f'Временный файл удален: {temp_path}')
                except Exception as e:
                    self.log.error(f'Ошибка при удалении временного файла: {str(e)}')

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.log.info("Соединение с сервером закрыто.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Клиент для получения метаданных аудио файлов')
    parser.add_argument('action', choices=['get', 'refresh', 'cut', 'list'],
                      help='Команда: get - получить метаданные, refresh - обновить метаданные, cut - получить часть аудио, list - показать список файлов')
    parser.add_argument('--file', type=str, help='Имя файла для получения сегмента')
    parser.add_argument('--segment', type=int, help='Индекс сегмента (от 0)')
    parser.add_argument('--output', help='Имя выходного файла (будет сохранен в директорию output)')
    args = parser.parse_args()

    client = Client(host='localhost', port=8899)

    try:
        if args.action == 'cut':
            if not all([args.file, args.segment is not None, args.output]):
                print('Необходимо указать --file, --segment и --output для команды cut')
                exit(1)
            output_path = os.path.join(client.result_dir, args.output)
            if client.download_audio_segment(args.file, args.segment, output_path):
                print(f'Аудио успешно получено и сохранено в {output_path}')
            else:
                print('Не удалось получить часть аудио')
    finally:
        client.disconnect()