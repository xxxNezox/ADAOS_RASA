import json
import base64

code_name = 'aboba'

with open('pivo.py', 'rb') as file:
    file_data = file.read()

# Кодируем бинарные данные в строку Base64
encoded_data = base64.b64encode(file_data).decode('utf-8')

json_message = {
    "type": "code",
    "file_name": f"{code_name}",
    "data": f"{encoded_data}"
}

file_name = json_message["file_name"]

# 2. Декодируем base64 в байты
file_data = base64.b64decode(json_message["data"])

# 3. Сохраняем в файл
with open(f"{file_name}.py", "wb") as f:
    f.write(file_data)

print(f"Файл {file_name} успешно сохранён.")