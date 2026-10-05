# -*- coding: utf-8 -*-
import socket
import threading
import random
import os

# Порт для бесплатного облака (Render автоматически подставляет нужный порт через переменную среды)
PORT = int(os.environ.get("PORT", 9999))
HOST = "0.0.0.0"  # Разрешаем подключения со всего глобального интернета

clients = {}  # ID: сокет

def load_users():
    users = {}
    if os.path.exists("users.txt"):
        with open("users.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "|" in line:
                    uid, pwd = line.split("|")
                    users[uid] = pwd
    return users

def save_user(uid, pwd):
    with open("users.txt", "a", encoding="utf-8") as f:
        f.write(f"{uid}|{pwd}\n")

def handle_client(client_sock, client_addr):
    print(f"[Сервер]: Новое сетевое подключение: {client_addr}")
    my_id = None
    users = load_users()
    
    try:
        while True:
            data = client_sock.recv(1024).decode('utf-8')
            if not data:
                break
                
            parts = data.split("|")
            cmd = parts[0]
            
            if cmd == "REG":
                pwd = parts[1]
                while True:
                    new_id = str(random.randint(100000, 999999))
                    if new_id not in users:
                        break
                save_user(new_id, pwd)
                users[new_id] = pwd
                client_sock.send(f"REG_OK|{new_id}".encode('utf-8'))
                print(f"[Регистрация]: Создан новый аккаунт ID: {new_id}")
                
            elif cmd == "AUTH":
                uid = parts[1]
                pwd = parts[2]
                if uid in users and users[uid] == pwd:
                    my_id = uid
                    clients[my_id] = client_sock
                    client_sock.send("AUTH_OK".encode('utf-8'))
                    print(f"[Вход]: Пользователь {my_id} вошел в сеть.")
                else:
                    client_sock.send("AUTH_ERR".encode('utf-8'))
                    
            elif cmd == "MSG":
                if not my_id:
                    continue
                to_id = parts[1]
                msg_text = parts[2]
                
                # Перезагружаем базу на случай ручного добавления админа через Блокнот
                users = load_users()
                
                if to_id not in users:
                    client_sock.send("ERR_NOT_FOUND".encode('utf-8'))
                elif to_id in clients:
                    clients[to_id].send(f"FROM|{my_id}|{msg_text}".encode('utf-8'))
                else:
                    client_sock.send("ERR_OFFLINE".encode('utf-8'))
    except:
        pass
    finally:
        if my_id and my_id in clients:
            del clients[my_id]
            print(f"[Выход]: Пользователь {my_id} отключился.")
        client_sock.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Позволяет перезапускать сервер мгновенно без залипания порта в памяти облака
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[Старт]: сервер PM запущен на порту {PORT}...")
        print(f"Загружено пользователей из базы: {len(load_users())}")
        print("Ожидание подключений к PM...")
    except Exception as e:
        print(f"[Ошибка старта]: {e}")
        return

    while True:
        try:
            client_sock, client_addr = server.accept()
            threading.Thread(target=handle_client, args=(client_sock, client_addr), daemon=True).start()
        except:
            break

if __name__ == "__main__":
    main()