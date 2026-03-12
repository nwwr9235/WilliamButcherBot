#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 بوت الأغاني والإدارة - النسخة العربية الشاملة
يعمل على: المجموعات + القنوات + الرسائل الخاصة
"""

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatMember
import yt_dlp
from datetime import datetime
from config_arabic import *

# ==============================================================================
# إنشاء عميل البوت
# ==============================================================================

التطبيق = Client(
    name="بوت_عربي",
    api_id=معرف_التطبيق,
    api_hash=كود_التطبيق,
    bot_token=رمز_البوت,
)

# ==============================================================================
# متغيرات عامة
# ==============================================================================

قائمة_الأغاني_العامة = {}  # قائمة الأغاني لكل مجموعة/قناة
الأغاني_الحالية = {}      # الأغنية الحالية لكل مكان
حالة_التشغيل = {}         # حالة التشغيل لكل مكان
التحذيرات = {}            # التحذيرات في المجموعات
الكلمات_المحظورة = {}     # الكلمات المحظورة في كل مجموعة
المستخدمون = {}           # بيانات المستخدمين

# ==============================================================================
# دوال مساعدة
# ==============================================================================

def الحصول_على_معرف_المجموعة(رسالة: Message) -> int:
    """الحصول على معرف المجموعة أو القناة أو الرسالة الخاصة"""
    return رسالة.chat.id

def الحصول_على_النوع(رسالة: Message) -> str:
    """الحصول على نوع الدردشة"""
    if رسالة.chat.type == "private":
        return "خاص"
    elif رسالة.chat.type == "group":
        return "مجموعة"
    elif رسالة.chat.type == "supergroup":
        return "سوبر_جروب"
    elif رسالة.chat.type == "channel":
        return "قناة"
    return "غير_معروف"

async def ابحث_في_اليوتيوب(الاستعلام: str, عدد_النتائج: int = 1):
    """البحث عن الأغاني في YouTube"""
    try:
        خيارات_ytdl = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'force_generic_extractor': True,
        }
        
        with yt_dlp.YoutubeDL(خيارات_ytdl) as ydl:
            النتائج = ydl.extract_info(f"ytsearch{عدد_النتائج}:{الاستعلام}", download=False)
            return النتائج['entries']
    except:
        return None

# ==============================================================================
# أوامر البدء والمساعدة
# ==============================================================================

@التطبيق.on_message(filters.command("ابدأ"))
async def ابدأ(عميل: Client, رسالة: Message):
    """أمر البدء - يعمل في كل مكان"""
    المستخدم = رسالة.from_user
    نوع_الدردشة = الحصول_على_النوع(رسالة)
    
    if نوع_الدردشة == "خاص":
        نص_الترحيب = f"""
👋 **أهلاً وسهلاً {المستخدم.first_name}!**

أنا بوت الأغاني والإدارة 🤖

📚 **الخدمات المتاحة:**

🎵 **تشغيل الأغاني:**
   • تشغيل اسم_الأغنية
   • بحث كلمة
   • قائمة
   • الأغنية

👥 **معلومات:**
   • معلومات
   • مساعدة

⚠️ **ملاحظة:** بعض الأوامر متاحة في المجموعات فقط
"""
    elif نوع_الدردشة == "قناة":
        نص_الترحيب = f"""
📢 **أهلاً بك في {رسالة.chat.title}!**

أنا بوت القناة 🤖

📚 **الخدمات المتاحة:**

🎵 **تشغيل الأغاني:**
   • تشغيل اسم_الأغنية
   • بحث كلمة
   • قائمة
   • الأغنية

📊 **معلومات:**
   • معلومات
   • مساعدة
"""
    else:  # مجموعة
        نص_الترحيب = f"""
🎉 **أهلاً بك في {رسالة.chat.title}!**

أنا بوت إدارة المجموعات 🤖

📚 **الخدمات المتاحة:**

🎵 **تشغيل الأغاني:**
   • تشغيل اسم_الأغنية
   • بحث كلمة
   • قائمة
   • الأغنية

👮 **الإدارة:**
   • كتم / فك
   • حظر / فك_حظر
   • تحذير
   • امسح

اكتب: **مساعدة** لعرض جميع الأوامر
"""
    
    لوحة_المفاتيح = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📚 مساعدة", callback_data="مساعدة_رئيسية"),
        ]
    ])
    
    await رسالة.reply_text(نص_الترحيب, reply_markup=لوحة_المفاتيح, parse_mode="markdown")

@التطبيق.on_message(filters.command("مساعدة"))
async def مساعدة(عميل: Client, رسالة: Message):
    """عرض المساعدة حسب نوع الدردشة"""
    نوع_الدردشة = الحصول_على_النوع(رسالة)
    
    مساعدة_عامة = """
📚 **قائمة الأوامر الكاملة**

🎵 **أوامر الأغاني (في كل مكان):**
━━━━━━━━━━━━━━━━━━━━━━━━━━
   تشغيل اسم_الأغنية    ← تشغيل أغنية من YouTube
   بحث كلمة            ← البحث عن أغنية (5 نتائج)
   إيقاف              ← إيقاف الأغنية
   استئناف            ← استئناف التشغيل
   التالي             ← أغنية تالية
   السابق             ← أغنية سابقة
   قائمة              ← عرض القائمة
   الأغنية            ← الأغنية الحالية

⚙️ **أوامر عامة (في كل مكان):**
━━━━━━━━━━━━━━━━━━━━━━━━━━
   ابدأ               ← بدء البوت
   مساعدة             ← هذه الرسالة
   معلومات            ← معلومات البوت
   إحصائيات           ← احصائيات المكان الحالي
"""
    
    if نوع_الدردشة in ["مجموعة", "سوبر_جروب"]:
        مساعدة_متقدمة = """
👮 **أوامر الإدارة (في المجموعات فقط):**
━━━━━━━━━━━━━━━━━━━━━━━━━━
   كتم               ← كتم عضو (رد أولاً)
   فك                ← فك كتم (رد أولاً)
   حظر               ← حظر عضو (رد أولاً)
   فك_حظر معرف       ← فك حظر برقم
   أزل                ← إزالة عضو (رد أولاً)
   تحذير             ← تحذير عضو (رد أولاً)
   امسح_التحذيرات    ← حذف تحذيرات (رد أولاً)
   احظر_كلمات        ← حظر كلمات معينة
   الكلمات            ← عرض الكلمات المحظورة
   أعضاء             ← عدد الأعضاء
   الإدارة            ← قائمة الإداريين
   امسح عدد           ← حذف رسائل
   ثبّت              ← تثبيت رسالة
   فك_التثبيت        ← فك التثبيت
"""
        await رسالة.reply_text(مساعدة_عامة + مساعدة_متقدمة, parse_mode="markdown")
    else:
        await رسالة.reply_text(مساعدة_عامة, parse_mode="markdown")

# ==============================================================================
# أوامر الأغاني (تعمل في كل مكان)
# ==============================================================================

@التطبيق.on_message(filters.command("تشغيل"))
async def تشغيل(عميل: Client, رسالة: Message):
    """تشغيل أغنية"""
    معرف_الدردشة = الحصول_على_معرف_المجموعة(رسالة)
    
    if not رسالة.text.split(' ', 1)[1:]:
        await رسالة.reply_text("❌ **اكتب اسم الأغنية!**\n\nمثال: `تشغيل اغنية حزينة`", parse_mode="markdown")
        return
    
    الاستعلام = رسالة.text.split(' ', 1)[1]
    رسالة_البحث = await رسالة.reply_text(f"🔍 **جاري البحث عن:** `{الاستعلام}`...")
    
    try:
        النتائج = await ابحث_في_اليوتيوب(الاستعلام, 1)
        
        if not النتائج:
            await رسالة_البحث.edit_text("❌ **لم أجد الأغنية!**")
            return
        
        الأغنية = النتائج[0]
        رابط_الأغنية = f"https://www.youtube.com/watch?v={الأغنية['id']}"
        
        # تهيئة قائمة الأغاني للدردشة الأولى
        if معرف_الدردشة not in قائمة_الأغاني_العامة:
            قائمة_الأغاني_العامة[معرف_الدردشة] = []
        
        قائمة_الأغاني_العامة[معرف_الدردشة].append({
            'الاسم': الأغنية['title'],
            'الرابط': رابط_الأغنية,
            'المعرف': الأغنية['id'],
            'أضاف': رسالة.from_user.first_name,
            'الوقت': datetime.now()
        })
        
        الأغاني_الحالية[معرف_الدردشة] = قائمة_الأغاني_العامة[معرف_الدردشة][-1]
        
        نص = (
            f"✅ **تم إضافة الأغنية!**\n\n"
            f"🎵 **الاسم:** `{الأغنية['title']}`\n"
            f"👤 **أضاف:** {رسالة.from_user.mention()}\n"
            f"📍 **الموضع:** #{len(قائمة_الأغاني_العامة[معرف_الدردشة])}"
        )
        
        لوحة = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("▶️ تشغيل", callback_data=f"تشغيل_الآن_{معرف_الدردشة}"),
                InlineKeyboardButton("📋 القائمة", callback_data=f"عرض_القائمة_{معرف_الدردشة}")
            ]
        ])
        
        await رسالة_البحث.edit_text(نص, reply_markup=لوحة, parse_mode="markdown")
        
    except Exception as e:
        await رسالة_البحث.edit_text(f"❌ **خطأ:** `{str(e)}`")

@التطبيق.on_message(filters.command("بحث"))
async def بحث(عميل: Client, رسالة: Message):
    """البحث عن أغنية"""
    معرف_الدردشة = الحصول_على_معرف_المجموعة(رسالة)
    
    if not رسالة.text.split(' ', 1)[1:]:
        await رسالة.reply_text("❌ **اكتب كلمة البحث!**\n\nمثال: `بحث اغاني حب`", parse_mode="markdown")
        return
    
    الاستعلام = رسالة.text.split(' ', 1)[1]
    رسالة_البحث = await رسالة.reply_text(f"🔍 **جاري البحث عن:** `{الاستعلام}`...")
    
    try:
        النتائج = await ابحث_في_اليوتيوب(الاستعلام, 5)
        
        if not النتائج:
            await رسالة_البحث.edit_text("❌ **لم أجد نتائج!**")
            return
        
        نص = f"🎵 **نتائج البحث عن:** `{الاستعلام}`\n\n"
        
        أزرار = []
        for i, أغنية in enumerate(النتائج, 1):
            نص += f"{i}️⃣ **{أغنية['title']}**\n"
            أزرار.append([
                InlineKeyboardButton(f"تشغيل #{i}", callback_data=f"تشغيل_بحث_{أغنية['id']}_{معرف_الدردشة}")
            ])
        
        لوحة = InlineKeyboardMarkup(أزرار)
        await رسالة_البحث.edit_text(نص, reply_markup=لوحة, parse_mode="markdown")
        
    except Exception as e:
        await رسالة_البحث.edit_text(f"❌ **خطأ:** `{str(e)}`")

@التطبيق.on_message(filters.command("إيقاف"))
async def إيقاف(عميل: Client, رسالة: Message):
    """إيقاف الأغنية"""
    معرف_الدردشة = الحصول_على_معرف_المجموعة(رسالة)
    
    if معرف_الدردشة not in حالة_التشغيل:
        حالة_التشغيل[معرف_الدردشة] = False
    
    حالة_التشغيل[معرف_الدردشة] = False
    await رسالة.reply_text("⏸️ **تم إيقاف الأغنية**")

@التطبيق.on_message(filters.command("استئناف"))
async def استئناف(عميل: Client, رسالة: Message):
    """استئناف التشغيل"""
    معرف_الدردشة = الحصول_على_معرف_المجموعة(رسالة)
    
    if معرف_الدردشة not in الأغاني_الحالية or not الأغاني_الحالية[معرف_الدردشة]:
        await رسالة.reply_text("❌ **لا توجد أغنية موقوفة!**")
        return
    
    حالة_التشغيل[معرف_الدردشة] = True
    أغنية = الأغاني_الحالية[معرف_الدردشة]
    
    await رسالة.reply_text(
        f"▶️ **تم استئناف التشغيل**\n🎵 `{أغنية['الاسم']}`",
        parse_mode="markdown"
    )

@التطبيق.on_message(filters.command("قائمة"))
async def قائمة(عميل: Client, رسالة: Message):
    """عرض قائمة التشغيل"""
    معرف_الدردشة = الحصول_على_معرف_المجموعة(رسالة)
    
    if معرف_الدردشة not in قائمة_الأغاني_العامة or not قائمة_الأغاني_العامة[معرف_الدردشة]:
        await رسالة.reply_text("📭 **القائمة فارغة!**\n\nاستخدم `تشغيل اسم_الأغنية`", parse_mode="markdown")
        return
    
    القائمة = قائمة_الأغاني_العامة[معرف_الدردشة]
    نص = f"🎵 **قائمة التشغيل** ({len(القائمة)} أغنية)\n\n"
    
    for i, أغنية in enumerate(القائمة, 1):
        رمز = "▶️" if i == len(القائمة) else "🎵"
        نص += f"{i}. {رمز} {أغنية['الاسم']}\n"
    
    await رسالة.reply_text(نص, parse_mode="markdown")

@التطبيق.on_message(filters.command("الأغنية"))
async def الأغنية(عميل: Client, رسالة: Message):
    """عرض الأغنية الحالية"""
    معرف_الدردشة = الحصول_على_معرف_المجموعة(رسالة)
    
    if معرف_الدردشة not in الأغاني_الحالية or not الأغاني_الحالية[معرف_الدردشة]:
        await رسالة.reply_text("❌ **لا توجد أغنية قيد التشغيل!**")
        return
    
    أغنية = الأغاني_الحالية[معرف_الدردشة]
    نص = (
        f"🎵 **الأغنية الحالية:**\n\n"
        f"**الاسم:** `{أغنية['الاسم']}`\n"
        f"👤 **أضاف:** {أغنية['أضاف']}\n"
        f"⏰ **الوقت:** {أغنية['الوقت'].strftime('%H:%M:%S')}"
    )
    
    await رسالة.reply_text(نص, parse_mode="markdown")

# ==============================================================================
# أوامر الإدارة (للمجموعات فقط)
# ==============================================================================

@التطبيق.on_message(filters.command("كتم") & filters.group)
async def كتم(عميل: Client, رسالة: Message):
    """كتم عضو"""
    if not رسالة.reply_to_message:
        await رسالة.reply_text("❌ **رد على رسالة العضو أولاً!**")
        return
    
    معرف_العضو = رسالة.reply_to_message.from_user.id
    اسم_العضو = رسالة.reply_to_message.from_user.mention()
    
    try:
        await عميل.restrict_chat_member(
            chat_id=رسالة.chat.id,
            user_id=معرف_العضو,
            permissions=None
        )
        
        await رسالة.reply_text(
            f"🔇 **تم كتم صوت العضو!**\n👤 {اسم_العضو}",
            parse_mode="markdown"
        )
    except Exception as e:
        await رسالة.reply_text(f"❌ **خطأ:** `{str(e)}`")

@التطبيق.on_message(filters.command("فك") & filters.group)
async def فك(عميل: Client, رسالة: Message):
    """فك كتم عضو"""
    if not رسالة.reply_to_message:
        await رسالة.reply_text("❌ **رد على رسالة العضو أولاً!**")
        return
    
    معرف_العضو = رسالة.reply_to_message.from_user.id
    اسم_العضو = رسالة.reply_to_message.from_user.mention()
    
    try:
        from pyrogram.types import ChatPermissions
        
        await عميل.restrict_chat_member(
            chat_id=رسالة.chat.id,
            user_id=معرف_العضو,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True
            )
        )
        
        await رسالة.reply_text(
            f"🔊 **تم فك الكتم!**\n👤 {اسم_العضو}",
            parse_mode="markdown"
        )
    except Exception as e:
        await رسالة.reply_text(f"❌ **خطأ:** `{str(e)}`")

@التطبيق.on_message(filters.command("حظر") & filters.group)
async def حظر(عميل: Client, رسالة: Message):
    """حظر عضو"""
    if not رسالة.reply_to_message:
        await رسالة.reply_text("❌ **رد على رسالة العضو أولاً!**")
        return
    
    معرف_العضو = رسالة.reply_to_message.from_user.id
    اسم_العضو = رسالة.reply_to_message.from_user.mention()
    
    try:
        await عميل.ban_chat_member(
            chat_id=رسالة.chat.id,
            user_id=معرف_العضو
        )
        
        await رسالة.reply_text(
            f"🚫 **تم حظر العضو!**\n👤 {اسم_العضو}",
            parse_mode="markdown"
        )
    except Exception as e:
        await رسالة.reply_text(f"❌ **خطأ:** `{str(e)}`")

@التطبيق.on_message(filters.command("تحذير") & filters.group)
async def تحذير(عميل: Client, رسالة: Message):
    """تحذير عضو"""
    if not رسالة.reply_to_message:
        await رسالة.reply_text("❌ **رد على رسالة العضو أولاً!**")
        return
    
    معرف_العضو = رسالة.reply_to_message.from_user.id
    اسم_العضو = رسالة.reply_to_message.from_user.mention()
    معرف_المجموعة = رسالة.chat.id
    
    المفتاح = f"{معرف_المجموعة}_{معرف_العضو}"
    التحذيرات[المفتاح] = التحذيرات.get(المفتاح, 0) + 1
    عدد_التحذيرات = التحذيرات[المفتاح]
    
    if عدد_التحذيرات >= 3:
        try:
            await عميل.ban_chat_member(معرف_المجموعة, معرف_العضو)
            await رسالة.reply_text(
                f"🚫 **تم حظر العضو بعد 3 تحذيرات!**\n👤 {اسم_العضو}"
            )
        except:
            pass
    else:
        await رسالة.reply_text(
            f"⚠️ **تحذير!**\n👤 {اسم_العضو}\n📊 التحذيرات: {عدد_التحذيرات}/3"
        )

@التطبيق.on_message(filters.command("أعضاء") & filters.group)
async def أعضاء(عميل: Client, رسالة: Message):
    """عرض عدد الأعضاء"""
    try:
        عدد_الأعضاء = await عميل.get_chat_members_count(رسالة.chat.id)
        اسم_المجموعة = رسالة.chat.title
        
        نص = f"""
👥 **احصائيات {اسم_المجموعة}:**

📊 **عدد الأعضاء:** `{عدد_الأعضاء}`
📝 **اسم المجموعة:** {اسم_المجموعة}
🆔 **معرف:** `{رسالة.chat.id}`
📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d')}
⏰ **الوقت:** {datetime.now().strftime('%H:%M:%S')}
"""
        await رسالة.reply_text(نص, parse_mode="markdown")
    except Exception as e:
        await رسالة.reply_text(f"❌ **خطأ:** `{str(e)}`")

@التطبيق.on_message(filters.command("امسح") & filters.group)
async def امسح(عميل: Client, رسالة: Message):
    """حذف الرسائل الأخيرة"""
    args = رسالة.text.split()
    if len(args) < 2:
        await رسالة.reply_text("❌ **استخدام خاطئ!**\n\nمثال: `امسح 10`", parse_mode="markdown")
        return
    
    try:
        عدد = int(args[1])
        تم_الحذف = 0
        
        async for رسالة_قديمة in عميل.get_chat_history(رسالة.chat.id, limit=عدد):
            try:
                await رسالة_قديمة.delete()
                تم_الحذف += 1
            except:
                pass
        
        await رسالة.reply_text(f"🗑️ **تم حذف {تم_الحذف} رسالة!**")
    except Exception as e:
        await رسالة.reply_text(f"❌ **خطأ:** `{str(e)}`")

# ==============================================================================
# أوامر معلومات (تعمل في كل مكان)
# ==============================================================================

@التطبيق.on_message(filters.command("معلومات"))
async def معلومات(عميل: Client, رسالة: Message):
    """معلومات البوت"""
    نوع_الدردشة = الحصول_على_النوع(رسالة)
    
    نص = f"""
ℹ️ **معلومات البوت العربي**

🤖 **الاسم:** بوت الأغاني والإدارة
📦 **الإصدار:** 3.0.0 عربي شامل
🐍 **اللغة:** Python 3.9+
📚 **المكتبة:** Pyrogram

✨ **الميزات:**
   ✅ تشغيل الأغاني من YouTube
   ✅ إدارة متقدمة للمجموعات
   ✅ دعم القنوات
   ✅ رسائل خاصة
   ✅ 100% أوامر عربية

📍 **مكان الاستخدام:** {نوع_الدردشة}
📊 **الإحصائيات:**
   ⏰ تاريخ الاستخدام: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    await رسالة.reply_text(نص, parse_mode="markdown")

@التطبيق.on_message(filters.command("إحصائيات"))
async def إحصائيات(عميل: Client, رسالة: Message):
    """احصائيات المجموعة أو القناة"""
    نوع_الدردشة = الحصول_على_النوع(رسالة)
    
    if نوع_الدردشة == "خاص":
        نص = f"""
📊 **احصائياتك:**

👤 **الاسم:** {رسالة.from_user.first_name}
🆔 **معرفك:** `{رسالة.from_user.id}`
📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d')}
⏰ **الوقت:** {datetime.now().strftime('%H:%M:%S')}
"""
    elif نوع_الدردشة == "قناة":
        نص = f"""
📊 **احصائيات القناة:**

📢 **اسم القناة:** {رسالة.chat.title}
🆔 **معرف:** `{رسالة.chat.id}`
📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d')}
⏰ **الوقت:** {datetime.now().strftime('%H:%M:%S')}
"""
    else:
        try:
            عدد_الأعضاء = await عميل.get_chat_members_count(رسالة.chat.id)
            نص = f"""
📊 **احصائيات المجموعة:**

👥 **الأعضاء:** `{عدد_الأعضاء}`
📝 **الاسم:** {رسالة.chat.title}
🆔 **معرف:** `{رسالة.chat.id}`
📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d')}
⏰ **الوقت:** {datetime.now().strftime('%H:%M:%S')}
"""
        except:
            نص = "❌ **خطأ في الحصول على البيانات**"
    
    await رسالة.reply_text(نص, parse_mode="markdown")

# ==============================================================================
# معالج Callbacks
# ==============================================================================

@التطبيق.on_callback_query()
async def معالج_الأزرار(عميل: Client, الاستدعاء):
    """معالج النقر على الأزرار"""
    البيانات = الاستدعاء.data
    
    if البيانات == "مساعدة_رئيسية":
        await الاستدعاء.answer("📚 جاري تحميل المساعدة...")
        # يمكن إضافة منطق إضافي هنا
    
    await الاستدعاء.answer()

# ==============================================================================
# أوامر اختصارة إضافية
# ==============================================================================

@التطبيق.on_message(filters.command("ه"))
async def همسة(عميل: Client, رسالة: Message):
    """أمر الهمسة - الرد على رسالة وكتابة ه لتحويلها لهمسة"""
    
    # يجب أن يكون الرد على رسالة فقط
    if not رسالة.reply_to_message:
        await رسالة.reply_text(
            "❌ **استخدام خاطئ!**\n\n"
            "طريقة الاستخدام:\n"
            "1️⃣ رد على أي رسالة\n"
            "2️⃣ اكتب: `ه`\n\n"
            "البوت سيحول الرسالة لهمسة سرية!",
            parse_mode="markdown"
        )
        return
    
    الرسالة_الأصلية = رسالة.reply_to_message
    صاحب_الرسالة = الرسالة_الأصلية.from_user.first_name
    
    نص_الهمسة = f"""
🤫 **همسة:**

> {الرسالة_الأصلية.text or '[رسالة بدون نص]'}

━━━━━━━━━━━━━━━━━━━━
⚠️ رسالة خاصة جداً!
"""
    
    try:
        # إرسال الهمسة
        await رسالة.reply_text(نص_الهمسة, parse_mode="markdown")
        # حذف الأمر الأصلي
        await رسالة.delete()
    except Exception as e:
        await رسالة.reply_text(f"❌ **خطأ:** `{str(e)}`")

@التطبيق.on_message(filters.command("ا"))
async def هويتي_مع_صورة(عميل: Client, رسالة: Message):
    """أمر الهوية - يعطيك المعرف والصورة فقط"""
    
    # إذا تم الرد على شخص آخر
    if رسالة.reply_to_message:
        المستخدم = رسالة.reply_to_message.from_user
    else:
        المستخدم = رسالة.from_user
    
    معرف_المستخدم = المستخدم.id
    
    try:
        # الحصول على صورة الملف الشخصي
        صور_الملف = await عميل.get_user_profile_photos(معرف_المستخدم, limit=1)
        
        if صور_الملف.total_count > 0:
            # إرسال الصورة فقط مع المعرف
            الصورة = صور_الملف.photos[0][0]
            
            نص = f"🆔 **المعرف:** `{معرف_المستخدم}`"
            
            await رسالة.reply_photo(
                photo=الصورة.file_id,
                caption=نص,
                parse_mode="markdown"
            )
        else:
            # إذا لم توجد صورة، أرسل المعرف فقط
            await رسالة.reply_text(
                f"🆔 **المعرف:** `{معرف_المستخدم}`\n"
                f"❌ **الصورة:** لا توجد صورة ملف شخصي",
                parse_mode="markdown"
            )
    
    except Exception as e:
        await رسالة.reply_text(f"❌ **خطأ:** `{str(e)}`")

@التطبيق.on_message(filters.command("اا"))
async def هويتي_صورة_فقط(عميل: Client, رسالة: Message):
    """أمر الهوية - يعطيك الصورة فقط"""
    
    # إذا تم الرد على شخص آخر
    if رسالة.reply_to_message:
        المستخدم = رسالة.reply_to_message.from_user
    else:
        المستخدم = رسالة.from_user
    
    معرف_المستخدم = المستخدم.id
    
    try:
        # الحصول على صورة الملف الشخصي
        صور_الملف = await عميل.get_user_profile_photos(معرف_المستخدم, limit=1)
        
        if صور_الملف.total_count > 0:
            # إرسال الصورة فقط بدون نص
            الصورة = صور_الملف.photos[0][0]
            
            await رسالة.reply_photo(photo=الصورة.file_id)
        else:
            # إذا لم توجد صورة
            await رسالة.reply_text(
                f"❌ **لا توجد صورة ملف شخصي لهذا المستخدم**",
                parse_mode="markdown"
            )
    
    except Exception as e:
        await رسالة.reply_text(f"❌ **خطأ:** `{str(e)}`")

# ==============================================================================
# معالجات الرسائل
# ==============================================================================

@التطبيق.on_message(filters.text & ~filters.command(""))
async def معالجة_الرسائل(عميل: Client, رسالة: Message):
    """معالجة الرسائل العادية"""
    # يمكن إضافة منطق إضافي هنا مثل التحية والرد الآلي
    pass

# ==============================================================================
# بدء البوت
# ==============================================================================

async def main():
    print("\n" + "="*70)
    print("🤖 بوت الأغاني والإدارة - النسخة العربية الشاملة")
    print("="*70)
    print(f"✅ جاري بدء البوت...")
    print(f"📅 الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 البوت يعمل على: المجموعات + القنوات + الرسائل الخاصة")
    print("="*70 + "\n")
    
    async with التطبيق:
        print("✅ تم الاتصال بـ Telegram بنجاح!")
        print("🎯 البوت جاهز الآن...")
        print("\n💡 الأوامر الأساسية:")
        print("   • تشغيل اسم_الأغنية")
        print("   • بحث كلمة")
        print("   • مساعدة")
        print("   • معلومات")
        print("   • (في المجموعات) كتم / حظر / تحذير\n")
        
        await التطبيق.listen()

if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ تم إيقاف البوت!")
        print("إلى اللقاء! 👋")
    except Exception as e:
        print(f"\n❌ خطأ: {str(e)}")
