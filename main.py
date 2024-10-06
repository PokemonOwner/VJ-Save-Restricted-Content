import pyrogram
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import os
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
            await bot.edit_message_text(message.chat.id, message.id, f"__Downloading__ : **{txt}**")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Error updating download status: {e}")
            await asyncio.sleep(5)

async def upstatus(statusfile, message):
    await asyncio.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            await bot.edit_message_text(message.chat.id, message.id, f"__Uploading__ : **{txt}**")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Error updating upload status: {e}")
            await asyncio.sleep(5)

async def progress(current, total, message, type):
    percentage = current * 100 / total
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{percentage:.1f}%")
    print(f"{type.capitalize()} progress: {percentage:.1f}%")  # Log progress

@bot.on_message(filters.command(["start"]))
async def send_start(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    await bot.send_message(
        message.chat.id,
        f"**__👋 Hi** **{message.from_user.mention}**, **I am Save Restricted Bot, I can send you restricted content by its post link__**\n\n{USAGE}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Update Channel", url="https://t.me/VJ_Botz")]]), 
        reply_to_message_id=message.id
    )

@bot.on_message(filters.text)
async def save(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    print(f"Received message: {message.text}")

    if "https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text:
        if acc is None:
            await bot.send_message(message.chat.id, "**String Session is not Set**", reply_to_message_id=message.id)
            return
        try:
            await acc.join_chat(message.text)
            await bot.send_message(message.chat.id, "**Chat Joined**", reply_to_message_id=message.id)
        except UserAlreadyParticipant:
            await bot.send_message(message.chat.id, "**Chat already Joined**", reply_to_message_id=message.id)
        except InviteHashExpired:
            await bot.send_message(message.chat.id, "**Invalid Link**", reply_to_message_id=message.id)
        except Exception as e:
            await bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)
            return

    elif "https://t.me/" in message.text:
        datas = message.text.split("/")
        temp = datas[-1].replace("?single", "").split("-")
        fromID = int(temp[0].strip())
        toID = int(temp[1].strip()) if len(temp) > 1 else fromID

        for msgid in range(fromID, toID + 1):
            if "https://t.me/c/" in message.text:
                chatid = int("-100" + datas[4])
                if acc is None:
                    await bot.send_message(message.chat.id, "**String Session is not Set**", reply_to_message_id=message.id)
                    return
                await handle_private(message, chatid, msgid)

            elif "https://t.me/b/" in message.text:
                username = datas[4]
                if acc is None:
                    await bot.send_message(message.chat.id, "**String Session is not Set**", reply_to_message_id=message.id)
                    return
                await handle_private(message, username, msgid)

            else:
                username = datas[3]
                try:
                    msg = await bot.get_messages(username, msgid)
                    await bot.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
                except UsernameNotOccupied:
                    await bot.send_message(message.chat.id, "**The username is not occupied by anyone**", reply_to_message_id=message.id)
                    return
                except Exception as e:
                    await bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)

            await asyncio.sleep(3)  # Rate limiting

async def handle_private(message: pyrogram.types.messages_and_media.message.Message, chatid: int, msgid: int):
    try:
        msg = await acc.get_messages(chatid, msgid)
    except Exception as e:
        await bot.send_message(message.chat.id, f"**Error retrieving message**: {e}", reply_to_message_id=message.id)
        return

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

def get_message_type(msg):
    # Your logic for determining message type
    try:
        if msg.document:
            return "Document"
        elif msg.video:
            return "Video"
        elif msg.animation:
            return "Animation"
        elif msg.sticker:
            return "Sticker"
        elif msg.voice:
            return "Voice"
        elif msg.audio:
            return "Audio"
        elif msg.photo:
            return "Photo"
        elif msg.text:
            return "Text"
    except Exception as e:
        print(f"Error determining message type: {e}")
    return "Unknown"

USAGE = """..."""

bot.run()
