import discord
from discord.ext import commands
from core.services.contributions import *
from core.db.mongo import DB
from core.config import ALLOWED_ROLE_ID, ETERNAL_GEM_MEMBER_ROLE, RANKS, GUILD_ID

class ConfirmView(discord.ui.View):
    def __init__(self, author: discord.User, success_message, callback, **params):
        super().__init__(timeout=30)  # buttons expire after 30s
        self.value = None
        self.author = author
        self.callback = callback
        self.params = params
        self.success_message = success_message

    async def on_error(self, interaction: discord.Interaction, error: Exception, item):
        print("VIEW ERROR:", repr(error))

        try:
            if interaction.response.is_done():
                await interaction.followup.send(
                    f"Error: {error}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"Error: {error}",
                    ephemeral=True
                )
        except Exception as e:
            print("Failed to send error message:", e)

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.author['user_id']

    @discord.ui.button(label="Agree", style=discord.ButtonStyle.success)
    async def agree(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()

        await self.callback(**self.params)

        await interaction.followup.edit_message(
            interaction.message.id,
            content=self.success_message,
            view=None
        )
        self.stop()

    @discord.ui.button(label="Disagree", style=discord.ButtonStyle.danger)
    async def disagree(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.followup.edit_message(
            interaction.message.id,
            content="Stopping",
            view=None
        )
        self.stop()

class Contributions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_staff():
        def predicate(interaction: discord.Interaction) -> bool:
            if not any(role.id == ALLOWED_ROLE_ID for role in interaction.user.roles):
                return False
            return True
        return discord.app_commands.check(predicate)

    @discord.app_commands.command(name="givepoints")
    @discord.app_commands.describe(user="User to give points to", amount="Amount of points", reason="Reason")
    #@is_staff()
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def givepoints(self, interaction: discord.Interaction, user: discord.Member, amount: int, reason: str = ''):
        db = DB()
        await db.add_contribution(user.id, amount, 'bot', reason=reason, author=interaction.user.id)
        await interaction.response.send_message(
            f"Gave {amount} points to {user.id} by {interaction.user.id}\n reason: {reason}"
        )

    @discord.app_commands.command(name="init", description="initialize bot for the server")
    #@is_staff() ###TODO readd check once in production
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def init(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        db = DB()
        members = interaction.guild.members
        for member in members:
            # check that they have GEM role
            if not any(role.id == ETERNAL_GEM_MEMBER_ROLE for role in member.roles):
                print(f"skipping member {member.id}")
                continue
            
            print(f"add member {member.id}")
            try:
                await db.add_user(member.id)
            except Exception as e:
                print(f"Error {e}")
        await interaction.followup.send("Bot sucessfully initialized")

    @discord.app_commands.command(name="rank_up", description="Request rank-up if you fullfill the requirements")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def rank_up(self, interaction: discord.Interaction):
        user = interaction.user
        roles = user.roles
        if not any(role.id == ETERNAL_GEM_MEMBER_ROLE for role in roles):
            await interaction.response.send_message(
                "You are not currently a member of the clan.",
                ephemeral=True
            )
            return
        
        member_role_ids = {role.id for role in roles}
        for rank in RANKS:
            if rank["id"] in member_role_ids:
                current_rank = rank
                break
        next_rank_index = RANKS.index(current_rank) + 1
        next_rank = RANKS[next_rank_index] if len(RANKS) > next_rank_index else None
        if not next_rank:
            await interaction.response.send_message(
                "You are already at the maximum rank.",
                ephemeral=True
            )
            return

        db = DB()
        db_user = await db.get_user(user.id)
        if db_user['contribution'] < next_rank['requirement']:
            await interaction.response.send_message(
                f"You don't have enough contribution to rank up, you currently have {db_user['contribution']} and need {next_rank['requirement']}",
                ephemeral=True
            )
            return
        ### TODO add check for time between last rank-up

        guild = interaction.guild
        await user.add_roles(guild.get_role(next_rank['id']))
        await user.remove_roles(guild.get_role(current_rank['id']))

        await db.logger(db_user['user_id'], 'rank_up', details={'source': 'bot', 'new_rank': next_rank})

        await interaction.response.send_message(
            f"You have successfully been ranked up to {next_rank['name']} Grats",
            ephemeral=True
        )

    @discord.app_commands.command(name="sync_rsn", description="Sync your RSN to your discord to get contribution from talking in the clan chat")
    @discord.app_commands.describe(rsn="Your runescape name")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def sync(self, interaction: discord.Interaction, rsn: str):
        user = interaction.user
        roles = user.roles
        if not any(role.id == ETERNAL_GEM_MEMBER_ROLE for role in roles):
            await interaction.response.send_message(
                "You are not currently a member of the clan.",
                ephemeral=True
            )
            return
        
        db = DB()
        user = await db.get_user(user.id)
        if user['rsn']:
            view = ConfirmView(user,
                            success_message=f"Successfully synced rsn: {rsn}",
                            callback=db.sync_rsn,
                            user=user,
                            rsn=rsn)

            await interaction.response.send_message(
                f"You already have a RSN synced, replace {user['rsn']} by {rsn} ?",
                view=view
            )

            await view.wait()
        else:
            await db.sync_rsn(user, rsn)
            await interaction.response.send_message(
                f"Successfully synced rsn: {rsn}"
            )

    @discord.app_commands.command(name="getlogs", description="Get the logs of the user")
    @discord.app_commands.describe(user="User to get the logs for")
    #@is_staff()
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def getlogs(self, interaction: discord.Interaction, user: discord.Member):
        db = DB()
        db_user = await db.get_user(user)
        logs = await db.get_logs(db_user)

        logs_count = logs['total']
        message = f"Displaying logs for {user.name} page: {logs['page']}/{logs['total_pages']}\n```"

        for log in logs['logs']:
            message += ' '.join([f"{key}: {value}" for key, value in log.items() if key not in ['_id', 'user_id']]) + '\n'

        message += '```'
        await interaction.response.send_message(
            message
        )


async def setup(bot):
    await bot.add_cog(Contributions(bot))