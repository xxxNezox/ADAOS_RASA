from openai import OpenAI
import os

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API")

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key= DEEPSEEK_API_KEY,
)

response =  client.chat.completions.create(
        model="deepseek/deepseek-r1-0528-qwen3-8b:free",
        messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Please, provide response in JSON. Store answer in dictionary 'answer'. In this dictionary must be 2 keys: 'question' and 'response'. Response must be string",
                },
                {
                    "role": "user",
                    "content": "Сколько пива можешь назвать видов",
                }
            ]
        )
print(response.choices[0].message.content)