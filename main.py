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
            await bot.edit_message_text(message.chat.id, message.id, f"Downloaded : {txt}")
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
            await bot.edit_message_text(message.chat.id, message.id, f"Uploaded : {txt}")
            await asyncio.sleep(10)
        except Exception as e:
            print(f"Error updating upload status: {e}")
            await asyncio.sleep(5)

def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")

@bot.on_message(filters.command(["start"]))
async def send_start(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    await bot.send_message(message.chat.id, f"👋 Hi {message.from_user.mention}, I am Save Restricted Bot, I can send you restricted content by its post link\n\n{USAGE}",
                           reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Update Channel", url="https://t.me/VJ_Botz")]]), 
                           reply_to_message_id=message.id)

@bot.on_message(filters.text)
async def save(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    print(message.text)

    if "https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text:
        if acc is None:
            await bot.send_message(message.chat.id, "String Session is not Set", reply_to_message_id=message.id)
            return

        try:
            await acc.join_chat(message.text)
            await bot.send_message(message.chat.id, "Chat Joined", reply_to_message_id=message.id)
        except UserAlreadyParticipant:
            await bot.send_message(message.chat.id, "Chat already Joined", reply_to_message_id=message.id)
        except InviteHashExpired:
            await bot.send_message(message.chat.id, "Invalid Link", reply_to_message_id=message.id)
        except Exception as e:
            await bot.send_message(message.chat.id, f"Error : {e}", reply_to_message_id=message.id)

    elif "https://t.me/" in message.text:
        datas = message.text.split("/")
        temp = datas[-1].replace("?single", "").split("-")
        fromID = int(temp[0].strip())
        toID = int(temp[1].strip()) if len(temp) > 1 else fromID

        for msgid in range(fromID, toID + 1):
            if "https://t.me/c/" in message.text:
                chatid = int("-100" + datas[4])
                if acc is None:
                    await bot.send_message(message.chat.id, "String Session is not Set", reply_to_message_id=message.id)
                    return
                await handle_private(message, chatid, msgid)

            elif "https://t.me/b/" in message.text:
                username = datas[4]
                if acc is None:
                    await bot.send_message(message.chat.id, "String Session is not Set", reply_to_message_id=message.id)
                    return
                await handle_private(message, username, msgid)

            else:
                username = datas[3]
                try:
                    msg = await bot.get_messages(username, msgid)
                    await bot.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
                except UsernameNotOccupied:
                    await bot.send_message(message.chat.id, "The username is not occupied by anyone", reply_to_message_id=message.id)
                    return
                except Exception as e:
                    await bot.send_message(message.chat.id, f"Error : {e}", reply_to_message_id=message.id)

            await asyncio.sleep(3)  # Rate limiting

async def handle_private(message: pyrogram.types.messages_and_media.message.Message, chatid: int, msgid: int):
    try:
        msg = await acc.get_messages(chatid, msgid)
    except Exception as e:
        await bot.send_message(message.chat.id, f"Error retrieving message: {e}", reply_to_message_id=message.id)
        return

    msg_type = get_message_type(msg)
    
    if msg_type == "Text":
        await bot.send_message(message.chat.id, msg.text, entities=msg.entities, reply_to_message_id=message.id)
        return

    smsg = await bot.send_message(message.chat.id, 'Downloading', reply_to_message_id=message.id)
    
    # Start download status
    asyncio.create_task(downstatus(f'{message.id}downstatus.txt', smsg))
    file = await acc.download_media(msg, progress=progress, progress_args=[message, "down"])
    os.remove(f'{message.id}downstatus.txt')

    # Start upload status
    asyncio.create_task(upstatus(f'{message.id}upstatus.txt', smsg))

    if msg_type == "Document":
        thumb = await acc.download_media(msg.document.thumbs[0].file_id) if msg.document.thumbs else None
        await bot.send_document(message.chat.id, file, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])
        if thumb is not None:
            os.remove(thumb)

    elif msg_type == "Video":
        thumb = await acc.download_media(msg.video.thumbs[0].file_id) if msg.video.thumbs else None
        await bot.send_video(message.chat.id, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])
        if thumb is not None:
            os.remove(thumb)

    # Handle other message types similarly...

    os.remove(file)
    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
    await bot.delete_messages(message.chat.id, [smsg.id])

def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
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

USAGE = """FOR PUBLIC CHATS
just send post/s link

FOR PRIVATE CHATS
**__first send invite link of the chat (unnecessary if the account of string session already member of the chat)
then send post/s link__**

FOR BOT CHATS
send link with '/b/', bot's username and message id, you might want to install some unofficial client to get the id like below

https://t.me/b/botusername/4321

MULTI POSTS
send public/private posts link as explained above with format "from - to" to send multiple messages like below

https://t.me/xxxx/1001-1010

Make Functionality back to this Code just make Asyncio error fix
"""

# Start the bot
bot.run()
