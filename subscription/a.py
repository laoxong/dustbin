import asyncio
from pyrogram import Client, enums

api_id = 12345
api_hash = ""
bot_token = ""

TARGET = None
import sqlite3

app = Client(
    "my_bot",
    api_id=api_id, api_hash=api_hash,
    bot_token=bot_token,
)
conn = sqlite3.connect('user.db')
async def main():
    async with app:
        count=0
        async for member in app.get_chat_members(TARGET):
            sql = "UPDATE user SET username = '{}' WHERE id = {} ".format(member.user.username, member.user.id)
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
            count = count + 1
        conn.close()
        await app.send_message(TARGET, "共更新了{}个RBQ的信息".format(count))
app.run(main())