import requests
import datetime as dt
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import pymorphy2
import os
from openai import OpenAI
import json
import base64
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
#-----------------------------------------Вопрос к ГПТ-----------------------------------------#
class ActionAskGPT(Action):
    def name(self) -> str:
        return "action_ask_GPT"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        
        ask = tracker.get_slot("search_query")
    
        dispatcher.utter_message(json_message = {"type":"prompt", "data": f"Ты дружелюбный ассистент, твоя задача отвечать на вопросы пользователя. Ответ должен быть в пределах 50 слов. В ответе укажи только ответ {ask}. "})

        return[SlotSet("search_query")]


#-----------------------------------------Научиться новому коду-----------------------------------------#
class АctionLearnNewCode(Action):
    def name(self) -> str:
        return "action_learn_new_code"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):

        check_request = tracker.latest_message.get("text")
    
        dispatcher.utter_message(json_message = {"type":"code_prompt", "data": f"Напиши простой код python код по запросу пользователя. Запрос такой: {check_request}.В ответе верни только код и ничего больше"})
    
        return[SlotSet("new_code_name"), SlotSet("new_code_info"), SlotSet("code_y_o_n")]


#-----------------------------------------Научиться новому башу-----------------------------------------#
class АctionLearnNewBash(Action):
    def name(self) -> str:
        return "action_learn_new_bash"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):

        check_request = tracker.latest_message.get("text")
    
        dispatcher.utter_message(json_message = {"type":"bash_prompt", "data": f"Напиши простой bash скрипт по запросу пользователя. Запрос такой: {check_request}. В ответе верни только баш и ничего больше"})
    
        return[SlotSet("new_bash_name"), SlotSet("new_bash_info"), SlotSet("bash_y_o_n")]


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