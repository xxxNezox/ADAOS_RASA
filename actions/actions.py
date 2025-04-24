import requests
import datetime as dt
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import pymorphy2
import os
from openai import OpenAI
import json

API_KEY = os.getenv("API_KEY")

#-----------------------------------------Вопрос к ГПТ-----------------------------------------#
class ActionAskGPT(Action):
    def name(self) -> str:
        return "action_ask_GPT"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        
        ask = tracker.get_slot("search_query")

        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key= API_KEY
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

        harmness = tracker.get_slot("code_y_o_n")

        if harmness == True:
            dispatcher.utter_message(json_message = {"type":"code", "data": f"Я не стану выполнять этот код. Он может навредить вашему ПК"})
            return[SlotSet("new_request_name"), SlotSet("new_request_info")]
        else:    
            client = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key= API_KEY
            )

            code_name = tracker.get_slot("new_code_name")
            code_purpose = tracker.get_slot("new_code_info")

            response =  client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": f"Write Python code that solves the following task: {code_purpose}. Instead of outputting the code as plain text, return it as a JSON object. Do not serialize the whole JSON as a string. Each line of code should be a plain string in a list, and the full output must be a proper JSON object, and the structure must be: {{'answer': {{'{code_name}': ['line of code 1','line of code 2','line of code 3','...']}}}}. Make sure all quotes and special characters are properly escaped so that the output is valid JSON."
                    },
                    {
                        "role": "user",
                        "content": f"Создай мне Python код с названием: {code_name}. Код должен выполнять следующее: {code_purpose}"
                    }
                ],
                model="gpt-4o",
                response_format={ "type" : "json_object"},
                temperature=.3,
                max_tokens=2048,
                top_p=1
            )

            data = json.loads(response.choices[0].message.content)

            dispatcher.utter_message(json_message = {"type":"code", "data": f"{data}"})
            return[SlotSet("new_code_name"), SlotSet("new_code_info"), SlotSet("code_y_o_n")]


#-----------------------------------------Сделать первичную проверку опасности баша-----------------------------------------#
class АctionCheckCodeHarmness(Action):
    def name(self) -> str:
        return "action_check_code_harmness"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key= API_KEY
    )

        check_request = tracker.latest_message.get("text")

        response =  client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant checking if a user’s request for a bash command or python code is potentially harmful. Respond ONLY in valid JSON format with the following structure: {'answer': {'code_y_o_n': 'Yes' if it can bring severe harm to user PC or even destroy it or 'No' if it relatively harmless, 'why': 'Brief explanation in Russian language'}}. Do not wrap the `data` dictionary in quotes. `data` must be a JSON object, not a string. Do not include backslashes or escape quotes inside values unnecessarily. Return raw JSON only, with no extra text.",
                },
                {
                    "role": "user",
                    "content": f"Проверь такой запрос пользователя: {check_request}."
                }
            ],
            model="gpt-4o",
            response_format={ "type" : "json_object"},
            temperature=.3,
            max_tokens=2048,
            top_p=1
        )

        data = json.loads(response.choices[0].message.content)

        if data["answer"]["code_y_o_n"].lower() == "yes":
            return[SlotSet("code_y_o_n", True)]
        else:
            return[SlotSet("code_y_o_n", False)]


#-----------------------------------------Сделать первичную проверку опасности кода-----------------------------------------#
class АctionCheckBashHarmness(Action):
    def name(self) -> str:
        return "action_check_bash_harmness"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key= API_KEY
    )

        check_request = tracker.latest_message.get("text")

        response =  client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant checking if a user’s request for a bash command or python code is potentially harmful. Respond ONLY in valid JSON format with the following structure: {'answer': {'bash_y_o_n': 'Yes' if it can bring severe harm to user PC or even destroy it or 'No' if it relatively harmless, 'why': 'Brief explanation in Russian language'}}. Do not wrap the `data` dictionary in quotes. `data` must be a JSON object, not a string. Do not include backslashes or escape quotes inside values unnecessarily. Return raw JSON only, with no extra text.",
                },
                {
                    "role": "user",
                    "content": f"Проверь такой запрос пользователя: {check_request}."
                }
            ],
            model="gpt-4o",
            response_format={ "type" : "json_object"},
            temperature=.3,
            max_tokens=2048,
            top_p=1
        )

        data = json.loads(response.choices[0].message.content)

        if data["answer"]["bash_y_o_n"].lower() == "yes":
            return[SlotSet("bash_y_o_n", True)]
        else:
            return[SlotSet("bash_y_o_n", False)]
        

#-----------------------------------------Научиться новому башу-----------------------------------------#
class АctionLearnNewBash(Action):
    def name(self) -> str:
        return "action_learn_new_bash"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        
        harmness = tracker.get_slot("bash_y_o_n")

        if harmness == True:
            dispatcher.utter_message(json_message = {"type":"bash", "data": f"Я не стану выполнять эту команду, она имеет высокую угрозу стабильности ПК"})
            return[SlotSet("new_request_name"), SlotSet("new_request_info")]
        else:    
            client = OpenAI(
                base_url="https://models.inference.ai.azure.com",
                api_key= API_KEY
            )

            bash_name = tracker.get_slot("new_request_name")
            bash_purpose = tracker.get_slot("new_request_info")

            response =  client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": f"You are bash command creator for Windows powershell. Do not use backslashes or escape quotes. Respond ONLY in valid JSON format with the following structure: {{'answer': {{'{bash_name}': Put created bash command here}}}}. Do not wrap the `data` dictionary in quotes. `data` must be a JSON object, not a string. Return raw JSON only, with no extra text. ",
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

            dispatcher.utter_message(json_message = {"type":"bash", "data": f"{data['answer'][f'{bash_name}']}"})
            return[SlotSet("new_bash_name"), SlotSet("new_bash_info"), SlotSet("bash_y_o_n")]


#-----------------------------------------Научиться новому интенту-----------------------------------------#
class АctionLearnNewIntent(Action):
    def name(self) -> str:
        return "action_learn_new_intent"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):

        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key= API_KEY
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