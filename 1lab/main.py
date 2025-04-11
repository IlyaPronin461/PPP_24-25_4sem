import subprocess
import time
import os
import sys

def run_server():
    server_script = os.path.join(os.path.dirname(__file__), 'server.py')
    return subprocess.Popen([sys.executable, server_script])

def run_client():
    client_script = os.path.join(os.path.dirname(__file__), 'client.py')
    audio_dir = os.path.join(os.path.dirname(__file__), 'audio')
    os.makedirs(audio_dir, exist_ok=True)

    commands = [
        ['get'],
        ['refresh'],
        ['list'],
        ['cut', '--file', 'Depeche_Mode_-_Policy_Of_Truth_47897760.mp3', '--segment', '1', '--output', 'output_segment_1.mp3'],
        ['cut', '--file', 'Depeche_Mode_-_Policy_Of_Truth_47897760.mp3', '--segment', '5', '--output', 'output_segment_5.mp3'],
    ]

    for cmd in commands:
        print(f"\nВыполнение команды: {' '.join(cmd)}")
        subprocess.run([sys.executable, client_script] + cmd)
        time.sleep(1)

def main():
    server = run_server()
    time.sleep(2)
    try:
        print('\nВыполнение клиентских команд')
        run_client()
    except Exception as e:
        print(f"Ошибка в выполнении: {e}")
    finally:
        print('\nЗавершение работы')
        server.terminate()
        server.wait()

if __name__ == '__main__':
    main()
