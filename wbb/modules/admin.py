"""
MIT License

Copyright (c) 2024 TheHamkerCat

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import asyncio
import re
from contextlib import suppress
from time import time

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus, ChatType
from pyrogram.errors import FloodWait
from pyrogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    ChatPermissions,
    ChatPrivileges,
    Message,
)

from wbb import BOT_ID, SUDOERS, app, log
from wbb.core.decorators.errors import capture_err
from wbb.core.keyboard import ikb
from wbb.utils.dbfunctions import (
    add_warn,
    get_warn,
    int_to_alpha,
    remove_warns,
    save_filter,
)
from wbb.utils.functions import (
    extract_user,
    extract_user_and_reason,
    time_converter,
)

# استيراد دوال نظام الرتب
from wbb.utils.ranks_db import get_user_rank_level, ARABIC_RANK_NAMES
from wbb.utils.rank_permissions import (
    can_ban, can_kick, can_mute, can_promote, can_demote
)

__MODULE__ = "Admin"
__HELP__ = """
**الأوامر المتاحة:**
/ban - حظر مستخدم
/dban - حذف الرسالة المراد الرد عليها مع حظر مرسلها
/tban - حظر مستخدم لمدة محددة
/unban - إلغاء حظر مستخدم
/listban - حظر مستخدم من مجموعات مدرجة في رسالة
/listunban - إلغاء حظر مستخدم من مجموعات مدرجة في رسالة
/warn - تحذير مستخدم
/dwarn - حذف الرسالة المراد الرد عليها مع تحذير مرسلها
/rmwarns - إزالة جميع تحذيرات مستخدم
/warns - عرض تحذيرات مستخدم
/kick - طرد مستخدم
/dkick - حذف الرسالة المراد الرد عليها مع طرد مرسلها
/purge - حذف رسائل متعددة
/purge [n] - حذف عدد n من الرسائل ابتداءً من الرسالة المراد الرد عليها
/del - حذف الرسالة المراد الرد عليها
/promote - رفع عضو كمشرف (حسب نظام الرتب)
/fullpromote - رفع عضو بكل الصلاحيات (حسب نظام الرتب)
/demote - تنزيل مشرف
/pin - تثبيت رسالة
/mute - كتم مستخدم
/tmute - كتم مستخدم لمدة محددة
/unmute - إلغاء كتم مستخدم
/ban_ghosts - حظر الحسابات المحذوفة
/report | @admins | @admin - الإبلاغ عن رسالة إلى المشرفين
/invite - إرسال رابط دعوة المجموعة

**الأوامر العربية (بدون /):**
حظر - حظر مستخدم (بالرد أو بذكر اسم المستخدم)
طرد - طرد مستخدم
رفع مشرف - رفع عضو كمشرف (صلاحيات محدودة حسب الرتب)
رفع مالك - رفع عضو كمشرف بكل الصلاحيات (حسب الرتب)
تنزيل مشرف - تنزيل مشرف
كتم - كتم مستخدم
الغاء كتم - إلغاء كتم مستخدم
تثبيت - تثبيت رسالة
الغاء تثبيت - إلغاء تثبيت رسالة
حذف - حذف الرسالة المراد الرد عليها
تنظيف - حذف رسائل متعددة (بدءاً من الرسالة المراد الرد عليها)
تحذير - تحذير مستخدم
تحذيرات - عرض تحذيرات مستخدم
إزالة تحذيرات - إزالة جميع تحذيرات مستخدم
تبليغ - الإبلاغ عن رسالة إلى المشرفين
دعوة - إرسال رابط دعوة المجموعة
"""


async def member_permissions(chat_id: int, user_id: int):
    perms = []
    member = (await app.get_chat_member(chat_id, user_id)).privileges
    if not member:
        return []
    if member.can_post_messages:
        perms.append("can_post_messages")
    if member.can_edit_messages:
        perms.append("can_edit_messages")
    if member.can_delete_messages:
        perms.append("can_delete_messages")
    if member.can_restrict_members:
        perms.append("can_restrict_members")
    if member.can_promote_members:
        perms.append("can_promote_members")
    if member.can_change_info:
        perms.append("can_change_info")
    if member.can_invite_users:
        perms.append("can_invite_users")
    if member.can_pin_messages:
        perms.append("can_pin_messages")
    if member.can_manage_video_chats:
        perms.append("can_manage_video_chats")
    return perms


from wbb.core.decorators.permissions import adminsOnly

admins_in_chat = {}


async def list_admins(chat_id: int):
    global admins_in_chat
    if chat_id in admins_in_chat:
        interval = time() - admins_in_chat[chat_id]["last_updated_at"]
        if interval < 3600:
            return admins_in_chat[chat_id]["data"]

    admins_in_chat[chat_id] = {
        "last_updated_at": time(),
        "data": [
            member.user.id
            async for member in app.get_chat_members(
                chat_id, filter=ChatMembersFilter.ADMINISTRATORS
            )
        ],
    }
    return admins_in_chat[chat_id]["data"]


# Admin cache reload
@app.on_chat_member_updated()
async def admin_cache_func(_, cmu: ChatMemberUpdated):
    if cmu.old_chat_member and cmu.old_chat_member.promoted_by:
        admins_in_chat[cmu.chat.id] = {
            "last_updated_at": time(),
            "data": [
                member.user.id
                async for member in app.get_chat_members(
                    cmu.chat.id, filter=ChatMembersFilter.ADMINISTRATORS
                )
            ],
        }
        log.info(f"تحديث قائمة المشرفين لـ {cmu.chat.id} [{cmu.chat.title}]")


# --------------------------------------------------------------
# دوال مساعدة للأوامر العربية
# --------------------------------------------------------------

async def extract_user_from_text(text: str, message: Message):
    """استخراج معرف المستخدم من نص عربي (مثلاً: @username أو الرد)"""
    if message.reply_to_message:
        if message.reply_to_message.from_user:
            return message.reply_to_message.from_user.id
        elif message.reply_to_message.sender_chat:
            return message.reply_to_message.sender_chat.id
    parts = text.split()
    if len(parts) > 1:
        mention = parts[1].strip()
        if mention.startswith('@'):
            try:
                user = await app.get_users(mention)
                return user.id
            except:
                pass
    return None


# --------------------------------------------------------------
# Purge Messages
# --------------------------------------------------------------

@app.on_message(filters.command("purge") & ~filters.private)
@adminsOnly("can_delete_messages")
async def purgeFunc(_, message: Message):
    repliedmsg = message.reply_to_message
    await message.delete()

    if not repliedmsg:
        return await message.reply_text("**الرجاء الرد على رسالة لبدء التنظيف منها.**")

    cmd = message.command
    if len(cmd) > 1 and cmd[1].isdigit():
        purge_to = repliedmsg.id + int(cmd[1])
        if purge_to > message.id:
            purge_to = message.id
    else:
        purge_to = message.id

    chat_id = message.chat.id
    message_ids = []

    for message_id in range(
        repliedmsg.id,
        purge_to,
    ):
        message_ids.append(message_id)

        if len(message_ids) == 100:
            await app.delete_messages(
                chat_id=chat_id,
                message_ids=message_ids,
                revoke=True,
            )
            message_ids = []

    if len(message_ids) > 0:
        await app.delete_messages(
            chat_id=chat_id,
            message_ids=message_ids,
            revoke=True,
        )
    await message.reply_text("**تم التنظيف بنجاح.**", delete_after=3)


# --------------------------------------------------------------
# Kick members
# --------------------------------------------------------------

@app.on_message(filters.command(["kick", "dkick"]) & ~filters.private)
async def kickFunc(_, message: Message):
    user_id, reason = await extract_user_and_reason(message)
    if not user_id:
        return await message.reply_text("**لم أتمكن من العثور على هذا المستخدم.**")
    
    chat_id = message.chat.id
    actor_id = message.from_user.id

    # التحقق من الصلاحية باستخدام نظام الرتب
    if not await can_kick(chat_id, actor_id, user_id):
        return await message.reply_text("❌ ليس لديك صلاحية لطرد هذا المستخدم.")

    if user_id == BOT_ID:
        return await message.reply_text("**لا يمكنني طرد نفسي، يمكنني المغادرة إذا أردت.**")
    if user_id in SUDOERS:
        return await message.reply_text("**لا يمكنك طرد أحد المطورين!**")
    if user_id in (await list_admins(message.chat.id)):
        return await message.reply_text("**لا يمكنني طرد مشرف، أنت تعرف القواعد وأنا أعرفها.**")

    mention = (await app.get_users(user_id)).mention
    msg = f"""
**المستخدم المطرود:** {mention}
**تم الطرد بواسطة:** {message.from_user.mention if message.from_user else 'مجهول'}
**السبب:** {reason or 'بدون سبب'}"""
    if message.command[0][0] == "d":
        await message.reply_to_message.delete()
    await message.chat.ban_member(user_id)
    replied_message = message.reply_to_message
    if replied_message:
        message = replied_message
    await message.reply_text(msg)
    await asyncio.sleep(1)
    await message.chat.unban_member(user_id)


# --------------------------------------------------------------
# Ban members
# --------------------------------------------------------------

@app.on_message(filters.command(["ban", "dban", "tban"]) & ~filters.private)
async def banFunc(_, message: Message):
    user_id, reason = await extract_user_and_reason(message, sender_chat=True)

    if not user_id:
        return await message.reply_text("**لم أتمكن من العثور على هذا المستخدم.**")
    
    chat_id = message.chat.id
    actor_id = message.from_user.id

    # التحقق من الصلاحية باستخدام نظام الرتب
    if not await can_ban(chat_id, actor_id, user_id):
        return await message.reply_text("❌ ليس لديك صلاحية لحظر هذا المستخدم.")

    if user_id == BOT_ID:
        return await message.reply_text("**لا يمكنني حظر نفسي، يمكنني المغادرة إذا أردت.**")
    if user_id in SUDOERS:
        return await message.reply_text("**لا يمكنك حظر أحد المطورين!**")
    if user_id in (await list_admins(message.chat.id)):
        return await message.reply_text("**لا يمكنني حظر مشرف، أنت تعرف القواعد وأنا أعرفها.**")

    try:
        mention = (await app.get_users(user_id)).mention
    except IndexError:
        mention = (
            message.reply_to_message.sender_chat.title
            if message.reply_to_message
            else "مجهول"
        )

    msg = (
        f"**المستخدم المحظور:** {mention}\n"
        f"**تم الحظر بواسطة:** {message.from_user.mention if message.from_user else 'مجهول'}\n"
    )
    if message.command[0][0] == "d":
        await message.reply_to_message.delete()
    if message.command[0] == "tban":
        split = reason.split(None, 1)
        time_value = split[0]
        temp_reason = split[1] if len(split) > 1 else ""
        temp_ban = await time_converter(message, time_value)
        msg += f"**مدة الحظر:** {time_value}\n"
        if temp_reason:
            msg += f"**السبب:** {temp_reason}"
        with suppress(AttributeError):
            if len(time_value[:-1]) < 3:
                await message.chat.ban_member(user_id, until_date=temp_ban)
                replied_message = message.reply_to_message
                if replied_message:
                    message = replied_message
                await message.reply_text(msg)
            else:
                await message.reply_text("**لا يمكنك استخدام أكثر من 99**")
        return
    if reason:
        msg += f"**السبب:** {reason}"
    await message.chat.ban_member(user_id)
    replied_message = message.reply_to_message
    if replied_message:
        message = replied_message
    await message.reply_text(msg)


# --------------------------------------------------------------
# Unban members
# --------------------------------------------------------------

@app.on_message(filters.command("unban") & ~filters.private)
@adminsOnly("can_restrict_members")  # نتركها لأن unban لا يؤذي
async def unban_func(_, message: Message):
    reply = message.reply_to_message

    if reply and reply.sender_chat and reply.sender_chat != message.chat.id:
        return await message.reply_text("**لا يمكنك إلغاء حظر قناة.**")

    if len(message.command) == 2:
        user = message.text.split(None, 1)[1]
    elif len(message.command) == 1 and reply:
        user = message.reply_to_message.from_user.id
    else:
        return await message.reply_text(
            "**الرجاء تقديم اسم مستخدم أو الرد على رسالة المستخدم لإلغاء الحظر.**"
        )
    await message.chat.unban_member(user)
    umention = (await app.get_users(user)).mention
    replied_message = message.reply_to_message
    if replied_message:
        message = replied_message
    await message.reply_text(f"**تم إلغاء حظر {umention}!**")


# --------------------------------------------------------------
# Ban users listed in a message (خاص بالمطورين فقط)
# --------------------------------------------------------------

@app.on_message(SUDOERS & filters.command("listban") & ~filters.private)
async def list_ban_(c, message: Message):
    userid, msglink_reason = await extract_user_and_reason(message)
    if not userid or not msglink_reason:
        return await message.reply_text(
            "**الرجاء تقديم معرف المستخدم/اسم المستخدم مع رابط الرسالة والسبب لحظر متعدد.**"
        )
    if len(msglink_reason.split(" ")) == 1:
        return await message.reply_text("**يجب تقديم سبب للحظر المتعدد.**")
    lreason = msglink_reason.split()
    messagelink, reason = lreason[0], " ".join(lreason[1:])

    if not re.search(r"(https?://)?t(elegram)?\.me/\w+/\d+", messagelink):
        return await message.reply_text("**رابط رسالة غير صالح.**")

    if userid == BOT_ID:
        return await message.reply_text("**لا يمكنني حظر نفسي.**")
    if userid in SUDOERS:
        return await message.reply_text("**لا يمكنك حظر أحد المطورين!**")
    splitted = messagelink.split("/")
    uname, mid = splitted[-2], int(splitted[-1])
    m = await message.reply_text(
        "**جاري حظر المستخدم من مجموعات متعددة. قد يستغرق هذا بعض الوقت...**"
    )
    try:
        msgtext = (await app.get_messages(uname, mid)).text
        gusernames = re.findall(r"@\w+", msgtext)
    except:
        return await m.edit_text("**تعذر الحصول على أسماء المجموعات.**")
    count = 0
    for username in gusernames:
        try:
            await app.ban_chat_member(username.strip("@"), userid)
            await asyncio.sleep(1)
        except FloodWait as e:
            await asyncio.sleep(e.x)
        except:
            continue
        count += 1
    mention = (await app.get_users(userid)).mention

    msg = f"""
**المستخدم المحظور متعدداً:** {mention}
**معرف المستخدم:** `{userid}`
**بواسطة:** {message.from_user.mention}
**عدد المجموعات المتأثرة:** `{count}`
**السبب:** {reason}
"""
    await m.edit_text(msg)


# --------------------------------------------------------------
# Unban users listed in a message (خاص بالمطورين)
# --------------------------------------------------------------

@app.on_message(SUDOERS & filters.command("listunban") & ~filters.private)
async def list_unban_(c, message: Message):
    userid, msglink = await extract_user_and_reason(message)
    if not userid or not msglink:
        return await message.reply_text(
            "**الرجاء تقديم معرف المستخدم/اسم المستخدم مع رابط الرسالة لإلغاء الحظر المتعدد.**"
        )

    if not re.search(r"(https?://)?t(elegram)?\.me/\w+/\d+", msglink):
        return await message.reply_text("**رابط رسالة غير صالح.**")

    splitted = msglink.split("/")
    uname, mid = splitted[-2], int(splitted[-1])
    m = await message.reply_text(
        "**جاري إلغاء حظر المستخدم من مجموعات متعددة. قد يستغرق هذا بعض الوقت...**"
    )
    try:
        msgtext = (await app.get_messages(uname, mid)).text
        gusernames = re.findall(r"@\w+", msgtext)
    except:
        return await m.edit_text("**تعذر الحصول على أسماء المجموعات.**")
    count = 0
    for username in gusernames:
        try:
            await app.unban_chat_member(username.strip("@"), userid)
            await asyncio.sleep(1)
        except FloodWait as e:
            await asyncio.sleep(e.x)
        except:
            continue
        count += 1
    mention = (await app.get_users(userid)).mention
    msg = f"""
**المستخدم الملغى حظره متعدداً:** {mention}
**معرف المستخدم:** `{userid}`
**بواسطة:** {message.from_user.mention}
**عدد المجموعات المتأثرة:** `{count}`
"""
    await m.edit_text(msg)


# --------------------------------------------------------------
# Delete messages
# --------------------------------------------------------------

@app.on_message(filters.command("del") & ~filters.private)
@adminsOnly("can_delete_messages")
async def deleteFunc(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("**الرجاء الرد على رسالة لحذفها.**")
    await message.reply_to_message.delete()
    await message.delete()


# --------------------------------------------------------------
# Promote Members (مع نظام الرتب)
# --------------------------------------------------------------

@app.on_message(filters.command(["promote", "fullpromote"]) & ~filters.private)
async def promoteFunc(_, message: Message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("**لم أتمكن من العثور على هذا المستخدم.**")
    
    chat_id = message.chat.id
    actor_id = message.from_user.id

    # تحديد الرتبة المطلوبة: إذا كان الأمر fullpromote نريد رتبة owner، وإلا admin
    target_rank = "owner" if message.command[0].startswith("full") else "admin"

    # التحقق من الصلاحية باستخدام نظام الرتب
    allowed, reason = await can_promote(chat_id, actor_id, user_id, target_rank)
    if not allowed:
        return await message.reply_text(f"❌ {reason}")

    bot = (await app.get_chat_member(message.chat.id, BOT_ID)).privileges
    if user_id == BOT_ID:
        return await message.reply_text("**لا يمكنني رفع نفسي.**")
    if not bot:
        return await message.reply_text("**أنا لست مشرفاً في هذه الدردشة.**")
    if not bot.can_promote_members:
        return await message.reply_text("**ليست لدي الصلاحيات الكافية.**")

    umention = (await app.get_users(user_id)).mention

    if message.command[0].startswith("full"):
        # صلاحيات كاملة
        await message.chat.promote_member(
            user_id=user_id,
            privileges=ChatPrivileges(
                can_change_info=bot.can_change_info,
                can_invite_users=bot.can_invite_users,
                can_delete_messages=bot.can_delete_messages,
                can_restrict_members=bot.can_restrict_members,
                can_pin_messages=bot.can_pin_messages,
                can_promote_members=bot.can_promote_members,
                can_manage_chat=bot.can_manage_chat,
                can_manage_video_chats=bot.can_manage_video_chats,
            ),
        )
        await message.reply_text(f"**تم رفع {umention} بكل الصلاحيات (رتبة مالك)!**")
    else:
        # صلاحيات محدودة (أدمن)
        await message.chat.promote_member(
            user_id=user_id,
            privileges=ChatPrivileges(
                can_change_info=False,
                can_invite_users=bot.can_invite_users,
                can_delete_messages=bot.can_delete_messages,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False,
                can_manage_chat=bot.can_manage_chat,
                can_manage_video_chats=bot.can_manage_video_chats,
            ),
        )
        await message.reply_text(f"**تم رفع {umention} كمشرف (رتبة أدمن)!**")


# --------------------------------------------------------------
# Demote Member (مع نظام الرتب)
# --------------------------------------------------------------

@app.on_message(filters.command("demote") & ~filters.private)
async def demote(_, message: Message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("**لم أتمكن من العثور على هذا المستخدم.**")
    
    chat_id = message.chat.id
    actor_id = message.from_user.id

    # التحقق من الصلاحية باستخدام نظام الرتب
    allowed, reason = await can_demote(chat_id, actor_id, user_id)
    if not allowed:
        return await message.reply_text(f"❌ {reason}")

    if user_id == BOT_ID:
        return await message.reply_text("**لا يمكنني تنزيل نفسي.**")
    if user_id in SUDOERS:
        return await message.reply_text("**لا يمكنك تنزيل أحد المطورين!**")
    try:
        member = await app.get_chat_member(message.chat.id, user_id)
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            await message.chat.promote_member(
                user_id=user_id,
                privileges=ChatPrivileges(
                    can_change_info=False,
                    can_invite_users=False,
                    can_delete_messages=False,
                    can_restrict_members=False,
                    can_pin_messages=False,
                    can_promote_members=False,
                    can_manage_chat=False,
                    can_manage_video_chats=False,
                ),
            )
            umention = (await app.get_users(user_id)).mention
            await message.reply_text(f"**تم تنزيل {umention} من الإشراف!**")
        else:
            await message.reply_text("**الشخص المذكور ليس مشرفاً.**")
    except Exception as e:
        await message.reply_text(str(e))


# --------------------------------------------------------------
# Pin Messages
# --------------------------------------------------------------

@app.on_message(filters.command(["pin", "unpin"]) & ~filters.private)
@adminsOnly("can_pin_messages")  # نتركها لأنها لا تعتمد على الرتب كثيراً
async def pin(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("**الرجاء الرد على رسالة لتثبيتها أو إلغاء تثبيتها.**")
    r = message.reply_to_message
    if message.command[0][0] == "u":
        await r.unpin()
        return await message.reply_text(
            f"**تم إلغاء تثبيت [هذه الرسالة]({r.link}).**",
            disable_web_page_preview=True,
        )
    await r.pin(disable_notification=True)
    await message.reply(
        f"**تم تثبيت [هذه الرسالة]({r.link}).**",
        disable_web_page_preview=True,
    )
    msg = "يرجى مراجعة الرسالة المثبتة: ~ " + f"[اضغط هنا, {r.link}]"
    filter_ = dict(type="text", data=msg)
    await save_filter(message.chat.id, "~pinned", filter_)


# --------------------------------------------------------------
# Mute members (مع نظام الرتب)
# --------------------------------------------------------------

@app.on_message(filters.command(["mute", "tmute"]) & ~filters.private)
async def mute(_, message: Message):
    user_id, reason = await extract_user_and_reason(message)
    if not user_id:
        return await message.reply_text("**لم أتمكن من العثور على هذا المستخدم.**")
    
    chat_id = message.chat.id
    actor_id = message.from_user.id

    # التحقق من الصلاحية باستخدام نظام الرتب
    if not await can_mute(chat_id, actor_id, user_id):
        return await message.reply_text("❌ ليس لديك صلاحية لكتم هذا المستخدم.")

    if user_id == BOT_ID:
        return await message.reply_text("**لا يمكنني كتم نفسي.**")
    if user_id in SUDOERS:
        return await message.reply_text("**لا يمكنك كتم أحد المطورين!**")
    if user_id in (await list_admins(message.chat.id)):
        return await message.reply_text("**لا يمكنني كتم مشرف، أنت تعرف القواعد وأنا أعرفها.**")
    
    mention = (await app.get_users(user_id)).mention
    keyboard = ikb({"🚨  إلغاء الكتم  🚨": f"unmute_{user_id}"})
    msg = (
        f"**المستخدم المكتوم:** {mention}\n"
        f"**تم الكتم بواسطة:** {message.from_user.mention if message.from_user else 'مجهول'}\n"
    )
    if message.command[0] == "tmute":
        split = reason.split(None, 1)
        time_value = split[0]
        temp_reason = split[1] if len(split) > 1 else ""
        temp_mute = await time_converter(message, time_value)
        msg += f"**مدة الكتم:** {time_value}\n"
        if temp_reason:
            msg += f"**السبب:** {temp_reason}"
        try:
            if len(time_value[:-1]) < 3:
                await message.chat.restrict_member(
                    user_id,
                    permissions=ChatPermissions(),
                    until_date=temp_mute,
                )
                replied_message = message.reply_to_message
                if replied_message:
                    message = replied_message
                await message.reply_text(msg, reply_markup=keyboard)
            else:
                await message.reply_text("**لا يمكنك استخدام أكثر من 99**")
        except AttributeError:
            pass
        return
    if reason:
        msg += f"**السبب:** {reason}"
    await message.chat.restrict_member(user_id, permissions=ChatPermissions())
    replied_message = message.reply_to_message
    if replied_message:
        message = replied_message
    await message.reply_text(msg, reply_markup=keyboard)


# --------------------------------------------------------------
# Unmute members
# --------------------------------------------------------------

@app.on_message(filters.command("unmute") & ~filters.private)
async def unmute(_, message: Message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("**لم أتمكن من العثور على هذا المستخدم.**")
    
    chat_id = message.chat.id
    actor_id = message.from_user.id

    # التحقق من الصلاحية: نفس صلاحية الكتم
    if not await can_mute(chat_id, actor_id, user_id):
        return await message.reply_text("❌ ليس لديك صلاحية لإلغاء كتم هذا المستخدم.")

    await message.chat.unban_member(user_id)
    umention = (await app.get_users(user_id)).mention
    replied_message = message.reply_to_message
    if replied_message:
        message = replied_message
    await message.reply_text(f"**تم إلغاء كتم {umention}!**")


# --------------------------------------------------------------
# Ban deleted accounts
# --------------------------------------------------------------

@app.on_message(filters.command("ban_ghosts") & ~filters.private)
@adminsOnly("can_restrict_members")
async def ban_deleted_accounts(_, message: Message):
    chat_id = message.chat.id
    deleted_users = []
    banned_users = 0
    m = await message.reply("**جاري البحث عن الحسابات المحذوفة...**")

    async for i in app.get_chat_members(chat_id):
        if i.user.is_deleted:
            deleted_users.append(i.user.id)
    if len(deleted_users) > 0:
        for deleted_user in deleted_users:
            try:
                await message.chat.ban_member(deleted_user)
            except Exception:
                pass
            banned_users += 1
        await m.edit(f"**تم حظر {banned_users} حساباً محذوفاً.**")
    else:
        await m.edit("**لا توجد حسابات محذوفة في هذه الدردشة.**")


# --------------------------------------------------------------
# Warn system
# --------------------------------------------------------------

@app.on_message(filters.command(["warn", "dwarn"]) & ~filters.private)
@adminsOnly("can_restrict_members")
async def warn_user(_, message: Message):
    user_id, reason = await extract_user_and_reason(message)
    chat_id = message.chat.id
    if not user_id:
        return await message.reply_text("**لم أتمكن من العثور على هذا المستخدم.**")
    if user_id == BOT_ID:
        return await message.reply_text("**لا يمكنني تحذير نفسي.**")
    if user_id in SUDOERS:
        return await message.reply_text("**لا يمكنك تحذير أحد المطورين!**")
    if user_id in (await list_admins(chat_id)):
        return await message.reply_text("**لا يمكنني تحذير مشرف، أنت تعرف القواعد وأنا أعرفها.**")
    user, warns = await asyncio.gather(
        app.get_users(user_id),
        get_warn(chat_id, await int_to_alpha(user_id)),
    )
    mention = user.mention
    keyboard = ikb({"🚨  إزالة التحذير  🚨": f"unwarn_{user_id}"})
    if warns:
        warns = warns["warns"]
    else:
        warns = 0
    if message.command[0][0] == "d":
        await message.reply_to_message.delete()
    if warns >= 2:
        await message.chat.ban_member(user_id)
        await message.reply_text(f"**تجاوز عدد تحذيرات {mention} الحد، تم الحظر!**")
        await remove_warns(chat_id, await int_to_alpha(user_id))
    else:
        warn = {"warns": warns + 1}
        msg = f"""
**المستخدم المحذر:** {mention}
**تم التحذير بواسطة:** {message.from_user.mention if message.from_user else 'مجهول'}
**السبب:** {reason or 'بدون سبب'}
**التحذيرات:** {warns + 1}/3"""
        replied_message = message.reply_to_message
        if replied_message:
            message = replied_message
        await message.reply_text(msg, reply_markup=keyboard)
        await add_warn(chat_id, await int_to_alpha(user_id), warn)


@app.on_callback_query(filters.regex("unwarn_"))
async def remove_warning(_, cq: CallbackQuery):
    from_user = cq.from_user
    chat_id = cq.message.chat.id
    permissions = await member_permissions(chat_id, from_user.id)
    permission = "can_restrict_members"
    if permission not in permissions:
        return await cq.answer(
            "ليس لديك الصلاحيات الكافية لتنفيذ هذا الإجراء.\n"
            + f"الصلاحية المطلوبة: {permission}",
            show_alert=True,
        )
    user_id = cq.data.split("_")[1]
    warns = await get_warn(chat_id, await int_to_alpha(user_id))
    if warns:
        warns = warns["warns"]
    if not warns or warns == 0:
        return await cq.answer("**لا يوجد تحذيرات لهذا المستخدم.**")
    warn = {"warns": warns - 1}
    await add_warn(chat_id, await int_to_alpha(user_id), warn)
    text = cq.message.text.markdown
    text = f"~~{text}~~\n\n"
    text += f"__تم إزالة التحذير بواسطة {from_user.mention}__"
    await cq.message.edit(text)


@app.on_message(filters.command("rmwarns") & ~filters.private)
@adminsOnly("can_restrict_members")
async def remove_warnings(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("**الرجاء الرد على رسالة لإزالة تحذيرات المستخدم.**")
    user_id = message.reply_to_message.from_user.id
    mention = message.reply_to_message.from_user.mention
    chat_id = message.chat.id
    warns = await get_warn(chat_id, await int_to_alpha(user_id))
    if warns:
        warns = warns["warns"]
    if warns == 0 or not warns:
        await message.reply_text(f"**{mention} ليس لديه تحذيرات.**")
    else:
        await remove_warns(chat_id, await int_to_alpha(user_id))
        await message.reply_text(f"**تم إزالة تحذيرات {mention}.**")


@app.on_message(filters.command("warns") & ~filters.private)
@capture_err
async def check_warns(_, message: Message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("**لم أتمكن من العثور على هذا المستخدم.**")
    warns = await get_warn(message.chat.id, await int_to_alpha(user_id))
    mention = (await app.get_users(user_id)).mention
    if warns:
        warns = warns["warns"]
    else:
        return await message.reply_text(f"**{mention} ليس لديه تحذيرات.**")
    return await message.reply_text(f"**{mention} لديه {warns}/3 تحذيرات.**")


# --------------------------------------------------------------
# Report
# --------------------------------------------------------------

@app.on_message(
    (
        filters.command("report")
        | filters.command(["admins", "admin"], prefixes="@")
    )
    & ~filters.private
)
@capture_err
async def report_user(_, message):
    if len(message.text.split()) <= 1 and not message.reply_to_message:
        return await message.reply_text(
            "**الرجاء الرد على رسالة للإبلاغ عن هذا المستخدم.**"
        )

    reply = message.reply_to_message if message.reply_to_message else message
    reply_id = reply.from_user.id if reply.from_user else reply.sender_chat.id
    user_id = (
        message.from_user.id if message.from_user else message.sender_chat.id
    )

    list_of_admins = await list_admins(message.chat.id)
    linked_chat = (await app.get_chat(message.chat.id)).linked_chat
    if linked_chat is not None:
        if (
            reply_id in list_of_admins
            or reply_id == message.chat.id
            or reply_id == linked_chat.id
        ):
            return await message.reply_text(
                "**هل تعلم أن المستخدم الذي ترد عليه هو مشرف؟**"
            )
    else:
        if reply_id in list_of_admins or reply_id == message.chat.id:
            return await message.reply_text(
                "**هل تعلم أن المستخدم الذي ترد عليه هو مشرف؟**"
            )

    user_mention = (
        reply.from_user.mention if reply.from_user else reply.sender_chat.title
    )
    text = f"**تم الإبلاغ عن {user_mention} إلى المشرفين!**"
    admin_data = [
        i
        async for i in app.get_chat_members(
            chat_id=message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS
        )
    ]
    for admin in admin_data:
        if admin.user.is_bot or admin.user.is_deleted:
            continue
        text += f"[\u2063](tg://user?id={admin.user.id})"

    await reply.reply_text(text)


# --------------------------------------------------------------
# Invite link
# --------------------------------------------------------------

@app.on_message(filters.command("invite"))
@adminsOnly("can_invite_users")
async def invite(_, message):
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        link = (await app.get_chat(message.chat.id)).invite_link
        if not link:
            link = await app.export_chat_invite_link(message.chat.id)
        text = f"**رابط دعوة هذه المجموعة:**\n\n{link}"
        if message.reply_to_message:
            await message.reply_to_message.reply_text(
                text, disable_web_page_preview=True
            )
        else:
            await message.reply_text(text, disable_web_page_preview=True)


# --------------------------------------------------------------
# معالج الأوامر العربية (بدون /)
# --------------------------------------------------------------

@app.on_message(filters.text & filters.group & ~filters.command([]))
async def arabic_command_handler(client, message):
    text = message.text.strip()
    
    if text.startswith("حظر"):
        await banFunc(client, message)
        return
    
    if text.startswith("طرد"):
        await kickFunc(client, message)
        return
    
    if text.startswith("رفع مالك"):
        # محاكاة الأمر /fullpromote
        message.command = ["fullpromote"] + message.text.split()[1:]
        await promoteFunc(client, message)
        return
    
    if text.startswith("رفع مشرف"):
        message.command = ["promote"] + message.text.split()[1:]
        await promoteFunc(client, message)
        return
    
    if text.startswith("تنزيل مشرف"):
        message.command = ["demote"] + message.text.split()[1:]
        await demote(client, message)
        return
    
    if text.startswith("كتم"):
        await mute(client, message)
        return
    
    if text.startswith("الغاء كتم"):
        await unmute(client, message)
        return
    
    if text.startswith("تثبيت"):
        await pin(client, message)
        return
    
    if text.startswith("الغاء تثبيت"):
        message.command = ["unpin"] + message.text.split()[1:]
        await pin(client, message)
        return
    
    if text.startswith("حذف"):
        await deleteFunc(client, message)
        return
    
    if text.startswith("تنظيف"):
        await purgeFunc(client, message)
        return
    
    if text.startswith("تحذير"):
        await warn_user(client, message)
        return
    
    if text.startswith("إزالة تحذيرات"):
        await remove_warnings(client, message)
        return
    
    if text.startswith("تحذيرات"):
        await check_warns(client, message)
        return
    
    if text.startswith("تبليغ"):
        await report_user(client, message)
        return
    
    if text.startswith("دعوة"):
        await invite(client, message)
        return
