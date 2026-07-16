
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key="",
)

completion = client.chat.completions.create(
    model="Qwen/Qwen2.5-Coder-7B-Instruct:nscale",
    messages=[
        {
            "role": "user",
            "content": "where are you from?"
        }
    ],
)

print(completion.choices[0].message)
