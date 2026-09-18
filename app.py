# -*- coding: utf-8 -*-
import os
import json
import binascii
import asyncio
import requests
import aiohttp
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf.json_format import MessageToJson
from google.protobuf.message import DecodeError
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# تجاهل تحذيرات الشهرسات الأمنية
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== إعدادات بوت التلجرام ====================
TELEGRAM_BOT_TOKEN = "8719274199:AAFTQ-6PeUE51KUqR4SFiTS3XOCPBlwuxuU"  # ضع توكن البوت هنا

# ==================== دمج كود Protobuf داخلياً (بدون ملفات خارجية) =---
_sym_db = _symbol_database.Default()

# 1. تعريف uid_generator
_DESCRIPTOR_UID = _descriptor_pool.Default().AddSerializedFile(b'\n\x13uid_generator.proto"0\n\ruid_generator\x12\x0f\n\x07saturn\x18\x01 \x01(\x03\x12\x0e\n\x06garena\x18\x02 \x01(\x03\x62\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(_DESCRIPTOR_UID, _globals)
_builder.BuildTopDescriptorsAndMessages(_DESCRIPTOR_UID, 'uid_generator_pb2', _globals)

# 2. تعريف like
_DESCRIPTOR_LIKE = _descriptor_pool.Default().AddSerializedFile(b'\n\nlike.proto"#\n\x04like\x12\x0b\n\x03uid\x18\x01 \x01(\x03\x12\x0e\n\x06region\x18\x02 \x01(\tb\x06proto3')
_builder.BuildMessageAndEnumDescriptors(_DESCRIPTOR_LIKE, _globals)
_builder.BuildTopDescriptorsAndMessages(_DESCRIPTOR_LIKE, 'like_pb2', _globals)

# 3. تعريف like_count
_DESCRIPTOR_COUNT = _descriptor_pool.Default().AddSerializedFile(b'\n\x10like_count.proto"?\n\tBasicInfo\x12\x0b\n\x03UID\x18\x01 \x01(\x03\x12\x16\n\x0ePlayerNickname\x18\x03 \x01(\t\x12\r\n\x05Likes\x18\x15 \x01(\x03"'\n\x04Info\x12\x1f\n\x0b\x41\x63\x63ountInfo\x18\x01 \x01(\x0b\x32\n.BasicInfob\x06proto3')
_builder.BuildMessageAndEnumDescriptors(_DESCRIPTOR_COUNT, _globals)
_builder.BuildTopDescriptorsAndMessages(_DESCRIPTOR_COUNT, 'like_count_pb2', _globals)

# ==================== روابط السيرفرات ====================
URLS_LIKE = {
    "IND": "https://client.ind.freefiremobile.com/LikeProfile",
    "BR": "https://client.us.freefiremobile.com/LikeProfile",
    "US": "https://client.us.freefiremobile.com/LikeProfile",
    "SAC": "https://client.us.freefiremobile.com/LikeProfile",
    "NA": "https://client.us.freefiremobile.com/LikeProfile"
}

URLS_INFO = {
    "IND": "https://client.ind.freefiremobile.com/GetPlayerPersonalShow",
    "BR": "https://client.us.freefiremobile.com/GetPlayerPersonalShow",
    "US": "https://client.us.freefiremobile.com/GetPlayerPersonalShow",
    "SAC": "https://client.us.freefiremobile.com/GetPlayerPersonalShow",
    "NA": "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
}

# ==================== الدوال الأساسية للعبة ====================

def load_tokens(server):
    filename = f"token_{server.lower()}.json"
    file_path = os.path.join("tokens", filename)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    default_path = os.path.join("tokens", "token_bd.json")
    if os.path.exists(default_path):
        with open(default_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def get_headers(token):
    return {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Expect": "100-continue",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB51",
    }

def encrypt_message(data):
    cipher = AES.new(b'Yg&tc%DEuh6%Zc^8', AES.MODE_CBC, b'6oyZDr22E3ychjM%')
    return binascii.hexlify(cipher.encrypt(pad(data, AES.block_size))).decode()

def create_like(uid, region):
    m = _globals['_LIKE']()  # استخدام الكلاس المدمج
    m.uid, m.region = int(uid), region
    return m.SerializeToString()

def create_uid(uid):
    m = _globals['_UID_GENERATOR']()  # استخدام الكلاس المدمج
    m.saturn_, m.garena = int(uid), 1
    return m.SerializeToString()

async def send(token, url, data):
    headers = get_headers(token)
    async with aiohttp.ClientSession() as s:
        async with s.post(url, data=bytes.fromhex(data), headers=headers) as r:
            return await r.text() if r.status == 200 else None

async def multi(uid, server, url):
    enc = encrypt_message(create_like(uid, server))
    tokens = load_tokens(server)
    if not tokens:
        return
    return await asyncio.gather(*[send(tokens[i % len(tokens)]['token'], url, enc) for i in range(105)])

def get_info(enc, server, token):
    urls = URLS_INFO
    r = requests.post(
        urls.get(server, "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"),
        data=bytes.fromhex(enc), 
        headers=get_headers(token), 
        verify=False
    )
    try:
        p = _globals['_INFO']()  # استخدام الكلاس المدمج
        p.ParseFromString(r.content)
        return p
    except DecodeError:
        return None

# ==================== أوامر بوت التلجرام ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك في بوت زيادة إعجابات فري فاير! 🎮\n\n"
        "استخدم الأمر بالشكل التالي:\n"
        "/like <UID> <Server>\n"
        "مثال: `/like 13002831333 ind`",
        parse_mode="Markdown"
    )

async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "❌ خطأ! يرجى إدخال الـ UID والسيرفر بشكل صحيح.\nمثال: `/like 13002831333 ind`", 
            parse_mode="Markdown"
        )
        return

    uid = args[0]
    server = args[1].upper()
    
    msg = await update.message.reply_text("⏳ جاري معالجة الطلب وإرسال الإعجابات، يرجى الانتظار...")

    try:
        tokens = load_tokens(server)
        if not tokens:
            await msg.edit_text(f"❌ لم يتم العثور على ملفات توكنات للسيرفر `{server}` في مجلد tokens.")
            return

        enc_uid = encrypt_message(create_uid(uid))
        before, tok = None, None
        
        for t in tokens[:10]:
            before = get_info(enc_uid, server, t["token"])
            if before:
                tok = t["token"]
                break
                
        if not before:
            await msg.edit_text("❌ لم يتم العثور على اللاعب أو أن الـ UID خاطئ.")
            return

        before_like = int(json.loads(MessageToJson(before)).get('AccountInfo', {}).get('Likes', 0))
        target_url = URLS_LIKE.get(server, "https://clientbp.ggblueshark.com/LikeProfile")
        
        await multi(uid, server, target_url)
        
        after = json.loads(MessageToJson(get_info(enc_uid, server, tok)))
        after_like = int(after.get('AccountInfo', {}).get('Likes', 0))
        
        player_name = after.get('AccountInfo', {}).get('PlayerNickname', 'Unknown')
        added = after_like - before_like

        result_text = (
            "✅ **تم إرسال الإعجابات بنجاح!**\n\n"
            f"👤 **اللاعب:** {player_name}\n"
            f"🆔 **الـ UID:** {uid}\n"
            f"👍 **الإعجابات قبل:** {before_like}\n"
            f"✨ **الإعجابات بعد:** {after_like}\n"
            f"📈 **المضاف:** {added}\n"
            f"🌐 **السيرفر:** {server}\n\n"
            "🔗 `great.thug4ff.com`"
        )
        await msg.edit_text(result_text, parse_mode="Markdown")

    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ أثناء تنفيذ الطلب: `{str(e)}`", parse_mode="Markdown")

# ==================== تشغيل البوت ====================

def main():
    if not os.path.exists("tokens"):
        os.makedirs("tokens")
        print("📁 تم إنشاء مجلد 'tokens' تلقائياً.")

    app_bot = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start_command))
    app_bot.add_handler(CommandHandler("like", like_command))
    
    print("🤖 بوت التلجرام يعمل الآن...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
