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
        print("Beginning boss data update")
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
                    print(f"Sending a boss update for {boss_name}")
                    await db_manager.update_boss_kill(boss_name, new_killed_at)
                    await self.send_boss_update(boss_name, new_killed_at)

    @commands.Cog.listener()
    async def on_ready(self):
        self.update_boss_data.start()

    async def send_boss_update(self, boss_name, killed_at):
        killed_at = killed_at.replace(tzinfo=datetime.timezone.utc)
        embed = await self.create_kill_embed(boss_name, killed_at)

        for server in self.bot.guilds:
            print(f"Checking {server} for channel...")
            channel_id = await db_manager.get_channel(server.id)
            print(channel_id)
            channel = server.get_channel(int(channel_id))
            print(channel)
            if channel:
                print(f"Sending to {channel} in {server}")
                await channel.send(embed=embed)

    @commands.hybrid_command(
        name="lastkill",
        description="Reports last kill time for selected boss.",
    )
    async def report_last_kill(self, context: commands.Context, input_boss_name):
        try:
            boss_name, killed_at = await db_manager.get_single_boss_data(input_boss_name)
            killed_at = datetime.datetime.strptime(killed_at, '%Y-%m-%d %H:%M:%S.%f')

            embed = await self.create_kill_embed(boss_name, killed_at)

            await context.send(embed=embed)

        except TypeError:
            error = discord.Embed(
                description=f"Could not find {input_boss_name} please try a different name.",
                title="Error",
                color=0xcc0000
            )
            await context.send(embed=error, ephemeral=True)

    async def create_kill_embed(self, boss_name, killed_at):
        killed_at = killed_at.replace(tzinfo=datetime.timezone.utc)
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        delta = now - killed_at

        description_string = 'was killed'
        days, seconds = delta.days, delta.seconds
        hours = seconds // 3600
        print(hours)
        minutes = (seconds % 3600) // 60

        description_string += f' {hours} hour{"s" if hours > 1 else ""}' if hours > 0 else ''
        description_string += f' {minutes} minute{"s" if minutes > 1 else ""}' if minutes > 0 else ''
        description_string += ' ago.'

        update_embed = discord.Embed(
            description=description_string,
            title=boss_name,
            color=0x9C84EF
        )

        return update_embed

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
