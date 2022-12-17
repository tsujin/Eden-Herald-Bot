from discord.ext import commands, tasks
from helpers import db_manager
import aiohttp
import datetime
import discord


class PveHerald(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_data(self):
        # required to receive json response
        headers = {'x-herald-api': 'minified'}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get('https://eden-daoc.net/hrald/proxy.php?pve') as request:
                if request.status == 200:
                    data = await request.json()
                    return data
                else:
                    print("Could not fetch data")

    async def parse_boss_kills(self, data):
        boss_kill_timer_map = {}
        for boss in data:
            try:
                last_killed_time = datetime.datetime.strptime(data[boss]['killed_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                boss_kill_timer_map[boss] = last_killed_time
            except TypeError:
                print("Skipping invalid data")

        return boss_kill_timer_map

    @tasks.loop(minutes=5.0)
    async def update_boss_data(self):
        db_data = await db_manager.get_boss_data()
        if not db_data:
            data = await self.fetch_data()
            parsed_data = await self.parse_boss_kills(data)
            for boss, killed_at in parsed_data.items():
                await db_manager.add_boss_kill(boss, killed_at)
        else:
            site_data = await self.fetch_data()
            parsed_site_data = await self.parse_boss_kills(site_data)

            for boss in db_data:
                boss_name = boss[0]
                killed_at = datetime.datetime.strptime(boss[1], '%Y-%m-%d %H:%M:%S.%f')
                new_killed_at = parsed_site_data[boss_name]

                if new_killed_at > killed_at:
                    print("Sending a boss update")
                    await db_manager.update_boss_kill(boss_name, new_killed_at)
                    await self.send_boss_update(boss_name, new_killed_at)

    @commands.Cog.listener()
    async def on_ready(self):
        self.update_boss_data.start()

    async def send_boss_update(self, boss_name, killed_at):
        timestamp = killed_at.replace(tzinfo=datetime.timezone.utc).timestamp()

        boss_update = discord.Embed(
            description=f"was killed <t:{int(timestamp)}:R>",
            title=boss_name,
            color=0x9C84EF
        )

        for server in self.bot.guilds:
            channel_id = await db_manager.get_channel(server.id)
            channel = self.bot.get_channel(channel_id)
            await channel.send(embed=boss_update)

    @commands.hybrid_command(
        name="setchannel",
        description="Sets channel to report boss kills in.",
    )
    async def set_reporting_channel(self, context: commands.Context, channel: discord.TextChannel):
        if await db_manager.get_channel(context.guild.id):
            await db_manager.update_channel(context.guild.id, channel.id)
        else:
            await db_manager.add_channel(context.guild.id, channel.id)

        user_confirmation_message = discord.Embed(
            description="The channel has been set.",
            color=0x9C84EF
        )
        new_channel_embed = discord.Embed(
            description="This has been set as the default channel for boss kill updates.",
            color=0x9C84EF
        )

        await context.send(embed=user_confirmation_message, ephemeral=True)
        await channel.send(embed=new_channel_embed)


async def setup(bot):
    await bot.add_cog(PveHerald(bot))
