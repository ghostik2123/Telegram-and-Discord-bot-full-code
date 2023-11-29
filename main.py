from keep_alive import keep_alive
keep_alive()
#import
import os
import telebot
from telebot import types
from datetime import datetime, timedelta
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.all()
client = commands.Bot(command_prefix='/', intents=intents)
#telegram code 
token = os.environ['token']
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
trusted_users = '2023014289'
CHAT_ID = ['2023014289']
banned_users = []
timeouts = {}


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


@bot.message_handler(commands=['help'])
def send_help(message):
		if str(message.from_user.id) in trusted_users:
				help_text = """
				Доступные команды:
				/log - Получить файл log.txt, если его размер больше 4KB и ваш chat_id добавлен в список.
				/add [chat_id] - Добавить новый chat_id в список.
				/list - Получить список всех chat_id.
				/del [chat_id] - Удалить chat_id из списка.
				/id - Получить ваш chat_id.
				/requestadd - Отправить запрос на добавление вашего chat_id в список.
				/ban [user_id] - Забанить пользователя.
				/unban [user_id] - Разбанить пользователя.
				/timeout [user_id] - Установить таймаут для пользователя.
				/banlist - Показать список забаненных пользователей.
				/timeoutlist - Показать список пользователей с таймаутом.
				"""
		else:
				help_text = """
				Доступные команды:
				/id - Получить ваш chat_id.
				/requestadd - Отправить запрос на добавление вашего chat_id в список.
				"""
		bot.reply_to(message, help_text)


@bot.message_handler(commands=['requestadd'])
def request_add(message):
				request_text = f'Пользователь {message.from_user.username} ({message.chat.id}) хочет добавить себя в список.'

				markup = types.InlineKeyboardMarkup()
				markup.add(
								types.InlineKeyboardButton("Разрешить", callback_data=f'add_{message.chat.id}'),
								types.InlineKeyboardButton("Игнорировать", callback_data=f'ignore_{message.chat.id}')
				)

				bot.send_message(trusted_users, request_text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
		action, user_id = call.data.split('_')
		if action == 'add':
				if user_id not in CHAT_ID:
						CHAT_ID.append(user_id)
						bot.answer_callback_query(call.id, f'Chat ID {user_id} успешно добавлен.')
						bot.send_message(user_id, 'Ваш запрос на добавление был одобрен.')
				else:
						bot.answer_callback_query(call.id, f'Chat ID {user_id} уже существует.')
		elif action == 'ignore':
				bot.answer_callback_query(call.id, f'Запрос от {user_id} игнорируется.')
				bot.send_message(user_id, 'Ваш запрос на добавление был отклонен.')

		# Удаляем сообщение с запросом после выбора действия
		bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.message_handler(commands=['banlist'])
def show_ban_list(message):
		if str(message.from_user.id) not in trusted_users:
				bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
				return

		if not banned_users:
				bot.reply_to(message, 'Список забаненных пользователей пуст.')
		else:
				ban_list = ', '.join(banned_users)
				bot.reply_to(message, f'Забаненные пользователи: {ban_list}')

@bot.message_handler(commands=['timeoutlist'])
def show_timeout_list(message):
		if str(message.from_user.id) not in trusted_users:
				bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
				return

		if not timeouts:
				bot.reply_to(message, 'Список пользователей с таймаутом пуст.')
		else:
				timeout_list = ', '.join(f'{user_id}: {end_time}' for user_id, end_time in timeouts.items())
				bot.reply_to(message, f'Пользователи с таймаутом: {timeout_list}')


@bot.message_handler(commands=['timeout'])
def timeout_user(message):
		if str(message.from_user.id) not in trusted_users:
				bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
				return

		user_id_to_timeout = message.text.split()[1]  # Получаем user_id из текста сообщения
		timeout_end = datetime.now() + timedelta(days=1)
		timeouts[user_id_to_timeout] = timeout_end
		bot.reply_to(message, f'User ID {user_id_to_timeout} теперь в таймауте до {timeout_end}.')

# Проверяем, находится ли пользователь в таймауте перед обработкой каждого сообщения
@bot.message_handler(func=lambda message: True)
def check_timeout(message):
		user_id = str(message.from_user.id)
		if user_id in timeouts:
				if datetime.now() < timeouts[user_id]:
						return  # Если пользователь в таймауте, просто игнорируем его сообщения
				else:
						del timeouts[user_id]

@bot.message_handler(commands=['ban'])
def ban_user(message):
		if str(message.from_user.id) not in trusted_users:
				bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
				return

		user_id_to_ban = message.text.split()[1]  # Получаем user_id из текста сообщения
		if user_id_to_ban not in banned_users:
				banned_users.append(user_id_to_ban)
				bot.reply_to(message, f'User ID {user_id_to_ban} успешно забанен.')
				bot.send_message(user_id_to_ban, 'Вы были забанены.')
		else:
				bot.reply_to(message, f'User ID {user_id_to_ban} уже забанен.')

# Проверяем, забанен ли пользователь перед обработкой каждого сообщения
@bot.message_handler(func=lambda message: True)
def check_ban(message):
		if str(message.from_user.id) in banned_users:
				return 

@bot.message_handler(commands=['id'])
def get_my_id(message):
		bot.reply_to(message, f'Ваш chat_id: {message.chat.id}')

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

@bot.message_handler(commands=['list'])
def get_chat_ids(message):
		if str(message.from_user.id) not in trusted_users:
				bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
				return

		chat_ids = ', '.join(CHAT_ID)
		bot.reply_to(message, f'Chat IDs: {chat_ids}')

@bot.message_handler(commands=['add'])
def add_chat_id(message):
		if str(message.from_user.id) not in trusted_users:
				bot.reply_to(message, 'У вас нет прав для выполнения этой команды.')
				return

		new_chat_id = message.text.split()[1]  # Получаем chat_id из текста сообщения
		if new_chat_id not in CHAT_ID:
				CHAT_ID.append(new_chat_id)
				bot.reply_to(message, f'Chat ID {new_chat_id} успешно добавлен.')
		else:
				bot.reply_to(message, f'Chat ID {new_chat_id} уже существует.')

@bot.message_handler(commands=['log'])
def send_file(message):
		chat_id = str(message.chat.id)
		if chat_id not in CHAT_ID:
				bot.send_message(chat_id, 'Ваш chat_id не добавлен в список. Используйте команду /requestadd, чтобы запросить доступ.')
				return

		file_path = 'log.txt'
		if os.path.getsize(file_path) < 4096:  # 4 KB = 4096 bytes
				bot.send_message(chat_id, "Лог еще пустой.")
		else:
				with open(file_path, 'rb') as file:
						bot.send_document(chat_id, file)

bot.polling()

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
