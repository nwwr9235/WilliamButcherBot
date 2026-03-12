from pyrogram import filters
from pyrogram.types import Message

from wbb import app, SUDOERS
from wbb.utils.ranks_db import (
    set_user_rank, get_user_rank, get_user_rank_level,
    delete_user_rank, get_chat_ranks, ARABIC_RANK_NAMES, RANK_LEVELS
)
from wbb.utils.rank_permissions import can_promote, can_demote
from wbb.utils.functions import extract_user

__MODULE__ = "الرتب"
__HELP__ = """
**نظام الرتب الداخلي للبوت**

/rank [بالرد] - عرض رتبة العضو
/setrank [رتبة] [بالرد] - تعيين رتبة (للمالك الأساسي فقط)
/delrank [بالرد] - إزالة رتبة خاصة
/ranks - عرض جميع الرتب في المجموعة

**الرتب والصلاحيات:**
🌟 منشئ - رتبة شرفية، لا صلاحيات، يمكن طرده من قبل المالك والمالك الأساسي.
💎 مالك أساسي - كل الصلاحيات، لكن لا يستطيع طرد مالك أساسي آخر.
👑 مالك - يمكنه: طرد، حظر، كتم، رفع وتنزيل الأدمنة.
🔰 أدمن - يمكنه: كتم الأعضاء فقط.
👤 عضو - لا صلاحيات.

**الأوامر العربية (بدون /):**
رتبتي
الرتب
رفع ادمن [بالرد على العضو]
رفع مالك [بالرد على العضو]
رفع مالك اساسي [بالرد على العضو]
تنزيل [بالرد على العضو]
"""


@app.on_message(filters.command(["rank", "myrank"]) & ~filters.private)
async def rank_command(_, message: Message):
    """عرض رتبة مستخدم"""
    chat_id = message.chat.id
    target_user = None
    
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        target_user = await extract_user(message)
    else:
        target_user = message.from_user
    
    if not target_user:
        return await message.reply_text("❌ لم أتمكن من العثور على المستخدم.")
    
    rank = await get_user_rank(chat_id, target_user.id)
    rank_arabic = ARABIC_RANK_NAMES.get(rank, "👤 عضو")
    
    await message.reply_text(
        f"**رتبة {target_user.mention}:** {rank_arabic}"
    )


@app.on_message(filters.command("setrank") & ~filters.private)
async def setrank_command(_, message: Message):
    """تعيين رتبة لعضو (رفع)"""
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ الاستخدام: /setrank [رتبة] [بالرد على العضو]\n"
            "الرتب المتاحة: admin, owner, primary_owner, creator"
        )
    
    if not message.reply_to_message:
        return await message.reply_text("❌ يجب الرد على رسالة العضو.")
    
    target_user = message.reply_to_message.from_user
    if not target_user:
        return await message.reply_text("❌ لم أتمكن من العثور على المستخدم.")
    
    chat_id = message.chat.id
    actor_id = message.from_user.id
    rank = message.command[1].lower()
    
    if rank not in ["admin", "owner", "primary_owner", "creator"]:
        return await message.reply_text("❌ رتبة غير صالحة.")
    
    # التحقق من الصلاحية
    allowed, reason = await can_promote(chat_id, actor_id, target_user.id, rank)
    if not allowed:
        return await message.reply_text(f"❌ {reason}")
    
    success = await set_user_rank(chat_id, target_user.id, rank)
    if success:
        rank_arabic = ARABIC_RANK_NAMES.get(rank, rank)
        await message.reply_text(
            f"✅ تم رفع {target_user.mention} إلى رتبة **{rank_arabic}**"
        )
    else:
        await message.reply_text("❌ حدث خطأ أثناء تعيين الرتبة.")


@app.on_message(filters.command("delrank") & ~filters.private)
async def delrank_command(_, message: Message):
    """إزالة رتبة خاصة من عضو (تنزيل إلى عضو)"""
    if not message.reply_to_message:
        return await message.reply_text("❌ يجب الرد على رسالة العضو.")
    
    target_user = message.reply_to_message.from_user
    if not target_user:
        return await message.reply_text("❌ لم أتمكن من العثور على المستخدم.")
    
    chat_id = message.chat.id
    actor_id = message.from_user.id
    
    # التحقق من الصلاحية
    allowed, reason = await can_demote(chat_id, actor_id, target_user.id)
    if not allowed:
        return await message.reply_text(f"❌ {reason}")
    
    await delete_user_rank(chat_id, target_user.id)
    await message.reply_text(
        f"✅ تم تنزيل {target_user.mention} إلى رتبة **عضو**"
    )


@app.on_message(filters.command("ranks") & ~filters.private)
async def ranks_list_command(_, message: Message):
    """عرض جميع الرتب في المجموعة"""
    chat_id = message.chat.id
    ranks = await get_chat_ranks(chat_id)
    
    if not ranks:
        return await message.reply_text("📊 لا يوجد أعضاء برتب خاصة في هذه المجموعة.")
    
    # ترتيب العرض
    rank_order = ["creator", "primary_owner", "owner", "admin"]
    rank_names = ARABIC_RANK_NAMES
    
    text = "**📊 قائمة الرتب في المجموعة:**\n\n"
    
    for rank in rank_order:
        users = []
        for uid, r in ranks.items():
            if r == rank:
                try:
                    user = await app.get_users(int(uid))
                    users.append(f"• {user.mention}")
                except:
                    users.append(f"• {uid}")
        if users:
            text += f"**{rank_names[rank]}:**\n" + "\n".join(users) + "\n\n"
    
    await message.reply_text(text)


# -------------------------------------------------------------------
# معالج الأوامر العربية
# -------------------------------------------------------------------

@app.on_message(filters.text & filters.group & ~filters.command([]))
async def arabic_ranks_handler(client, message):
    text = message.text.strip()
    
    if text == "رتبتي":
        rank = await get_user_rank(message.chat.id, message.from_user.id)
        rank_arabic = ARABIC_RANK_NAMES.get(rank, "👤 عضو")
        await message.reply_text(f"**رتبتك:** {rank_arabic}")
        return
    
    if text == "الرتب":
        await ranks_list_command(client, message)
        return
    
    if text.startswith("رفع ادمن") and message.reply_to_message:
        # محاكاة الأمر /setrank admin
        message.command = ["setrank", "admin"]
        await setrank_command(client, message)
        return
    
    if text.startswith("رفع مالك") and message.reply_to_message:
        message.command = ["setrank", "owner"]
        await setrank_command(client, message)
        return
    
    if text.startswith("رفع مالك اساسي") and message.reply_to_message:
        message.command = ["setrank", "primary_owner"]
        await setrank_command(client, message)
        return
    
    if text.startswith("رفع منشئ") and message.reply_to_message:
        message.command = ["setrank", "creator"]
        await setrank_command(client, message)
        return
    
    if text.startswith("تنزيل") and message.reply_to_message:
        await delrank_command(client, message)
        return
