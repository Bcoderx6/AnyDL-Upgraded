import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import numpy
import os
import time

from config import Config
from PIL import Image
from translation import Translation

import database.database as sql
import pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)
from pyrogram import Client, Filters 

@Client.on_message(Filters.photo)
async def save_photo(bot, update):
    if update.from_user.id in Config.BANNED_USER:
        await bot.delete_messages(
            chat_id=update.chat.id,
            message_ids=update.message_id,
            revoke=True
        )
        return
    if update.media_group_id is not None:
        # album is sent
        download_location = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + "/" + str(update.media_group_id) + "/"
        # create download directory, if not exist
        if not os.path.isdir(download_location):
            os.makedirs(download_location)
        await sql.df_thumb(update.from_user.id, update.message_id)
        await bot.download_media(
            message=update,
            file_name=download_location
        )
    else:
        # received single photo
        download_location = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + ".jpg"
        await bot.download_media(
            message=update,
            file_name=download_location
        )
        await sql.df_thumb(update.from_user.id, update.message_id)
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.SAVED_CUSTOM_THUMB_NAIL,
            reply_to_message_id=update.message_id
        )


@Client.on_message(Filters.command(["deletethumbnail"]))
async def delete_thumbnail(bot, update):
    if update.from_user.id in Config.BANNED_USER:
        await bot.delete_messages(
            chat_id=update.chat.id,
            message_ids=update.message_id,
            revoke=True
        )
        return
    download_location = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id)
    try:
        await sql.del_thumb(update.from_user.id)
        os.remove(download_location + ".jpg")
        # os.remove(download_location + ".json")
    except:
        pass
    await bot.send_message(
        chat_id=update.chat.id,
        text=Translation.DEL_ETED_CUSTOM_THUMB_NAIL,
        reply_to_message_id=update.message_id
    )
    
    
@Client.on_message(pyrogram.Filters.command(["generatecustomthumbnail"]))
def generate_custom_thumbnail(bot, update):
    TRChatBase(update.from_user.id, update.text, "generatecustomthumbnail")
    if str(update.from_user.id) not in Config.SUPER7X_DLBOT_USERS:
        bot.send_message(
            chat_id=update.chat.id,
            text=Translation.NOT_AUTH_USER_TEXT,
            reply_to_message_id=update.message_id
        )
        return
    if update.reply_to_message is not None:
        reply_message = update.reply_to_message
        if reply_message.media_group_id is not None:
            download_location = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id) + "/" + str(reply_message.media_group_id) + "/"
            save_final_image = download_location + str(round(time.time())) + ".jpg"
            list_im = os.listdir(download_location)
            if len(list_im) == 2:
                imgs = [ Image.open(download_location + i) for i in list_im ]
                inm_aesph = sorted([(numpy.sum(i.size), i.size) for i in imgs])
                min_shape = inm_aesph[1][1]
                imgs_comb = numpy.hstack(numpy.asarray(i.resize(min_shape)) for i in imgs)
                imgs_comb = Image.fromarray(imgs_comb)
                # combine: https://stackoverflow.com/a/30228789/4723940
                imgs_comb.save(save_final_image)
                # send
                bot.send_photo(
                    chat_id=update.chat.id,
                    photo=save_final_image,
                    caption=Translation.CUSTOM_CAPTION_UL_FILE,
                    reply_to_message_id=update.message_id
                )
            else:
                bot.send_message(
                    chat_id=update.chat.id,
                    text=Translation.ERR_ONLY_TWO_MEDIA_IN_ALBUM,
                    reply_to_message_id=update.message_id
                )
            try:
                [os.remove(download_location + i) for i in list_im ]
                os.remove(download_location)
            except:
                pass
        else:
            bot.send_message(
                chat_id=update.chat.id,
                text=Translation.REPLY_TO_MEDIA_ALBUM_TO_GEN_THUMB,
                reply_to_message_id=update.message_id
            )
    else:
        bot.send_message(
            chat_id=update.chat.id,
            text=Translation.REPLY_TO_MEDIA_ALBUM_TO_GEN_THUMB,
            reply_to_message_id=update.message_id
        )
