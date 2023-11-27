from keep_alive import keep_alive
keep_alive()
# import
import datetime
import os
from discord.ext import commands
from discord import Intents
import telebot
import asyncio


DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = '2023014289'

voice_sessions = {}

intents = Intents.default()
intents.message_content = True  # Enable receiving message content

discord_bot = commands.Bot(command_prefix='!', intents=intents)
telegram_bot = telebot.TeleBot(TELEGRAM_TOKEN)


@discord_bot.event
async def on_ready():
		print('Bot is ready.')


# Events

@discord_bot.event
async def on_message(message):
		author_name = message.author.name  # Get the name of the message author
		server_name = message.guild.name  # Get the name of the server
		channel_name = message.channel.name  # Get the name of the channel

		# Format the text for sending to Telegram
		text = f'Ник: {author_name}\nСервер: {server_name}\nКанал: {channel_name}\nСообщение: {message.content}'

		# Send the message to Telegram with Markdown formatting
		telegram_bot.send_message(TELEGRAM_CHAT_ID, f'```\n{text}\n```', parse_mode='Markdown')

		# Check for attachments
		if message.attachments:
				attachments = "\nВложения:"
				for attachment in message.attachments:
						attachments += f"\n- {attachment.url}"
				text += attachments

		telegram_bot.send_message(TELEGRAM_CHAT_ID, text, parse_mode='Markdown')
		await discord_bot.process_commands(message)

# voice connect and disconnect
@discord_bot.event
async def on_voice_state_update(member, before, after):
		if before.channel is None and after.channel is not None:
				# Member joined a voice channel
				author_name = member.name
				server_name = member.guild.name
				channel_name = after.channel.name
				start_time = datetime.datetime.now()
				voice_sessions[member.id] = start_time
				text = f'Ник: {author_name}\nСервер: {server_name}\nКанал: {channel_name}\nПрисоединился к голосовому каналу в {start_time}'
				await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f'\n{text}\n', parse_mode='Markdown')
		elif before.channel is not None and after.channel is None:
				# Member left a voice channel
				start_time = voice_sessions.get(member.id)
				if start_time:
						end_time = datetime.datetime.now()
						duration = end_time - start_time
						del voice_sessions[member.id]
						duration_seconds = duration.total_seconds()
						duration_hours = int(duration_seconds // 3600)
						duration_minutes = int((duration_seconds % 3600) // 60)
						duration_seconds = duration_seconds % 60
						duration_formatted = f'{duration_hours}:{duration_minutes:02d}:{duration_seconds:.2f}'
						author_name = member.name
						server_name = member.guild.name
						channel_name = before.channel.name
						text = f'Ник: {author_name}\nСервер: {server_name}\nКанал: {channel_name}\nПокинул голосовой канал в {end_time}.\nПродолжительность: {duration_formatted}'
						await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f'```\n{text}\n```')

@discord_bot.event
async def on_message(message):
		if message.author.bot:
				# Ignore if the message is sent by a bot
				return

		author_name = message.author.name  # Get the name of the message author
		server_name = message.guild.name  # Get the name of the server
		channel_name = message.channel.name  # Get the name of the channel

		# Format the text for sending to Telegram
		text = f'Ник: {author_name}\nСервер: {server_name}\nКанал: {channel_name}\nСообщение: {message.content}'
		if message.attachments:
				attachments = "\nВложения:"
				for attachment in message.attachments:
						attachments += f"\n- {attachment.url}"
				text += attachments

		await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f'\n{text}\n', parse_mode='Markdown')
		await discord_bot.process_commands(message)

# Commands

@discord_bot.command()
async def servers(ctx):
		bot = ctx.bot
		guilds = bot.guilds
		for guild in guilds:
				members = guild.members
				member_names = [member.name for member in members]
				text = f"Сервер: {guild.name}\nУчастники: {', '.join(member_names)}"
				await ctx.send(f'\n{text}\n', parse_mode='Markdown')

discord_bot.run(DISCORD_TOKEN)
