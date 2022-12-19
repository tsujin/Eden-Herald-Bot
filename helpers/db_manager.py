""""
Copyright © Krypton 2022 - https://github.com/kkrypt0nn (https://krypton.ninja)
Description:
This is a template to create your own discord bot in python.

Version: 5.4
"""

import aiosqlite


async def add_channel(server_id: int, channel_id: int):
    async with aiosqlite.connect("database/database.db") as db:
        await db.execute("INSERT INTO channels(server_id, channel_id) VALUES (?, ?)", (server_id,channel_id))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM channels")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0


async def update_channel(server_id: int, channel_id: int):
    async with aiosqlite.connect("database/database.db") as db:
        await db.execute("UPDATE channels SET channel_id=? WHERE server_id=?", (channel_id, server_id))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM channels")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result is not None else 0


async def get_channel(server_id: int):
    async with aiosqlite.connect("database/database.db") as db:
        rows = await db.execute("SELECT channel_id FROM channels WHERE server_id=?", (server_id,))
        async with rows as cursor:
            result = await cursor.fetchone()

        return result[0] if result else None


async def add_boss_kill(boss_name, killed_at):
    async with aiosqlite.connect("database/database.db") as db:
        await db.execute("INSERT INTO boss_kills(boss_name, last_killed) VALUES (?, ?)", (boss_name, killed_at))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM boss_kills")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def update_boss_kill(boss_name, killed_at):
    async with aiosqlite.connect("database/database.db") as db:
        await db.execute("UPDATE boss_kills SET last_killed = ? WHERE boss_name = ?", (killed_at, boss_name))
        await db.commit()
        rows = await db.execute("SELECT COUNT(*) FROM boss_kills")
        async with rows as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def get_boss_data():
    async with aiosqlite.connect("database/database.db") as db:
        rows = await db.execute("SELECT * FROM boss_kills")
        async with rows as cursor:
            result = await cursor.fetchall()
            result_list = []
            for row in result:
                result_list.append(row)
            return result_list


async def get_single_boss_data(boss_name):
    async with aiosqlite.connect("database/database.db") as db:
        rows = await db.execute("SELECT * FROM boss_kills WHERE boss_name LIKE ?", ['%'+boss_name+'%'])
        async with rows as cursor:
            result = await cursor.fetchone()
            return result if result else None