import yadisk
import json
import random
import os
import requests
import re


TELEGRAM_API_TOKEN = "ваш_телеграм_токен"
YANDEX_API_TOKEN = "ваш_яндекс_токен"

YANDEX_FOLDER_URL = "https://cloud-api.yandex.net/v1/disk/resources"
TELEGRAM_FOLDER_URL = f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/"

YANDEX_FILES_PATH = "disk:/bot/res/"  # Путь на Яндекс Диске, где будут храниться файлы


def get_file_from_yandex_disk(file_path):
    headers = {"Authorization": f"OAuth {YANDEX_API_TOKEN}"}
    params = {"path": file_path}
    url = YANDEX_FOLDER_URL + "/download"
    response = requests.get(url, headers=headers, params=params)
    file_link = response.json().get("href", "")
    file_content = requests.get(file_link).content if file_link else None
    return file_content.decode('utf-8') if file_content else None


def upload_file_to_yandex_disk(file_path, content):
    headers = {"Authorization": f"OAuth {YANDEX_API_TOKEN}"}
    params = {"path": file_path, "overwrite": "true"}
    url = YANDEX_FOLDER_URL + "/upload"
    get_link = requests.get(url, headers=headers, params=params).json()
    upload_link = get_link.get("href", "")
    if upload_link:
        requests.put(upload_link, files={"file": content})


def load_allowed_users(file_name="allowed_users.txt"):
    file_content = get_file_from_yandex_disk(YANDEX_FILES_PATH + file_name)
    if file_content:
        return set(file_content.strip().split('\n'))
    return set()


def get_user_name(message):
    user = message.get("from", {})
    username = user.get("username", "")
    return username


def handle_get_backlog(chat_id):
    folder_path = "disk:/bot/working_folder"
    resources = get_resource_list(folder_path)
    digits_set = set()

    for resource_path in resources:
        file_name = os.path.basename(resource_path)
        digits = get_digits_from_filename(file_name)
        if digits:
            digits_set.add(digits)

    unique_digits_count = len(digits_set)
    total_files = len(resources)

    send_message(chat_id, f"Доступно шаблонов: {total_files}\nУникальных хидов: {unique_digits_count}")


def get_resource_list(folder_path):
    headers = {"Authorization": f"OAuth {YANDEX_API_TOKEN}"}
    params = {"path": folder_path, "fields": "_embedded.items.path"}
    response = requests.get(YANDEX_FOLDER_URL, headers=headers, params=params)
    resources = response.json().get("_embedded", {}).get("items", [])
    return [r["path"] for r in resources]


def load_user_files(file_name="user_files.txt"):
    user_files = {}
    file_content = get_file_from_yandex_disk(YANDEX_FILES_PATH + file_name)
    if file_content:
        for line in file_content.strip().split('\n'):
            user, file_name = line.strip().split(":", 1)
            user_files[user] = file_name
    return user_files


def move_file_to_folder(file_path, folder_path):
    headers = {"Authorization": f"OAuth {YANDEX_API_TOKEN}"}
    # Исправленный параметр "from" добавлен в params.
    params = {"from": file_path, "path": folder_path}
    response = requests.post(YANDEX_FOLDER_URL + "/move", headers=headers, params=params)
    if response.status_code != 201:
        print(f"Error moving file: {response.json()}")


def get_digits_from_filename(filename):
    digits = ""
    for char in filename:
        if char.isdigit():
            digits += char
        else:
            break
    return digits


def log_sent_file(user_name, file_path):
    file_name = os.path.basename(file_path)
    digits = get_digits_from_filename(file_name)
    log_file_content = get_file_from_yandex_disk(YANDEX_FILES_PATH + "sent_files_log.txt") or ""
    log_file_content += f"User {user_name}: {digits}\n"
    upload_file_to_yandex_disk(YANDEX_FILES_PATH + "sent_files_log.txt", log_file_content.encode('utf-8'))


#функция для загрузки истории отправленных файлов для пользователя:
def load_sent_files_for_user(user_name):
    sent_files = set()
    file_content = get_file_from_yandex_disk(YANDEX_FILES_PATH + "sent_files_log.txt")
    if file_content:
        for line in file_content.strip().split('\n'):
            if line.startswith(f"User {user_name}:"):
                sent_files.add(line.strip().split()[-1])
    return sent_files


def give_random_file(chat_id, user_name):
    resources = get_resource_list()
    sent_files = load_sent_files_for_user(user_name)

    # Фильтрация файлов на основе наличия порядкового номера в конце имени
    numbered_resources = [r for r in resources if re.search(r"\_\d+(\.\w+)?$", os.path.basename(r))]
    other_resources = [r for r in resources if r not in numbered_resources]

    # Проверка, не были ли файлы из numbered_resources уже отправлены пользователю
    available_numbered_resources = [r for r in numbered_resources if get_digits_from_filename(os.path.basename(r)) not in sent_files]

    # Если все файлы с номером уже были отправлены, переходим к другим файлам
    if not available_numbered_resources:
        available_resources = [r for r in other_resources if get_digits_from_filename(os.path.basename(r)) not in sent_files]
    else:
        available_resources = available_numbered_resources

    if not available_resources:
        send_message(chat_id, "Access denied")
        return

    random_path = random.choice(available_resources)
    download_url = f"{YANDEX_FOLDER_URL}/download?path={random_path}"
    send_message(chat_id, f"Sending {os.path.basename(random_path)}...")
    headers = {"Authorization": f"OAuth {YANDEX_API_TOKEN}"}
    response = requests.get(download_url, headers=headers)
    remote_file = requests.get(response.json()["href"])
    send_document(chat_id, os.path.basename(random_path), remote_file.content)

    log_sent_file(user_name, random_path)

    folder_path = f"disk:/bot/given_folder/{os.path.basename(random_path)}"
    move_file_to_folder(random_path, folder_path)


def handler(event, context):
    # Преобразуем тело запроса из строки в словарь Python
    body = json.loads(event['body'])
    updates = body.get("result", [])
    process_new_updates(updates)
    # Возвращаем 200 OK ответ серверу
    return {
        'statusCode': 200,
        'body': 'OK'
    }


def process_new_updates(updates):
    allowed_users = load_allowed_users()

    for update in updates:
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        user_name = get_user_name(message)
        text = message.get("text", "").strip()

        if user_name not in allowed_users:
            send_message(chat_id, "Кажется, что ты не являешься сотрудником Службы. За предоставлением доступа обратись к своему руководителю")
            continue

        # if text == "/start":
        #     send_image(chat_id, "60.jpg")  # Отправка картинки при старте
        if text == "/start":
            send_message(chat_id, "Привет! Я -- тестовая версия бота Службы! Пока мои возможности ограничены, но я уже умею:\n\n"
                                   "/get_file - выдавать ассортиментные файлы для Единого задания\n"
                                   "/backlog - возвращать текущий беклог (для менеджеров)")
        elif text == "/get_file":
            give_random_file(chat_id, user_name)
        elif text == "/backlog":
            handle_get_backlog(chat_id)  # Обработка команды /backlog


def send_message(chat_id, text):
    data = {"chat_id": chat_id, "text": text}
    url = TELEGRAM_FOLDER_URL + "sendMessage"
    response = requests.post(url, json=data)


def send_document(chat_id, filename, content):
    url = TELEGRAM_FOLDER_URL + "sendDocument"
    data = {"chat_id": chat_id}
    files = {"document": (filename, content)}
    response = requests.post(url, data=data, files=files)


def get_updates(offset=None):
    method = "getUpdates"
    params = {"offset": offset, "timeout": 10}

    try:
        resp = requests.get(TELEGRAM_FOLDER_URL + method, params)
        resp.raise_for_status()  # проверяем статус-код HTTP ответа
        json_data = resp.json()

        result = []  # инициализировать result как пустой список перед проверкой
        if "result" in json_data:
            result = json_data["result"]

    except requests.HTTPError as e:
        if e.response.status_code == 409:
            print("Warning: Conflict error (409) occurred, server might be processing simultaneous requests")
        else:
            print(f"Error: HTTP request failed: Error {e.response.status_code}: {e}")
        return []

    except Exception as e:
        print(f"Error: {e}")
        return []

    if not result:
        return []

    last_id = result[-1]["update_id"]
    process_new_updates(result)
    return last_id + 1


if __name__ == "__main__":
    update_id = None
    while True:
        try:
            update_id = get_updates(update_id)
        except Exception as e:
            print(f"Error: {e}")