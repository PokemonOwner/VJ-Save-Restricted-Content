import pyrogram
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import time
import os
import threading
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

# download status
def downstatus(statusfile, message):
    while True:
        if os.path.exists(statusfile):
            break

        time.sleep(3)

    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()

        try:
            bot.edit_message_text(message.chat.id, message.message_id, f"__Downloaded__ : **{txt}**")
            time.sleep(10)
        except:
            time.sleep(5)

# upload status
def upstatus(statusfile, message):
    while True:
        if os.path.exists(statusfile):
            break

        time.sleep(3)

    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()

        try:
            bot.edit_message_text(message.chat.id, message.message_id, f"__Uploaded__ : **{txt}**")
            time.sleep(10)
        except:
            time.sleep(5)

# progress writer
def progress(current, total, message, type):
    with open(f'{message.message_id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")

# start command
@bot.on_message(filters.command(["start"]))
def send_start(client, message):
    bot.send_message(
        message.chat.id,
        f"**__👋 Hi** **{message.from_user.mention}**, **I am Save Restricted Bot, I can send you restricted content by its post link__**\n\n{USAGE}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Update Channel", url="https://t.me/VJ_Botz")]]),
        reply_to_message_id=message.message_id
    )

# handle private
def handle_private(message, chatid, msgid):
    try:
        if not acc.is_initialized:
            acc.start()

        msg = acc.get_messages(chatid, msgid)
        msg_type = get_message_type(msg)

        if "Text" == msg_type:
            bot.send_message(message.chat.id, msg.text, entities=msg.entities, reply_to_message_id=message.message_id)
            return

        smsg = bot.send_message(message.chat.id, '__Downloading__', reply_to_message_id=message.message_id)
        dosta = threading.Thread(target=lambda: downstatus(f'{message.message_id}downstatus.txt', smsg), daemon=True)
        dosta.start()
        file = acc.download_media(msg, progress=progress, progress_args=[message, "down"])
        os.remove(f'{message.message_id}downstatus.txt')

        upsta = threading.Thread(target=lambda: upstatus(f'{message.message_id}upstatus.txt', smsg), daemon=True)
        upsta.start()

        if "Document" == msg_type:
            try:
                thumb = acc.download_media(msg.document.thumbs[0].file_id)
            except:
                thumb = None

            bot.send_document(message.chat.id, file, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.message_id, progress=progress, progress_args=[message, "up"])
            if thumb:
                os.remove(thumb)

        elif "Video" == msg_type:
            try:
                thumb = acc.download_media(msg.video.thumbs[0].file_id)
            except:
                thumb = None

            bot.send_video(message.chat.id, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.message_id, progress=progress, progress_args=[message, "up"])
            if thumb:
                os.remove(thumb)

        elif "Animation" == msg_type:
            bot.send_animation(message.chat.id, file, reply_to_message_id=message.message_id)

        elif "Sticker" == msg_type:
            bot.send_sticker(message.chat.id, file, reply_to_message_id=message.message_id)

        elif "Voice" == msg_type:
            bot.send_voice(message.chat.id, file, caption=msg.caption, thumb=thumb, caption_entities=msg.caption_entities, reply_to_message_id=message.message_id, progress=progress, progress_args=[message, "up"])

        elif "Audio" == msg_type:
            try:
                thumb = acc.download_media(msg.audio.thumbs[0].file_id)
            except:
                thumb = None

            bot.send_audio(message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.message_id, progress=progress, progress_args=[message, "up"])
            if thumb:
                os.remove(thumb)

        elif "Photo" == msg_type:
            bot.send_photo(message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.message_id)

        os.remove(file)
        if os.path.exists(f'{message.message_id}upstatus.txt'):
            os.remove(f'{message.message_id}upstatus.txt')
        bot.delete_messages(message.chat.id, [smsg.message_id])

    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.message_id)
        print(f"Exception in handle_private: {e}")

# get the type of message
def get_message_type(msg):
    try:
        msg.document.file_id
        return "Document"
    except:
        pass
    
    try:
        msg.video.file_id
        return "Video"
    except:
        pass
    
    try:
        msg.animation.file_id
        return "Animation"
    except:
        pass
    
    try:
        msg.sticker.file_id
        return "Sticker"
    except:
        pass
    
    try:
        msg.voice.file_id
        return "Voice"
    except:
        pass
    
    try:
        msg.audio.file_id
        return "Audio"
    except:
        pass
    
    try:
        msg.photo.file_id
        return "Photo"
    except:
        pass
    
    try:
        msg.text
        return "Text"
    except:
        pass

# Usage text
USAGE = """**FOR PUBLIC CHATS**

**__just send post/s link__**

**FOR PRIVATE CHATS**

**__first send invite link of the chat (unnecessary if the account of string session already member of the chat)
then send post/s link__**

**FOR BOT CHATS**

**__send link with** '/b/', **bot's username and message id, you might want to install some unofficial client to get the id like below__**


**MULTI POSTS**

**__send public/private posts link as explained above with format "from - to" to send multiple messages like below__**


**__note that space in between doesn't matter__**
"""

# Run bot
bot.run()
