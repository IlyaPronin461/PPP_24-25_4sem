# файл с сервером
from pydub import AudioSegment
import eyed3
import os
import json
import threading
import socket
import io
import logging


class Server:
    def __init__(self, host='localhost', port=8899, audio_folder='audio'):
        self.host = host
        self.port = port
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.audio_folder = os.path.join(current_dir, audio_folder)
        self.track_info = {}
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
        for file in os.listdir(self.audio_folder):
            if file.endswith(('.mp3', '.wav')):
                full_path = os.path.join(self.audio_folder, file)
                try:
                    audio = eyed3.load(full_path)
                    self.track_info[file] = {
                        'name': audio.tag.title,
                        'artist': audio.tag.artist,
                        'album': audio.tag.album,
                        'year': str(audio.tag.recording_date) if audio.tag.recording_date else None,
                        'duration': audio.info.time_secs
                    }
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

    def cut_audio(self, track_num, start, end):
        try:
            self.log.info('Запрос на то, чтобы обрезать файл')
            tracks = list(self.track_info.keys())
            if track_num >= len(tracks):
                return None

            track_path = os.path.join(self.audio_folder, tracks[track_num])
            self.log.debug(f'Загрузка {track_path}')

            sound = AudioSegment.from_mp3(track_path)
            self.log.debug(f'Файл загружен, длительность: {len(sound) / 1000} секунд')

            start_ms = int(float(start) * 1000)
            end_ms = int(float(end) * 1000)

            self.log.debug('Обрезка аудио')
            segment = sound[start_ms:end_ms]

            buffer = io.BytesIO()
            segment.export(buffer, format='mp3')

            result = buffer.getvalue()
            self.log.info('Обрезка завершена')
            return result
        except Exception as e:
            self.log.error(f'Ошибка при обработке аудио: {str(e)}', exc_info=True)
            return None

    def process_client(self, conn):
        try:
            client_addr = conn.getpeername()
            self.log.info(f'Обращается клинет {client_addr}')

            while True:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break

                self.log.debug(f'{client_addr} сделал запро: {data}')

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
                    self.log.debug('Возвращение фрагмента аудио')
                    track_num = request.get('file_index')
                    start = request.get('start_time')
                    end = request.get('end_time')

                    if not all([track_num is not None, start, end]):
                        error = 'Нужно указать все параметры'
                        self.log.error(error)
                        response = json.dumps({'error': error})
                        conn.send(response.encode('utf-8'))
                        continue

                    audio = self.cut_audio(track_num, start, end)
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