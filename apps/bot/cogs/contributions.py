import discord
from discord.ext import commands
from core.services.contributions import *
from core.db.mongo import DB
from core.config import ETERNAL_GEM_MEMBER_ROLE, RANKS, GUILD_ID, TO_BE_RANKED
from core.utils.utils import is_staff
from apps.bot.views.contributions import ConfirmView, PointsView
import re


class Contributions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="givepoints")
    @discord.app_commands.describe(user="User to give points to", amount="Amount of points", reason="Reason")
    #@is_staff()
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def givepoints(self, interaction: discord.Interaction,
                         user: discord.Member,
                         amount: discord.app_commands.Range[int, 1],
                         reason: str = ''):
        db = DB()
        result = await db.add_contribution(user.id, amount, 'bot', reason=reason, author=interaction.user.id)
        if not result:
            await interaction.response.send_message(
                f"Error: couldn't find user in database"
            )
            return
        await interaction.response.send_message(
            f"Gave {amount} points to {user.mention} by {interaction.user.mention}\n reason: {reason}"
        )

    @discord.app_commands.command(name="givebulkpoints")
    #@is_staff()
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def givebulkpoints(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Choose users from the menu below:",
            view=PointsView(print),
            ephemeral=True
        )
        #db = DB()
        #for user in users:
        #    result = await db.add_contribution(user.id, amount, 'bot', reason=reason, author=interaction.user.id)
        #    if not result:
        #        await interaction.response.send_message(
        #            f"Error: couldn't find user in database"
        #        )
        #        continue
        #    await interaction.response.send_message(
        #        f"Gave {amount} points to {user.mention} by {interaction.user.mention}\n reason: {reason}"
        #    )

    @discord.app_commands.command(name="init", description="initialize bot for the server")
    #@is_staff() ###TODO readd check once in production
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def init(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

        failure = skipped = success = 0
        db = DB()
        members = interaction.guild.members
        for member in members:
            # check that they have GEM role
            if not any(role.id == ETERNAL_GEM_MEMBER_ROLE for role in member.roles):
                print(f"skipping member {member.id}")
                skipped +=1
                continue
            
            print(f"add member {member.id}")
            try:
                await db.add_user(member.id)
                success += 1
            except Exception as e:
                failure += 1
                print(f"Error {e}")
        await interaction.followup.send(f"Bot sucessfully initialized: success {success} skipped {skipped} failure {failure}")

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
        try:
            await user.add_roles(guild.get_role(next_rank['id']))
            await user.remove_roles(guild.get_role(current_rank['id']))
        except:
            db.logger(user.id, 'error', {'role_assignment': next_rank['name'], 'source': 'rank_up'})

        await db.logger(db_user['user_id'], 'rank_up', details={'source': 'bot', 'new_rank': next_rank, 'old_rank': current_rank})

        to_be_ranked = interaction.guild.get_channel(TO_BE_RANKED)
        await to_be_ranked.send(f"{user.mention} to {next_rank['name']}")

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
        
        pattern = r'^[A-Za-z0-9 -]{1,12}$'
        if not bool(re.fullmatch(pattern, rsn)):
            await interaction.response.send_message(
                "Invalid RSN provided",
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

        message = f"Displaying logs for {user.name} page: {logs['page']}/{logs['total_pages']}\n```"

        for log in logs['logs']:
            message += ' '.join([f"{key}: {value}" for key, value in log.items() if key not in ['_id', 'user_id']]) + '\n'

        message += '```'
        await interaction.response.send_message(
            message
        )

    @commands.Cog.listener('on_member_update')
    async def handle_member_update(self, before, after):
        if ETERNAL_GEM_MEMBER_ROLE not in [role.id for role in before.roles] and ETERNAL_GEM_MEMBER_ROLE in [role.id for role in after.roles]:
            db = DB()
            user = after
            # check that user doesn't already exist is in the add_user function
            await db.add_user(user.id)
            db_user = await db.get_user(user.id)
            # new member
            print(db_user)
            if db_user['contribution'] == 0:
                return
            
            #give back old member their role
            for i, rank in enumerate(RANKS):
                print(i, rank)
                if db_user['contribution'] < rank['requirement']:
                    print(rank)
                    i -= 1
                    break

            current_rank = RANKS[i] if i > 0 else None
            if current_rank:            
                guild = user.guild
                try:
                    print(current_rank)
                    await user.add_roles(guild.get_role(current_rank['id']))
                    await user.remove_roles(guild.get_role(RANKS[0]['id']))
                except:
                    db.logger(user.id, 'error', {'role_assignment': current_rank['name'], 'source': 'on_member_rejoin'})

async def setup(bot):
    await bot.add_cog(Contributions(bot))