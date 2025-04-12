import requests
import datetime as dt
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import pymorphy2
import os
from openai import OpenAI
import json


#-----------------------------------------Вопрос к ГПТ-----------------------------------------#
class ActionAskGPT(Action):
    def name(self) -> str:
        return "action_ask_GPT"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        
        ask = tracker.get_slot("search_query")

        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key= ""
    )
        
        response =  client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Please, provide response in JSON. Store answer in dictionary 'answer'. In this dictionary must be 2 keys: 'question' and 'response'. Response must be string",
                },
                {
                    "role": "user",
                    "content": ask,
                }
            ],
            model="gpt-4o",
            response_format={ "type" : "json_object"},
            temperature=.3,
            max_tokens=2048,
            top_p=1
        )

        data = json.loads(response.choices[0].message.content)

        response_data = data.get("answer")

        answer = response_data["response"]

        dispatcher.utter_message(text= f"Ответ: {answer}")

        return[SlotSet("search_query")]


#-----------------------------------------Научиться новому коду-----------------------------------------#
class АctionLearnNewCode(Action):
    def name(self) -> str:
        return "action_learn_new_code"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):

        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key= ""
    )

        code_name = tracker.get_slot("new_intent_name")
        code_info = tracker.get_slot("new_intent_info")

        print(code_name)
        print(code_info)

        response =  client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are code creator on python. Please, provide response in JSON. Store answer in dictionary 'answer'. In this dictionary must be 1 key: '{code_name}'. Response must be string ",
                },
                {
                    "role": "user",
                    "content": f"Напиши мне код с названием файла: {code_name}.py, Этот код должен выполнять следующие действия: {code_info}"
                }
            ],
            model="gpt-4o",
            response_format={ "type" : "json_object"},
            temperature=.3,
            max_tokens=2048,
            top_p=1
        )

        data = json.loads(response.choices[0].message.content)


#-----------------------------------------Сделать первичную проверку опасности-----------------------------------------#
class АctionCheckHarmness(Action):
    def name(self) -> str:
        return "action_check_harmness"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key= ""
    )

        check_code = tracker.latest_message.get("text")

        response =  client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are hamrness checker. Please, provide response in JSON. Store answer in dictionary 'answer'. In this dictionary must be 2 key: 'y_o' and 'why'. You must provide at least 10 examples. Response must be string ",
                },
                {
                    "role": "user",
                    "content": f"Проверь такой запрос пользователя: {check_code}. Если он имеет высокую угрозу файлам пользователя, то напиши почему. Запиши в ключ 'y_o' ответ 'Да' или 'Нет' в зависимости от того, опасен ли код. В ключ 'why' запиши причину, почему он опасен."
                }
            ],
            model="gpt-4o",
            response_format={ "type" : "json_object"},
            temperature=.3,
            max_tokens=2048,
            top_p=1
        )

        data = json.loads(response.choices[0].message.content)

        dispatcher.utter_message(json_message = {"type":"check_command", "data": f"{data}"})


#-----------------------------------------Научиться новому башу-----------------------------------------#
class АctionLearnNewBash(Action):
    def name(self) -> str:
        return "action_learn_new_bash"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key= ""
    )

        bash_name = tracker.get_slot("new_intent_name")
        bash_purpose = tracker.get_slot("new_intent_info")

        print(bash_name)
        print(bash_purpose)

        response =  client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are bash command's creator. Please, provide response in JSON. Store answer in dictionary 'answer'. In this dictionary must be 1 key: '{bash_name}'. You must provide at least 10 examples. Response must be string ",
                },
                {
                    "role": "user",
                    "content": f"Создай мне bash команду с названием: {bash_name}. Эта команда должна выполнять следующее действие: {bash_purpose}"
                }
            ],
            model="gpt-4o",
            response_format={ "type" : "json_object"},
            temperature=.3,
            max_tokens=2048,
            top_p=1
        )

        data = json.loads(response.choices[0].message.content)


#-----------------------------------------Научиться новому интенту-----------------------------------------#
class АctionLearnNewIntent(Action):
    def name(self) -> str:
        return "action_learn_new_intent"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):

        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key= ""
    )

        intent_name = tracker.get_slot("new_intent_name")
        intent_purpose = tracker.get_slot("new_intent_info")

        print(intent_name)
        print(intent_purpose)

        response =  client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are example creator for intents in RASA. Please, provide response in JSON. Store answer in dictionary 'answer'. In this dictionary must be 1 key: '{intent_name}'. It must be list on examples. You must provide at least 10 examples. Response must be string ",
                },
                {
                    "role": "user",
                    "content": f"Создай мне примеры для интента: {intent_name}, Этот интент имеет следующее назначение: {intent_purpose}"
                }
            ],
            model="gpt-4o",
            response_format={ "type" : "json_object"},
            temperature=.3,
            max_tokens=2048,
            top_p=1
        )

        data = json.loads(response.choices[0].message.content)

        print(data)

        def generate_nlu_yaml(nlu_data):
            header = 'version: "3.1"\n\n\nnlu:\n'
            intents_text = ""

            for intent, examples in nlu_data.items():
                examples_block = "\n".join([f"    - {example}" for example in examples])
                intent_block = f"- intent: {intent}\n  examples: |\n{examples_block}\n"
                intents_text += intent_block + "\n"

            return header + intents_text.strip()

        nlu_data = data
        yaml_text = generate_nlu_yaml(nlu_data)

        with open(f"data/data_nlu/{intent_name}.yml", "w", encoding="utf-8") as f:
            f.write(yaml_text)

        dispatcher.utter_message(text=f"По вашему запросу, я научилась интенту: {intent_name}, он находится в папке data/data_nlu")

        return[SlotSet("new_intent_name"), SlotSet("new_intent_info")]


#-----------------------------------------Сохранить пример-----------------------------------------#
class АctionSaveExampleToIntent(Action):
    def name(self) -> str:
        return "action_save_example_to_intent"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):

        directory = "data/data_nlu"
        intent_name = tracker.latest_message['intent'].get('name')
        new_example = tracker.latest_message.get("text")

        last_entity_value = tracker.get_slot("last_entity_value")
        last_entity_name = tracker.get_slot("last_entity_name")

        print(last_entity_value)
        print(last_entity_name)

        filepath = os.path.join(directory, f"{intent_name}.yml")
        
        if last_entity_name and last_entity_value:
            message = new_example.replace(last_entity_value, f"[{last_entity_value}]({last_entity_name})")
        else:
            message = new_example

        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()

        if not os.path.exists(filepath):
            dispatcher.utter_message(text=f"Файл для интента {intent_name} не найден в {directory}")
            return
        
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()

        if message in content:
            return
        
        with open(filepath, "a", encoding="utf-8") as file:
            file.write(f"\n    - {message}")

        return [SlotSet("last_entity_name"), SlotSet(("last_entity_value"))]


#-----------------------------------------Создать команду для powershell-----------------------------------------#
class ActionCreateCommand(Action):
    def name(self) -> str:
        return "action_create_command"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):

        command = tracker.get_intent_of_latest_message()

        if command == "create_folder":
            user_command = 'mkdir "C:\\Users\\plant\\Desktop\\new_folder"'
        elif command == "delete_folder":
            user_command = 'Remove-Item -Path "C:\\Users\\plant\\Desktop\\new_folder" -Recurse -Force'
        elif command == "create_file":
            user_command = 'New-Item -Path "C:\\Users\\plant\\Desktop\\file.txt" -ItemType File -Force'
        elif command == "delete_file":
            user_command = 'Remove-Item -Path "C:\\Users\\plant\\Desktop\\file.txt" -Force'

        dispatcher.utter_message(json_message = {"type":"bash", "data": f"{user_command}"})


#-----------------------------------------Получить время-----------------------------------------#
class ActionShowTime(Action):
    def name(self) -> str:
        return "action_show_time"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):

        current_time = dt.datetime.now().strftime('%H:%M:%S')

        dispatcher.utter_message(json_message = {"type":"text", "data": f"Текущее время:{current_time}"})


#-----------------------------------------Получить погоду-----------------------------------------#
class ActionGetWeather(Action):
    def name(self) -> str:
        return "action_get_weather"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):

        user_location = tracker.get_slot("last_entity_value")

        morph = pymorphy2.MorphAnalyzer()
        word = user_location
        lemma = morph.parse(word)[0].normal_form
        lemma = lemma.capitalize()

        api_key = "c5d07661c7168c73f4c654904566fbc4"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={lemma}&appid={api_key}&units=metric&lang=ru"

        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            temp = data["main"]["temp"]
            description = data["weather"][0]["description"]
            dispatcher.utter_message(json_message = {"type":"text", "data": f"В городе {lemma} сейчас {temp}°C, {description}."})
        else:
            dispatcher.utter_message(json_message = {"type":"text", "data": "Я не смог найти погоду для этого города. Попробуйте другой город."})