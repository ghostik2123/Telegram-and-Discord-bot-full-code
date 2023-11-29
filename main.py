from keep_alive import keep_alive
keep_alive()
#import
import discord
import os
import telebot
from datetime import datetime

#telegram code 
token = os.environ['token']
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
CHAT_ID = ['2023014289', '6697778630', '2106774730']

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def send_file_to_telegram(file_path):
    try:
        with open(file_path, 'rb') as file:
            for chat_id in CHAT_ID:
                bot.send_document(chat_id, file)
    except Exception as e:
        print(f'Ошибка отправки файла в Telegram: {e}')

file_size = os.path.getsize('log.txt')  # Получаем размер файла
if file_size >= 100 * 1024:  # Если размер файла превышает 100 МБ (100кб)
    send_file_to_telegram('log.txt')  # Отправляем файл в телеграм
    open('log.txt', 'w').close()  # Очищаем файл после отправки

intents = discord.Intents.all()  # Включаем все возможные события
client = discord.Client(intents=intents)


## Обновленное событие для логирования входа в голосовой канал
@client.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:  # Проверяем, изменился ли голосовой канал
        if after.channel:  # Если член зашел в голосовой канал
            log_message(f'{member} зашел в голосовой канал {after.channel} на сервере {after.channel.guild}.')
            if member.bot:
                return
        else:  # Если член вышел из голосового канала
            log_message(f'{member} покинул голосовой канал {before.channel} на сервере {before.channel.guild}.')
            if member.bot:
                return
@client.event
async def on_ready():
    print(f'вошли в систему под именем {client.user}')

@client.event
async def on_message(message):
    # Логируем все сообщения в текстовый файл
    log_message(f'{message.guild} #{message.channel} - {message.author}: {message.content}')

@client.event
async def on_member_update(before, after):
    # Логируем изменения статуса участников
    log_message(f'{after.guild} - {after.name} изменил статус: {before.status} -> {after.status}')

@client.event
async def on_message_delete(message):
    # Логируем удаленные сообщения
    log_message(f'{message.guild} #{message.channel} - {message.author} удалил сообщение: {message.content}')
@client.event
async def on_message_edit(before, after):
    # Логируем отредактированные сообщения
    log_message(f'{before.guild} #{before.channel} - {before.author} изменил сообщение: {before.content} -> {after.content}')

def log_message(text):
    log_path = 'log.txt'
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f'[{timestamp}] {text}\n'
    with open(log_path, 'a', encoding='utf-8') as log_file:
        log_file.write(log_entry)

client.run(token)
