from wbb import SUDOERS
from wbb.utils.ranks_db import get_user_rank_level

async def can_kick(chat_id: int, actor_id: int, target_id: int) -> bool:
    """التحقق مما إذا كان بإمكان المستخدم (actor) طرد المستخدم (target)"""
    # المطورون (SUDOERS) يمكنهم كل شيء
    if actor_id in SUDOERS:
        return True
    
    actor_level = await get_user_rank_level(chat_id, actor_id)
    target_level = await get_user_rank_level(chat_id, target_id)
    
    # المالك الأساسي (المستوى 3) يمكنه طرد أي شخص ما عدا مالك أساسي آخر
    if actor_level == 3:
        return target_level < 3  # لا يطرد من هم في نفس مستواه (3) أو أعلى (المنشئ 4)
    
    # المالك (المستوى 2) يمكنه طرد: المنشئ (4)، الأدمن (1)، العضو (0) – ولا يمكنه طرد مالك آخر (2)
    if actor_level == 2:
        return target_level in [0, 1, 4]  # يطرد المنشئ رغم أنه أعلى رقماً لكن هذا المطلوب
    
    # الأدمن (المستوى 1) لا يمكنه الطرد مطلقاً
    return False


async def can_ban(chat_id: int, actor_id: int, target_id: int) -> bool:
    """نفس صلاحية الطرد (الحظر أشد)"""
    return await can_kick(chat_id, actor_id, target_id)


async def can_mute(chat_id: int, actor_id: int, target_id: int) -> bool:
    """التحقق من صلاحية الكتم"""
    if actor_id in SUDOERS:
        return True
    
    actor_level = await get_user_rank_level(chat_id, actor_id)
    target_level = await get_user_rank_level(chat_id, target_id)
    
    # الأدمن (المستوى 1) يمكنه كتم الأعضاء فقط (المستوى 0)
    if actor_level == 1:
        return target_level == 0
    
    # المالك (2) والمالك الأساسي (3) يمكنهما كتم أي شخص
    if actor_level >= 2:
        return True
    
    return False


async def can_promote(chat_id: int, actor_id: int, target_id: int, new_rank: str) -> bool:
    """التحقق من صلاحية رفع عضو إلى رتبة معينة"""
    if actor_id in SUDOERS:
        return True, ""
    
    actor_level = await get_user_rank_level(chat_id, actor_id)
    target_level = await get_user_rank_level(chat_id, target_id)
    
    # المالك الأساسي (3) يمكنه رفع أي رتبة (ما عدا رفع مالك أساسي آخر)
    if actor_level == 3:
        if target_level >= 3:
            return False, "لا يمكنك رفع مالك أساسي آخر."
        # يمكنه رفع المنشئ (4) لكن المنشئ رتبة شرفية، يمكن رفع أي شخص لأي رتبة
        return True, ""
    
    # المالك (2) يمكنه رفع الأدمنة فقط (1)
    if actor_level == 2:
        if new_rank != "admin":
            return False, "يمكنك فقط رفع أعضاء إلى رتبة أدمن."
        return True, ""
    
    return False, "ليس لديك صلاحية للرفع."


async def can_demote(chat_id: int, actor_id: int, target_id: int) -> bool:
    """التحقق من صلاحية تنزيل عضو (إعادته عضو عادي)"""
    if actor_id in SUDOERS:
        return True, ""
    
    actor_level = await get_user_rank_level(chat_id, actor_id)
    target_level = await get_user_rank_level(chat_id, target_id)
    
    # المالك الأساسي (3) يمكنه تنزيل أي شخص ما عدا مالك أساسي آخر
    if actor_level == 3:
        if target_level >= 3:
            return False, "لا يمكنك تنزيل مالك أساسي آخر."
        return True, ""
    
    # المالك (2) يمكنه تنزيل الأدمنة (1) والمنشئ (4) والأعضاء (0) – أي شخص ليس مالكاً أو مالكاً أساسياً
    if actor_level == 2:
        if target_level >= 2:
            return False, "لا يمكنك تنزيل مالك أو أعلى."
        return True, ""
    
    return False, "ليس لديك صلاحية للتنزيل."
