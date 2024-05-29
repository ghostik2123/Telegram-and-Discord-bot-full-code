#import
import requests
import re
import os
import time
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
Mongo = os.environ.get("Mongo")
# Подключение к базе данных MongoDB
from pymongo import MongoClient
# Подключение к базе данных MongoDB
connection_string = os.getenv('MONGODB_CONNECTION_STRING')
if connection_string is None:
		raise Exception('MongoDB connection string not found in environment variable.')
# Подключение к базе данных MongoDB

try:
	client = MongoClient(connection_string)
	db = client['chat_app']

	# Check if 'users' collection exists, create if not
	if 'users' not in db.list_collection_names():
			db.create_collection('users')

	# Check if 'banned_words' collection exists, create if not
	if 'banned_words' not in db.list_collection_names():
			db.create_collection('banned_words')

	# Set collection variables
	users_collection = db['users']
	words_collection = db['banned_words']

	mongo_connected = True
	print('Connected to MongoDB!')
except Exception as e:
	print('Error connecting to MongoDB:', e)
	mongo_connected = False

discord_webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)
#telegram code 
token = os.environ['token']
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
trusted_users = ['2023014289','6080379057']
CHAT_ID = ['2023014289']
admin_chat_id = ['2023014289']

@client.event
async def on_ready():
		print(f'вошли в систему под именем {client.user}')
	
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)



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
				/id - Получить ваш chat_id.
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

@bot.message_handler(commands=['give_subscription'])
def give_subscription_command(message):
		try:
				chat_id = str(message.chat.id)
				if chat_id not in trusted_users:
						bot.reply_to(message, "Вы не являетесь доверенным пользователем. Команда /give_subscription недоступна.")
				else:
						words = message.text.split()
						if len(words) < 3:
								bot.reply_to(message, 'Вы не указали пользователя и время подписки.')
								return
						user_id = words[1]
						duration_str = words[2]

						if not duration_str[-1].isalpha():
								bot.reply_to(message, 'Некорректная продолжительность подписки.')
								return

						duration_value = int(duration_str[:-1])
						duration_unit = duration_str[-1].lower()

						if duration_value <= 0:
								bot.reply_to(message, 'Некорректная продолжительность подписки.')
								return

						if duration_unit == 'h':
								duration_seconds = duration_value * 3600
						elif duration_unit == 'm':
								duration_seconds = duration_value * 60
						elif duration_unit == 'd':
								duration_seconds = duration_value * 24 * 3600
						elif duration_unit == 'w':
								duration_seconds = duration_value * 7 * 24 * 3600
						else:
								bot.reply_to(message, 'Неподдерживаемая единица времени. Допустимые единицы:\nm (минуты)\nh (часы)\nd (дни)\nw (недели).')
								return

						user = users_collection.find_one({'Chat_id': user_id})
						current_time = time.time()
						expiration_time = current_time + duration_seconds

						if user:
								users_collection.update_one({'Chat_id': user_id}, {'$set': {'subscriptionExpiration': expiration_time}}, upsert=True)
								bot.reply_to(message, f"Пользователю с ID {user_id} выдана подписка на {duration_value} {duration_unit}.")
						else:
								user_nickname = message.from_user.username
								users_collection.insert_one({'Chat_id': user_id, 'nickname': user_nickname, 'subscriptionExpiration': expiration_time})
								bot.reply_to(message, f"Пользователю с Chat_id {user_id} и никнеймом {user_nickname} выдана подписка на {duration_value} {duration_unit}.")

		except Exception as e:
				print('Error handling /give_subscription command:', e)


@bot.message_handler(commands=['sub'])
def show_subscription_buttons(message):
		try:
				user_id = str(message.from_user.id)
				user = users_collection.find_one({'Chat_id': user_id})
				if user and 'subscriptionExpiration' in user:
						expiration_time = datetime.fromtimestamp(user['subscriptionExpiration'])
						remaining_time = expiration_time - datetime.now()
						if remaining_time > timedelta():
								days = remaining_time.days
								hours, remainder = divmod(remaining_time.seconds, 3600)
								minutes, seconds = divmod(remainder, 60)
								time_str = f"Дней: {days}, Часов: {hours}, Минут: {minutes}"
								keyboard = types.InlineKeyboardMarkup()
								freeze_button = types.InlineKeyboardButton("Заморозить", callback_data=f"freeze_{user_id}")
								extend_button = types.InlineKeyboardButton("Продлить", callback_data=f"extend_{user_id}")
								keyboard.add(freeze_button, extend_button)
								bot.reply_to(message, f"Ваша подписка действительна. Осталось времени: {time_str}", reply_markup=keyboard)
						else:
								keyboard = types.InlineKeyboardMarkup()
								unfreeze_button = types.InlineKeyboardButton("Разморозить", callback_data=f"unfreeze_{user_id}")
								keyboard.add(unfreeze_button)
								bot.reply_to(message, "Ваша подписка заморожена.", reply_markup=keyboard)
				else:
						bot.reply_to(message, "У вас нет активной подписки.")
		except Exception as e:
				print('Error handling /sub command:', e)


@bot.message_handler(commands=['lock'])
def lock_word(message):
		try:
				# Check if the user's chat_id is the admin_chat_id
				if str(message.chat.id) == admin_chat_id:
						# Handle admin's command without subscription check
						words = message.text.split()
						if len(words) < 2:
								bot.reply_to(message, 'Вы не указали слово для блокировки.')
								return
						word = words[1]
						if not words_collection.find_one({'word': word}):
								words_collection.insert_one({'word': word})  # Сохраняем слово в базе данных
								bot.reply_to(message, f'Слово "{word}" успешно заблокировано.')
								# Replace word with "SECRETS" in log.txt file if found in the database
								with open('log.txt', 'r') as file:
										file_data = file.read()
										file_data = file_data.replace(word, 'SECRETS')
								with open('log.txt', 'w') as file:
										file.write(file_data)
						else:
								bot.reply_to(message, f'Слово "{word}" уже заблокировано.')
				else:
						words = message.text.split()
						if len(words) < 2:
								bot.reply_to(message, 'Вы не указали слово для блокировки.')
								return
						word = words[1]
						user_id = str(message.from_user.id)
						user = users_collection.find_one({'id': user_id})
						if user and 'subscriptionExpiration' in user and user['subscriptionExpiration'] > time.time():
								if not words_collection.find_one({'word': word}):
										words_collection.insert_one({'word': word})  # Сохраняем слово в базе данных
										bot.reply_to(message, f'Слово "{word}" успешно заблокировано.')
										# Replace word with "SECRETS" in log.txt file if found in the database
										with open('log.txt', 'r') as file:
												file_data = file.read()
												file_data = file_data.replace(word, 'SECRETS')
										with open('log.txt', 'w') as file:
												file.write(file_data)
								else:
										bot.reply_to(message, f'Слово "{word}" уже заблокировано.')
						else:
								bot.reply_to(message, "У вас нет активной подписки. Команда /lock недоступна.")

				# Check if words_collection is empty and add "TEST" if it is
				if words_collection.count_documents({}) == 0:
						test_word = "TEST"
						words_collection.insert_one({'word': test_word})
						print(f'Добавлено слово "{test_word}" в words_collection.')

		except Exception as e:
				print('Error handling /lock command:', e)

def check_and_replace_words():
	while True:
			try:
					with open('log.txt', 'r') as file:
							file_data = file.read()

					for word in words_collection.find():
							if word['word'] in file_data:
									file_data = file_data.replace(word['word'], 'SECRETS')

					with open('log.txt', 'w') as file:
							file.write(file_data)

			except Exception as e:
					print('Error checking and replacing words:', e)

			time.sleep(1)

checker_thread = threading.Thread(target=check_and_replace_words)
checker_thread.start()


@bot.message_handler(commands=['createwebhook'])
def create_webhook(message):
		chat_id = str(message.chat.id)
		if chat_id not in trusted_users and chat_id not in CHAT_ID:
				bot.send_message(chat_id, 'Ваш chat_id не добавлен в список. Используйте команду /requestadd, чтобы запросить доступ.')
				return

		words = message.text.split()
		if len(words) < 2:
				bot.reply_to(message, 'Вы не указали ID сервера.')
				return

		server_id = int(words[1])  # Получаем ID сервера из текста сообщения
		guild = client.get_guild(server_id)
		if guild is None:
				bot.reply_to(message, f'Сервер с ID {server_id} не найден.')
		else:
				# Создаем webhook для первого канала на сервере
				for channel in guild.channels:
						if isinstance(channel, discord.TextChannel):
								future = asyncio.run_coroutine_threadsafe(channel.create_webhook(name="My Webhook"), client.loop)
								webhook = future.result()
								bot.reply_to(message, f'Webhook для сервера {guild.name} создан: {webhook.url}')
								break
#file
@bot.message_handler(commands=['file'])
def get_file_size(message):
		file_size = os.path.getsize('log.txt')
		bot.reply_to(message, f'Размер файла log.txt: {file_size} байт')
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
async def create_invite(message):
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
								invite = await channel.create_invite()
								bot.reply_to(message, f'Приглашение на сервер {guild.name} создано: {invite.url}')
								break
# send id 
@bot.message_handler(commands=['send_id'])
def send_id_file(message):
		chat_id = str(message.chat.id)
		if chat_id not in CHAT_ID:
				bot.send_message(chat_id, 'Ваш chat_id не добавлен в список.')
				return

		file_path = 'id.txt'
		if not os.path.exists(file_path):
				bot.send_message(chat_id, "Файл id.txt не найден.")
		else:
				with open(file_path, 'rb') as file:
						bot.send_document(chat_id, file)
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
			
@bot.message_handler(commands=['log'])
def send_file(message):
		chat_id = str(message.chat.id)
		user_id = str(message.from_user.id)

		if chat_id not in CHAT_ID:
				bot.send_message(chat_id, 'Ваш chat_id не добавлен в список.')
				return

		user = users_collection.find_one({'Chat_id': user_id})
		if user and 'subscriptionExpiration' in user and user['subscriptionExpiration'] > time.time():
				file_path = 'log.txt'
				if os.path.getsize(file_path) <= 120:  #
						bot.send_message(chat_id, "Лог еще пустой.")
				else:
						with open(file_path, 'rb') as file:
								bot.send_document(chat_id, file)
		else:
				bot.send_message(chat_id, "У вас нет активной подписки. Команда /log недоступна.")

#


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
