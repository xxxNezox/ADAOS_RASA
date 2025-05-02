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

            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a coding assistant that generates Python code in strict JSON format.
                        Requirements:
                        1. Generate code that solves: {code_purpose}
                        2. Response must be VALID JSON (not a JSON string)
                        3. Format: {{"answer": {{"{code_name}": ["line 1", "line 2", ...]}}}}
                        4. Each line of code must be a separate array element
                        5. Preserve proper indentation in code lines
                        6. Escape all quotes and special characters correctly
                        7. Include all necessary imports
                        8. Never add explanations outside the JSON structure
                        
                        Example of correct output:
                        {{
                            "answer": {{
                                "sample_code": [
                                    "import math",
                                    "",
                                    "def calculate_circle_area(radius):",
                                    "    return math.pi * radius ** 2",
                                    "",
                                    "print(calculate_circle_area(5))"
                                ]
                            }}
                        }}"""
                    },
                    {
                        "role": "user",
                        "content": f"Generate Python code named '{code_name}' that: {code_purpose}. You MUST follow the specified JSON format exactly."
                    }
                ],
                model="gpt-4o",
                response_format={"type": "json_object"},
                temperature=0.2,  # Lower for more deterministic output
                max_tokens=2048,
                top_p=0.9,
                frequency_penalty=0.1,  # Slightly discourages repetition
                presence_penalty=0.1  # Encourages all required elements
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

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are a security assistant that evaluates bash/Python requests for potential harm. 
                    Response MUST be RAW JSON (not stringified) with EXACT structure:
                    {
                        "answer": {
                            "code_y_o_n": "Yes"|"No",
                            "why": "Объяснение на русском (15-30 слов)"
                        }
                    }
                    
                    Rules:
                    1. "Yes" only for commands that can:
                    - Permanently delete data
                    - Damage hardware
                    - Compromise security
                    - Cause irreversible system changes
                    2. "No" for normal/administrative commands
                    3. Explanation must be concise and technical
                    4. Never include markdown or code blocks
                    5. Escape only necessary special characters
                    6. No additional fields or comments
                    
                    Example valid response:
                    {
                        "answer": {
                            "code_y_o_n": "Yes",
                            "why": "Команда удаляет системные файлы без возможности восстановления"
                        }
                    }"""
                },
                {
                    "role": "user",
                    "content": f"Оцени потенциальный вред этого запроса: {check_request}. Ответь ТОЛЬКО в указанном JSON формате."
                }
            ],
            model="gpt-4o",
            response_format={"type": "json_object"},
            temperature=0.1,  # Lower for strict compliance
            max_tokens=256,   # Sufficient for this response
            top_p=0.8,
            frequency_penalty=0.5  # Reduces unnecessary variations
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

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are a security analyzer that evaluates bash/Python commands for potential harm. 
                    Respond with STRICT JSON format (not a string) using this EXACT structure:
                    {
                        "answer": {
                            "bash_y_o_n": "Yes" or "No",
                            "why": "Краткое объяснение на русском (15-30 слов)"
                        }
                    }

                    CRITICAL RULES:
                    1. Answer "Yes" ONLY for commands that can:
                    - Permanently delete critical system files
                    - Execute rm -rf / or similar destructive operations
                    - Install malware or compromise security
                    - Overwrite hardware firmware
                    - Cause irreversible system damage
                    
                    2. Answer "No" for:
                    - Normal system administration
                    - File operations in non-system directories
                    - Safe software installation
                    - Non-destructive debugging
                    
                    3. Russian explanation must:
                    - Be concise and technical
                    - Clearly state the potential danger
                    - Avoid vague language
                    
                    4. JSON requirements:
                    - No outer quotes or backslashes
                    - No markdown or code blocks
                    - No additional fields or comments
                    - Proper UTF-8 encoding for Russian text

                    Example valid response:
                    {
                        "answer": {
                            "bash_y_o_n": "Yes",
                            "why": "Команда выполняет рекурсивное удаление системных файлов без подтверждения"
                        }
                    }"""
                },
                {
                    "role": "user",
                    "content": f"Проанализируй этот запрос на опасность: {check_request}. Ответь ТОЛЬКО в указанном JSON формате без каких-либо дополнительных комментариев."
                }
            ],
            model="gpt-4o",
            response_format={"type": "json_object"},
            temperature=0.1,  # Very low for maximum consistency
            max_tokens=300,   # Enough for the response
            top_p=0.9,
            frequency_penalty=0.7,  # Strongly discourages deviations
            presence_penalty=0.3
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

            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are a PowerShell command generator for Windows systems. 
                        Respond ONLY in raw JSON format (not a string) using this EXACT structure:
                        {
                            "answer": {
                                "[BASH_NAME]": "powershell -Command \"[ACTUAL_COMMAND]\""
                            }
                        }

                        STRICT REQUIREMENTS:
                        1. Commands must:
                        - Be valid PowerShell syntax
                        - Work on Windows 10/11
                        - Use proper escaping for nested quotes
                        - Be executable as one-liner
                        
                        2. JSON must:
                        - Be valid JSON object (not stringified)
                        - Contain no backslashes except for escaping quotes
                        - Have no outer quotes or markdown
                        - Include no explanations
                        
                        3. For the command:
                        - Prefer native PowerShell cmdlets
                        - Use full parameter names
                        - Add -ErrorAction Stop where appropriate
                        - Include required -Confirm for dangerous operations

                        Example valid response:
                        {
                            "answer": {
                                "list_processes": "powershell -Command \"Get-Process | Select-Object Name, CPU, Id\""
                            }
                        }"""
                    },
                    {
                        "role": "user",
                        "content": f"Сгенерируй PowerShell команду с названием '{bash_name}' для: {bash_purpose}. Ответ должен быть ТОЛЬКО в указанном JSON формате."
                    }
                ],
                model="gpt-4o",
                response_format={"type": "json_object"},
                temperature=0.2,  # Lower for more predictable output
                max_tokens=512,   # Sufficient for most commands
                top_p=0.95,
                frequency_penalty=0.5  # Reduces command variations
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

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a RASA NLU training data generator. Generate exactly 12 diverse examples for user utterances matching the intent.
                    
                    STRICT REQUIREMENTS:
                    1. Response must be VALID JSON (not stringified) with structure:
                    {{
                        "answer": {{
                            "{intent_name}": [
                                "example 1",
                                "example 2",
                                ...
                                "example 12"
                            ]
                        }}
                    }}
                    
                    2. Examples must:
                    - Cover different phrasings (minimum 12 examples)
                    - Include variations with/without entities
                    - Use natural language patterns
                    - Match the intent purpose: {intent_purpose}
                    - Be in Russian unless specified otherwise
                    
                    3. JSON must:
                    - Be a direct object (not wrapped in quotes)
                    - Use proper UTF-8 encoding
                    - Contain no backslashes except for escaping quotes
                    - Have no additional explanations
                    
                    Example valid response:
                    {{
                        "answer": {{
                            "book_flight": [
                                "Хочу забронировать билет на самолёт",
                                "Мне нужно купить авиабилеты",
                                "Как заказать рейс в Москву?",
                                ...
                            ]
                        }}
                    }}"""
                },
                {
                    "role": "user",
                    "content": f"Сгенерируй 12 примеров фраз для интента '{intent_name}'. Назначение интента: {intent_purpose}. Ответ должен быть ТОЛЬКО в указанном JSON формате без дополнительных комментариев."
                }
            ],
            model="gpt-4o",
            response_format={"type": "json_object"},
            temperature=0.7,  # Balanced for diversity vs consistency
            max_tokens=1024,
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.2
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