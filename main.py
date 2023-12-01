from keep_alive import keep_alive
keep_alive()
#import
import os
import threading
import telebot
from telebot import types
from datetime import datetime
import pytz
import discord
from discord.ext import commands
from cryptography.fernet import Fernet
import re
import asyncio

intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)
#telegram code 
token = os.environ['token']
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
trusted_users = '2023014289'
CHAT_ID = ['2023014289','2106774730', '6697778630']
banned_users = []
timeouts = {}

@client.event
async def on_ready():
		print(f'вошли в систему под именем {client.user}')
	
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def send_file_to_telegram(file_path):
	try:
			with open(file_path, 'rb') as file:
					for chat_id in CHAT_ID:
							bot.send_document(chat_id, file)
	except Exception as e:
			print(f'Ошибка отправки файла в Telegram: {e}')

file_size = os.path.getsize('log.txt')
if file_size >= 100 * 1024:  # Если размер файла превышает 100 МБ (100кб)
	send_file_to_telegram('log.txt')
	open('log.txt', 'w').close()

#telegram commands
@bot.message_handler(commands=['help'])
def send_help(message):
		chat_id = str(message.chat.id)
		if chat_id in trusted_users:
				help_text = """
				Доступные команды:
				/log - Получить файл log.txt, если его размер больше 4KB и ваш chat_id добавлен в список.
				/add [chat_id] - Добавить новый chat_id в список.
				/list - Получить список всех chat_id.
				/del [chat_id] - Удалить chat_id из списка.
				/id - Получить ваш chat_id.
				/requestadd - Отправить запрос на добавление вашего chat_id в список.
				"""
		elif chat_id in CHAT_ID:
				help_text = """
				Доступные команды:
				/log - Получить файл log.txt, если его размер больше 4KB.
				/id - Получить ваш chat_id.
				"""
		else:
				help_text = """
				Вас нет в списке chat_id. Вы можете купить chat_id, перейдя по следующей ссылке: [ссылка на платежную систему]
				"""
		bot.reply_to(message, help_text)
#file
@bot.message_handler(commands=['file'])
def get_file_size(message):
		file_size = os.path.getsize('log.txt')
		bot.reply_to(message, f'Размер файла log.txt: {file_size} байт')

#reque
@bot.message_handler(commands=['requestadd'])
def request_add(message):
		global last_request_chat_id
		last_request_chat_id = str(message.chat.id)
		request_text = f'Пользователь {message.from_user.username} ({last_request_chat_id}) хочет добавить себя в список. Ответьте командой /accept для разрешения или /ignore для игнорирования.'
		bot.send_message(trusted_users, request_text)

@bot.message_handler(commands=['accept'])
def accept_request(message):
		global last_request_chat_id
		if str(message.from_user.id) not in trusted_users or last_request_chat_id is None:
				bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
				return

		if last_request_chat_id not in CHAT_ID:
				CHAT_ID.append(last_request_chat_id)
				bot.reply_to(message, f'Chat ID {last_request_chat_id} успешно добавлен.')
				bot.send_message(last_request_chat_id, 'Ваш запрос на добавление был одобрен.')
				last_request_chat_id = None
		else:
				bot.reply_to(message, f'Chat ID {last_request_chat_id} уже существует.')

@bot.message_handler(commands=['ignore'])
def ignore_request(message):
		global last_request_chat_id
		if str(message.from_user.id) not in trusted_users or last_request_chat_id is None:
				bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
				return

		bot.reply_to(message, f'Запрос от {last_request_chat_id} игнорируется.')
		bot.send_message(last_request_chat_id, 'Ваш запрос на добавление был отклонен.')
		last_request_chat_id = None
#id 
@bot.message_handler(commands=['id'])
def get_my_id(message):
		bot.reply_to(message, f'Ваш chat_id: {message.chat.id}')
#del
@bot.message_handler(commands=['del'])
def remove_chat_id(message):
		if str(message.from_user.id) not in trusted_users:
				bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
				return

		chat_id_to_remove = message.text.split()[1]  # Получаем chat_id из текста сообщения
		if chat_id_to_remove in CHAT_ID:
				CHAT_ID.remove(chat_id_to_remove)
				bot.reply_to(message, f'Chat ID {chat_id_to_remove} успешно удален.')
		else:
				bot.reply_to(message, f'Chat ID {chat_id_to_remove} не найден.')
#list 
@bot.message_handler(commands=['list'])
def get_chat_ids(message):
    if str(message.from_user.id) not in trusted_users:
        bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
        return

    # Create an inline keyboard
    markup = types.InlineKeyboardMarkup()

    # Add a button for each chat ID, allowing the administrator to choose which one to remove
    for chat_id in CHAT_ID:
        button = types.InlineKeyboardButton(f"Удалить {chat_id}", callback_data=f"delete_{chat_id}")
        markup.add(button)

    bot.reply_to(message, 'Выберите chat_id для удаления:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def delete_chat_id(call):
    chat_id_to_delete = call.data.split('_')[1]  # Extract the chat ID to be deleted from the callback data
    if chat_id_to_delete in CHAT_ID:
        CHAT_ID.remove(chat_id_to_delete)
        bot.answer_callback_query(call.id, f'Chat ID {chat_id_to_delete} успешно удален.')
    else:
        bot.answer_callback_query(call.id, f'Chat ID {chat_id_to_delete} не найден.')

    # Optionally, update the user interface with the modified list
    # You can send an updated list or perform any other necessary action
#add
@bot.message_handler(commands=['add'])
def add_chat_id(message):
		if str(message.from_user.id) not in trusted_users:
				bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
				return

		words = message.text.split()
		if len(words) < 2:
				bot.reply_to(message, 'Вы не указали chat_id.')
				return

		new_chat_id = words[1]  # Получаем chat_id из текста сообщения
		if new_chat_id not in CHAT_ID:
				CHAT_ID.append(new_chat_id)
				bot.reply_to(message, f'Chat ID {new_chat_id} успешно добавлен.')
		else:
				bot.reply_to(message, f'Chat ID {new_chat_id} уже существует.')

#kick
@bot.message_handler(commands=['kick'])
def kick_from_voice_channel(message):
		if str(message.from_user.id) not in trusted_users:
				bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
				return

		# Создаем кнопки для каждого сервера
		markup = types.InlineKeyboardMarkup()
		for guild in client.guilds:
				markup.add(types.InlineKeyboardButton(guild.name, callback_data=f'kick_guild_{guild.id}'))

		bot.send_message(message.chat.id, "Выберите сервер:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
		if call.data.startswith('kick_guild_'):
				_, guild_id, *_ = call.data.split('_')

				# Создаем кнопки для каждого голосового канала на сервере
				markup = types.InlineKeyboardMarkup()
				guild = client.get_guild(int(guild_id))
				for channel in guild.voice_channels:
						markup.add(types.InlineKeyboardButton(channel.name, callback_data=f'kick_channel_{guild_id}_{channel.id}'))

				bot.edit_message_text("Выберите голосовой канал:", call.message.chat.id, call.message.message_id, reply_markup=markup)

		elif call.data.startswith('kick_channel_'):
				_, guild_id, channel_id, *_ = call.data.split('_')

				# Создаем кнопки для каждого пользователя в голосовом канале
				markup = types.InlineKeyboardMarkup()
				channel = client.get_channel(int(channel_id))
				for member in channel.members:
						markup.add(types.InlineKeyboardButton(member.name, callback_data=f'kick_member_{guild_id}_{channel_id}_{member.id}'))

				bot.edit_message_text("Выберите пользователя:", call.message.chat.id, call.message.message_id, reply_markup=markup)

		elif call.data.startswith('kick_member_'):
				_, guild_id, channel_id, user_id, *_ = call.data.split('_')

				# Находим пользователя и голосовой канал
				user = client.get_user(int(user_id))
				channel = client.get_channel(int(channel_id))

				if user and channel and isinstance(channel, discord.VoiceChannel):
						# Если пользователь находится в голосовом канале, кикаем его
						if user in channel.members:
								asyncio.run_coroutine_threadsafe(user.move_to(None), client.loop)
								bot.answer_callback_query(call.id, f'Пользователь {user_id} был кикнут из голосового канала {channel_id}.')
						else:
								bot.answer_callback_query(call.id, f'Пользователь {user_id} не находится в голосовом канале {channel_id}.')
				else:
						bot.answer_callback_query(call.id, 'Не удалось найти пользователя или голосовой канал.')
#log 

@bot.message_handler(commands=['log'])
def send_file(message):
		chat_id = str(message.chat.id)
		if chat_id not in CHAT_ID:
				bot.send_message(chat_id, 'Ваш chat_id не добавлен в список. Используйте команду /requestadd, чтобы запросить доступ.')
				return

		file_path = 'log.txt'
		if os.path.getsize(file_path) <= 4096:  # 4 KB = 4096 bytes
				bot.send_message(chat_id, "Лог еще пустой.")
		else:
				with open(file_path, 'rb') as file:
						bot.send_document(chat_id, file)
## Обновленное событие для логирования входа в голосовой канал
@client.event
async def on_voice_state_update(member, before, after):
		if before.channel != after.channel:  # Check if the voice channel has changed
				if after.channel:  # If the member entered a voice channel
						if after.channel.guild:  # Ensure that the voice channel belongs to a guild
								log_message(f'{after.channel.guild} - {member} вошел в голосовой канал {after.channel}.')
				elif before.channel:  # If the member left the voice channel
						if before.channel.guild:  # Ensure that the voice channel belonged to a guild
								log_message(f'{before.channel.guild} - {member} вышел из голосового канала {before.channel}.')



@client.event
async def on_message(message):
		# Логируем все сообщения в текстовый файл
		log_message(f'{message.guild} #{message.channel} - {message.author}: {message.content}')

@client.event
async def on_member_update(before, after):
		# Логируем изменения статуса участников
		log_message(f'{after.guild} - {after.name} - изменил статус: {before.status} -> {after.status}')

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
	moscow_tz = pytz.timezone('Europe/Moscow')  # Устанавливаем часовой пояс Москвы
	moscow_time = datetime.now(moscow_tz)  # Получаем текущее время в Московском часовом поясе
	timestamp = moscow_time.strftime("%Y-%m-%d %H:%M:%S")
	log_entry = f'[{timestamp}] {text}\n'
	with open(log_path, 'a', encoding='utf-8') as log_file:
			log_file.write(log_entry)


def start_polling():
	bot.polling()

polling_thread = threading.Thread(target=start_polling)
polling_thread.start()

client.run(token)
