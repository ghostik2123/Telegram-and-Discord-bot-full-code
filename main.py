from keep_alive import keep_alive
keep_alive()
#import
import os
import threading
import telebot
from telebot import types
from datetime import datetime
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.all()
client = commands.Bot(command_prefix='/', intents=intents)
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

		chat_ids = ', '.join(CHAT_ID)
		bot.reply_to(message, f'Chat IDs: {chat_ids}')
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
def send_log(message):
		markup = types.InlineKeyboardMarkup()
		markup.add(
				types.InlineKeyboardButton("Сервер 1", callback_data='server1'),
				types.InlineKeyboardButton("Сервер 2", callback_data='server2'),
				# Добавьте больше кнопок, если нужно
		)
		bot.send_message(message.chat.id, "Выберите сервер:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
		server_name = ''
		if call.data == 'server1':
				server_name = 'ITACHI TEST'
				bot.answer_callback_query(call.id, 'Отправка логов с сервера 1...')
		elif call.data == 'server2':
				server_name = 'ANOTHER SERVER'
				bot.answer_callback_query(call.id, 'Отправка логов с сервера 2...')
		# Добавьте больше условий, если нужно

		with open('log.txt', 'r') as file:
				lines = file.readlines()

		# Фильтруем строки по имени сервера
		server_lines = [line for line in lines if line.startswith(f'[{server_name}]')]

		# Создаем новый файл с отфильтрованными строками
		with open('filtered_log.txt', 'w') as file:
				file.writelines(server_lines)

		# Отправляем новый файл
		with open('filtered_log.txt', 'rb') as file:
				bot.send_document(call.message.chat.id, file)


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
def start_polling():
	bot.polling()

polling_thread = threading.Thread(target=start_polling)
polling_thread.start()

client.run(token)
