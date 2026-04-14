import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_tg_notification(fb_obj): # Принимаем один объект fb
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Ошибка: Токен или Chat ID не найдены в .env")
        return

    # Достаем данные прямо из объекта
    message = (
        f"🚀 **Новая заявка с сайта!**\n\n"
        f"👤 Имя: {fb_obj.name}\n"
        f"📞 Тел: {fb_obj.phone}\n"
        f"📅 Дата: {fb_obj.date}\n"
        f"📝 Коммент: {fb_obj.comment}"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"})
        if response.status_code != 200:
            print(f"Ошибка Telegram API: {response.text}")
        else:
            print("--- Сообщение в Telegram успешно отправлено! ---")
    except Exception as e:
        print(f"Ошибка отправки в TG: {e}")