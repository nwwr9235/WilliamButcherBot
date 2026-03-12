from wbb import db

ranks_collection = db.ranks

# مستويات الرتب (كلما زاد الرقم زادت الصلاحية)
RANK_LEVELS = {
    "member": 0,
    "admin": 1,
    "owner": 2,
    "primary_owner": 3,
    "creator": 4   # رتبة شرفية، لكنها أعلى رقمياً لأنها لا تمنح صلاحيات بل مجرد لقب
}

RANK_NAMES = {
    0: "member",
    1: "admin",
    2: "owner",
    3: "primary_owner",
    4: "creator"
}

# الأسماء العربية للعرض
ARABIC_RANK_NAMES = {
    "member": "👤 عضو",
    "admin": "🔰 أدمن",
    "owner": "👑 مالك",
    "primary_owner": "💎 مالك أساسي",
    "creator": "🌟 منشئ"
}

async def set_user_rank(chat_id: int, user_id: int, rank: str):
    """تعيين رتبة لعضو في مجموعة معينة"""
    if rank not in RANK_LEVELS:
        return False
    await ranks_collection.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"rank": rank, "level": RANK_LEVELS[rank]}},
        upsert=True
    )
    return True

async def get_user_rank(chat_id: int, user_id: int):
    """الحصول على رتبة عضو في مجموعة معينة"""
    doc = await ranks_collection.find_one({"chat_id": chat_id, "user_id": user_id})
    if doc:
        return doc.get("rank", "member")
    return "member"

async def get_user_rank_level(chat_id: int, user_id: int):
    """الحصول على مستوى الرتبة (رقم)"""
    doc = await ranks_collection.find_one({"chat_id": chat_id, "user_id": user_id})
    if doc:
        return doc.get("level", 0)
    return 0

async def delete_user_rank(chat_id: int, user_id: int):
    """حذف رتبة عضو (إعادته عضو عادي)"""
    await ranks_collection.delete_one({"chat_id": chat_id, "user_id": user_id})

async def get_chat_ranks(chat_id: int):
    """الحصول على جميع الرتب في مجموعة (قاموس {user_id: rank})"""
    cursor = ranks_collection.find({"chat_id": chat_id})
    ranks = {}
    async for doc in cursor:
        ranks[str(doc["user_id"])] = doc["rank"]
    return ranks
