from pydub import AudioSegment
import os
import json
import socket
import threading
import io
import logging

class Server:
    def __init__(self, host='localhost', port=8899, audio_folder='audio'):
        self.host = host
        self.port = port
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.audio_folder = os.path.join(current_dir, audio_folder)
        self.track_info = {}
        self.track_segments = {}
        self.socket = None
        self.is_running = False
        logs_dir = os.path.join(current_dir, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        log_path = os.path.join(logs_dir, 'server.log')
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.log = logging.getLogger(__name__)
        self.log.info('Сервер начинает работу')
        self.log.info(f'Аудио файлы: {self.audio_folder}')
        self.log.info(f'Файлы для логов: {logs_dir}')
        self.load_audio_files()

    def load_audio_files(self):
        self.track_info = {}
        self.track_segments = {}
        for file in os.listdir(self.audio_folder):
            if file.endswith(('.mp3', '.wav')):
                full_path = os.path.join(self.audio_folder, file)
                try:
                    audio = AudioSegment.from_file(full_path)
                    segments = []
                    segment_length = 6000  # 6 секунд

                    # аудио на сегменты
                    for start_ms in range(0, len(audio), segment_length):
                        segment = audio[start_ms:start_ms + segment_length]
                        segments.append(segment)

                    self.track_info[file] = {
                        'name': file,
                        'duration': len(audio) / 1000
                    }
                    self.track_segments[file] = segments
                except Exception:
                    pass

        with open('audio_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(self.track_info, f, ensure_ascii=False, indent=4)

    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(3)
        self.is_running = True
        print(f'Сервер стартанул, {self.host}:{self.port}')
        while self.is_running:
            try:
                conn, addr = self.socket.accept()
                client_thread = threading.Thread(
                    target=self.process_client,
                    args=(conn,)
                )
                client_thread.start()
            except Exception as e:
                print(f'Ошибка: {e}')

    def cut_audio(self, track_name, segment_idx):
        try:
            segments = self.track_segments.get(track_name)
            if segments and 0 <= segment_idx < len(segments):
                segment = segments[segment_idx]
                buffer = io.BytesIO()
                segment.export(buffer, format='mp3')
                result = buffer.getvalue()
                return result
            else:
                self.log.error(f'Ошибка: неверный индекс сегмента для {track_name}')
                return None
        except Exception as e:
            self.log.error(f'Ошибка при обработке аудио: {str(e)}', exc_info=True)
            return None

    def process_client(self, conn):
        try:
            client_addr = conn.getpeername()
            self.log.info(f'Обращается клиент {client_addr}')
            while True:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break
                self.log.debug(f'{client_addr} сделал запрос: {data}')
                try:
                    request = json.loads(data)
                    cmd = request.get('command')
                except json.JSONDecodeError:
                    cmd = data

                if cmd == 'get_metadata':
                    self.log.debug('Отправка метаданных')
                    response = json.dumps(self.track_info, ensure_ascii=False)
                    conn.send(response.encode('utf-8'))

                elif cmd == 'refresh':
                    self.log.debug('Обновление метаданных')
                    self.load_audio_files()
                    response = json.dumps({'status': 'refreshed'})
                    conn.send(response.encode('utf-8'))

                elif cmd == 'get_audio_list':
                    self.log.debug('Отправка списка аудио')
                    response = json.dumps(
                        [self.track_info[track]['name'] for track in self.track_info],
                        ensure_ascii=False
                    )
                    conn.send(response.encode('utf-8'))

                elif cmd == 'get_part_of_audio':
                    track_name = request.get('file_name')
                    segment_idx = request.get('segment_idx')
                    if track_name is None or segment_idx is None:
                        error_msg = 'Нужно указать все параметры'
                        self.log.error(error_msg)
                        response = json.dumps({'error': error_msg})
                        conn.send(response.encode('utf-8'))
                        continue

                    audio = self.cut_audio(track_name, segment_idx)
                    if audio:
                        size = len(audio).to_bytes(8, byteorder='big')
                        conn.send(size)
                        conn.sendall(audio)
                        self.log.info('Аудио данные успешно отправлены')
                    else:
                        error_msg = 'Ошибка с аудио обработкой'
                        self.log.error(error_msg)
                        response = json.dumps({'error': error_msg})
                        conn.send(response.encode('utf-8'))
        except Exception as e:
            self.log.error(f'Ошибка {str(e)}', exc_info=True)
        finally:
            conn.close()

    def stop(self):
        self.is_running = False
        if self.socket:
            self.socket.close()


if __name__ == '__main__':
    server = Server()
    try:
        server.run()
    except KeyboardInterrupt:
        print('\nЗавершение работы')
        server.stop()
