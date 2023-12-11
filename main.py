from keep_alive import keep_alive
keep_alive()
#import
import logging
import json
import requests
import re
import os
import threading
#telgram
import telebot
from telebot import types
from datetime import datetime , timedelta
import pytz
#discord
import discord
from discord import Permissions
from discord.utils import oauth_url
from discord.ext import commands
import asyncio
#crypt
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad

user_chat_ids = {}
banned_channels = ['1143915567548485766', '1144234201063895110', '1144234201063895110']

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)
#telegram code 
token = os.environ['token']
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
trusted_users = ['2023014289']
CHAT_ID = ['2023014289']
crypto_key = os.environ['crypto_key']
@client.event
async def on_ready():
		print(f'вошли в систему под именем {client.user}')
	
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@client.event
async def on_message(message):
		if str(message.channel.id) in banned_channels:
				return
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
				Вас нет в списке chat_id
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
#
@bot.message_handler(commands=['serverinfo'])
def get_server_info(message):
		words = message.text.split()
		if len(words) < 2:
				bot.reply_to(message, 'Вы не указали ID сервера.')
				return

		server_id = int(words[1])  # Получаем ID сервера из текста сообщения
		guild = client.get_guild(server_id)
		if guild is None:
				bot.reply_to(message, f'Сервер с ID {server_id} не найден.')
		else:
				# Создаем файл channels.txt и записываем в него информацию о каналах
				with open('channels.txt', 'w') as file:
						file.write(f"Текстовые каналы на сервере {guild.name}:\n")
						for channel in guild.text_channels:
								file.write(f"{channel.name} (ID: {channel.id})\n")
						file.write("\nГолосовые каналы на сервере:\n")
						for channel in guild.voice_channels:
								file.write(f"{channel.name} (ID: {channel.id})\n")

				# Отправляем файл
				with open('channels.txt', 'rb') as file:
						bot.send_document(message.chat.id, file)

				# Удаляем файл
				os.remove('channels.txt')

#
@bot.message_handler(commands=['createinvite'])
def create_invite(message):
		words = message.text.split()
		if len(words) < 2:
				bot.reply_to(message, 'Вы не указали ID сервера.')
				return

		server_id = int(words[1])  # Получаем ID сервера из текста сообщения
		guild = client.get_guild(server_id)
		if guild is None:
				bot.reply_to(message, f'Сервер с ID {server_id} не найден.')
		else:
				# Создаем приглашение для первого канала на сервере
				for channel in guild.channels:
						if isinstance(channel, discord.TextChannel):
								invite = asyncio.run_coroutine_threadsafe(channel.create_invite(), client.loop).result()
								bot.reply_to(message, f'Приглашение на сервер {guild.name} создано: {invite.url}')
								break
#ban
@bot.message_handler(commands=['ban'])
def ban_user(message):
		args = message.text.split()
		if len(args) < 4:
				bot.reply_to(message, "Недостаточно аргументов.")
		else:
				server_id = args[1]
				member_id = args[2]
				reason = ' '.join(args[3:])
				# Здесь вы можете вызвать функцию или метод, которая связывает вашего бота Telegram с ботом Discord
				# ban_in_discord(server_id, member_id, reason)

# send id 
@bot.message_handler(commands=['send_id'])
def send_id_file_as_code(message):
		chat_id = str(message.chat.id)
		if chat_id not in CHAT_ID:
				bot.send_message(chat_id, 'Ваш chat_id не добавлен в список. Используйте команду /requestadd, чтобы запросить доступ.')
				return

		file_path = 'id.txt'
		if not os.path.exists(file_path):
				bot.send_message(chat_id, "Файл id.txt не найден.")
		else:
				with open(file_path, 'r', encoding='utf-8') as file:  # Открываем файл в текстовом режиме
						file_content = "```\n" + file.read() + "\n```"  # Заключаем содержимое файла в блок кода
						bot.send_message(chat_id, file_content, parse_mode='Markdown')  # Отправляем содержимое файла как блок кода
# create 
@bot.message_handler(commands=['create'])
def create_channel(message):
		words = message.text.split()
		if len(words) < 3:
				bot.reply_to(message, 'Вы не указали ID сервера или имя канала.')
				return

		server_id = int(words[1])  # Получаем ID сервера из текста сообщения
		channel_name = words[2]  # Получаем имя канала из текста сообщения
		guild = client.get_guild(server_id)
		if guild is None:
				bot.reply_to(message, f'Сервер с ID {server_id} не найден.')
		else:
				asyncio.run_coroutine_threadsafe(guild.create_text_channel(channel_name), client.loop)
				bot.reply_to(message, f'Канал {channel_name} успешно создан на сервере {guild.name}.')

@bot.message_handler(commands=['remove'])
def delete_channel(message):
		words = message.text.split()
		if len(words) < 3:
				bot.reply_to(message, 'Вы не указали ID сервера или ID канала.')
				return

		server_id = int(words[1])  # Получаем ID сервера из текста сообщения
		channel_id = int(words[2])  # Получаем ID канала из текста сообщения
		guild = client.get_guild(server_id)
		if guild is None:
				bot.reply_to(message, f'Сервер с ID {server_id} не найден.')
		else:
				channel = guild.get_channel(channel_id)
				if channel is None:
						bot.reply_to(message, f'Канал с ID {channel_id} не найден на сервере {guild.name}.')
				else:
						asyncio.run_coroutine_threadsafe(channel.delete(), client.loop)
						bot.reply_to(message, f'Канал {channel.name} успешно удален с сервера {guild.name}.')


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
				chat = bot.get_chat(chat_id)
				username = chat.username if chat.username else "No username"
				button = types.InlineKeyboardButton(f"Удалить {username} ({chat_id})", callback_data=f"delete_{chat_id}")
				markup.add(button)

		bot.reply_to(message, 'Выберите chat_id для удаления:', reply_markup=markup)
@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def delete_chat_id(call):
		chat_id_to_delete = call.data.split('_')[1]  # Extract the chat ID from the callback data

		if chat_id_to_delete in CHAT_ID:
				CHAT_ID.remove(chat_id_to_delete)
				bot.answer_callback_query(call.id, f'Chat ID {chat_id_to_delete} был удален.')

				# Create a new inline keyboard with the updated list of chat IDs
				markup = types.InlineKeyboardMarkup()
				for chat_id in CHAT_ID:
						chat = bot.get_chat(chat_id)
						username = chat.username if chat.username else "No username"
						button = types.InlineKeyboardButton(f"Удалить {username} ({chat_id})", callback_data=f"delete_{chat_id}")
						markup.add(button)

				# Update the message's reply markup
				bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
		else:
				bot.answer_callback_query(call.id, f'Chat ID {chat_id_to_delete} не найден.')
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

#log 
@bot.message_handler(commands=['log'])
def send_file(message):
		chat_id = str(message.chat.id)
		if chat_id not in CHAT_ID:
				bot.send_message(chat_id, 'Ваш chat_id не добавлен в список. Используйте команду /requestadd, чтобы запросить доступ.')
				return

		file_path = 'log.txt'
		if os.path.getsize(file_path) <= 120:  #
				bot.send_message(chat_id, "Лог еще пустой.")
		else:
				with open(file_path, 'rb') as file:
						bot.send_document(chat_id, file)
#
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
