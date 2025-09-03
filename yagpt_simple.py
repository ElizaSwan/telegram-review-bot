import aiohttp
import os
import asyncio

class YandexGPTClient:
    def __init__(self):
        self.api_key = os.getenv('YANDEX_API_KEY', '')
        self.folder_id = os.getenv('YANDEX_FOLDER_ID', '')
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    async def generate_review(self, gender, service, likes, recommendation, comment=""):
        try:
            prompt = f"""
Сгенерируй отзыв о риелторских услугах Demyanov realty.

Пол: {gender}
Услуга: {service}
Понравилось: {', '.join(likes) if likes else 'нет'}
Рекомендует: {'да' if recommendation == '✅ Да' else 'нет'}
Комментарий: {comment if comment else 'нет'}

Сделай отзыв естественным, 3-5 предложений.
"""

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Api-Key {self.api_key}",
                "x-folder-id": self.folder_id
            }

            data = {
                "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.7,
                    "maxTokens": 500
                },
                "messages": [
                    {
                        "role": "user",
                        "text": prompt
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['result']['alternatives'][0]['message']['text'].strip()
                    else:
                        return None

        except Exception:
            return None

# Создаем экземпляр
yagpt_client = YandexGPTClient()