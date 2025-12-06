#!/usr/bin/env python3
"""
Telegram бот для автоматических ответов в групповых чатах.
Отвечает на сообщения, содержащие определенные ключевые слова.
"""

import json
import logging
import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Не установлена переменная окружения BOT_TOKEN!")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def load_qa_data() -> list:
    """Загружает вопросы и ответы из JSON файла."""
    try:
        with open('qa_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('questions', [])
    except FileNotFoundError:
        logger.error("Файл qa_data.json не найден!")
        return []
    except json.JSONDecodeError:
        logger.error("Ошибка при чтении JSON файла!")
        return []


def find_answer(message_text: str, qa_data: list) -> dict | None:
    """
    Ищет ответ на основе ключевых слов в сообщении.
    
    Args:
        message_text: Текст сообщения
        qa_data: Список вопросов и ответов
        
    Returns:
        Словарь с ответом, если найдено совпадение, иначе None
    """
    message_lower = message_text.lower()
    
    for qa in qa_data:
        keywords = qa.get('keywords', [])
        for keyword in keywords:
            if keyword.lower() in message_lower:
                return {
                    'type': qa.get('type', 'text'),
                    'answer': qa.get('answer'),
                    'caption': qa.get('caption', '')
                }
    
    return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик входящих сообщений.
    Проверяет наличие ключевых слов и отправляет ответ.
    """
    if not update.message or not update.message.text:
        return
    
    message_text = update.message.text
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    logger.info(f"Получено сообщение в чате {chat_id} ({chat_type}): {message_text[:50]}...")
    
    # Загружаем данные Q&A
    qa_data = load_qa_data()
    
    # Ищем ответ
    result = find_answer(message_text, qa_data)
    
    if result:
        answer_type = result['type']
        answer = result['answer']
        caption = result['caption']
        
        if answer_type == 'photo':
            # Отправляем фото
            logger.info(f"Отправляем фото: {answer}")
            try:
                with open(answer, 'rb') as photo:
                    await update.message.reply_photo(photo=photo, caption=caption if caption else None)
            except FileNotFoundError:
                logger.error(f"Файл не найден: {answer}")
                await update.message.reply_text("Извините, файл не найден.")
        else:
            # Отправляем текст
            logger.info(f"Найден ответ для сообщения: {answer[:50]}...")
            await update.message.reply_text(answer)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок."""
    logger.error(f"Произошла ошибка: {context.error}")


def main() -> None:
    """Запуск бота."""
    logger.info("Запуск бота...")
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчик сообщений (работает в личных чатах и группах)
    # filters.TEXT - только текстовые сообщения
    # ~filters.COMMAND - исключаем команды
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    logger.info("Бот запущен и готов к работе!")
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
