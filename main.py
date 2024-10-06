import pyrogram
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import os
import json
from os import environ

bot_token = environ.get("TOKEN", "") 
api_hash = environ.get("HASH", "") 
api_id = int(environ.get("ID", ""))
bot = Client("mybot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

ss = environ.get("STRING", "")
if ss is not None:
    acc = Client("myacc", api_id=api_id, api_hash=api_hash, session_string=ss)
    acc.start()
else:
    acc = None

async def downstatus(statusfile, message):
    await asyncio.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()
        try:
            await bot.edit_message_text(message.chat.id, message.id, f"__Downloaded__ : **{txt}**")
            await asyncio.sleep(10)
        except Exception as e:
            print(e)
            await asyncio.sleep(5)

async def upstatus(statusfile, message):
    await asyncio.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            await bot.edit_message_text(message.chat.id, message.id, f"__Uploaded__ : **{txt}**")
            await asyncio.sleep(10)
        except Exception as e:
            print(e)
            await asyncio.sleep(5)

async def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")

@bot.on_message(filters.command(["start"]))
async def send_start(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    await bot.send_message(message.chat.id, f"**__👋 Hi** **{message.from_user.mention}**, **I am Save Restricted Bot, I can send you restricted content by its post link__**\n\n{USAGE}",
                           reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Update Channel", url="https://t.me/VJ_Botz")]]), 
                           reply_to_message_id=message.id)

@bot.on_message(filters.text)
async def save(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    print(message.text)
    # Joining chats logic remains unchanged
    # ...

async def handle_private(message: pyrogram.types.messages_and_media.message.Message, chatid: int, msgid: int):
    msg = await acc.get_messages(chatid, msgid)
    msg_type = get_message_type(msg)

    smsg = await bot.send_message(message.chat.id, '__Downloading__', reply_to_message_id=message.id)

    # Start download status
    asyncio.create_task(downstatus(f'{message.id}downstatus.txt', smsg))
    file = await acc.download_media(msg, progress=progress, progress_args=[message, "down"])
    
    if os.path.exists(f'{message.id}downstatus.txt'):
        os.remove(f'{message.id}downstatus.txt')

    # Start upload status
    asyncio.create_task(upstatus(f'{message.id}upstatus.txt', smsg))
    
    if msg_type == "Document":
        thumb = await acc.download_media(msg.document.thumbs[0].file_id) if msg.document.thumbs else None
        await bot.send_document(message.chat.id, file, thumb=thumb, caption=msg.caption, reply_to_message_id=message.id, 
                                progress=progress, progress_args=[message, "up"])
    # Handle other message types similarly...

    os.remove(file)
    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
    await bot.delete_messages(message.chat.id, [smsg.id])

# The rest of your functions remain mostly unchanged
# Ensure all calls to async functions are awaited
USAGE = """..."""

bot.run()
