import aiohttp
import json
import logging
import asyncio
import os
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

# Простой конфиг внутри файла
class YandexConfig:
    API_KEY = os.getenv('YANDEX_API_KEY', '')
    FOLDER_ID = os.getenv('YANDEX_FOLDER_ID', '')
    TEMPERATURE = 0.7
    MAX_TOKENS = 500
    TIMEOUT = 30

logger = logging.getLogger(__name__)

class YandexGPTClient:
    BASE_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    def __init__(self):
        self.api_key = YandexConfig.API_KEY
        self.folder_id = YandexConfig.FOLDER_ID
        self.model_uri = f"gpt://{self.folder_id}/yandexgpt-lite"
        self.timeout = aiohttp.ClientTimeout(total=YandexConfig.TIMEOUT)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_review(self, gender: str, service: str, likes: list, recommendation: str, comment: str = "") -> Optional[str]:
        try:
            prompt = self._build_prompt(gender, service, likes, recommendation, comment)
            payload = self._build_payload(prompt)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Api-Key {self.api_key}",
                "x-folder-id": self.folder_id
            }

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.BASE_URL, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['result']['alternatives'][0]['message']['text'].strip()
                    else:
                        error_text = await response.text()
                        logger.error(f"YaGPT API error: {response.status} - {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Error generating review: {e}")
            return None

    def _build_prompt(self, gender: str, service: str, likes: list, recommendation: str, comment: str) -> str:
        gender_text = "женщина" if "женск" in gender.lower() else "мужчина"
        recommendation_text = "рекомендует" if recommendation == "✅ Да" else "не рекомендует"
        likes_text = ", ".join(likes) if likes else "особых моментов не выделил(а)"

        return f"""
Сгенерируй искренний отзыв о риелторских услугах компании "Demyanov realty".

Информация:
- Пол: {gender_text}
- Услуга: {service}
- Понравилось: {likes_text}
- Рекомендует: {recommendation_text}
- Комментарий: {comment if comment else "нет"}

Требования:
- Естественный тон, как настоящий клиент
- 3-5 предложений
- Упоминание Demyanov realty
- Учет выбранных преимуществ
- Позитивный настрой
- Без эмодзи и маркдауна
- Грамматически правильный русский

Только текст отзыва.
"""

    def _build_payload(self, prompt: str) -> Dict[str, Any]:
        return {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": YandexConfig.TEMPERATURE,
                "maxTokens": YandexConfig.MAX_TOKENS
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Ты генератор естественных отзывов о риелторских услугах."
                },
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }

# Создаем экземпляр клиента для импорта
yagpt_client = YandexGPTClient()