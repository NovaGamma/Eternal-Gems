import discord
from discord.ext import commands
from core.config import GUILD_ID, STAFF_ROLES
from core.utils.utils import is_staff
from core.services.mod_mail import close_ticket, create_modmail_ticket, send_user_message, staff_message_ticket, send_staff_message, user_message_ticket

class ModMail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def staff_mention(self, guild: discord.Guild):
        roles = []
        for role_id in STAFF_ROLES:
            try:
                role = await guild.fetch_role(role_id)
                roles.append(role.mention)
            except discord.NotFound:
                # in case role is deleted but not removed from config
                pass

        return ' '.join(roles)

    @discord.app_commands.command(name="createticket", description="create channel for anonymous messaging to a user")
    @discord.app_commands.describe(user="User to create ticket for")
    #@is_staff()
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def createTicket(self, interaction: discord.Interaction, user: discord.Member):
        channel_category = interaction.channel.category
        staff_channel = await channel_category.create_text_channel(f'ModMail_{user.name}_staff_side')
        await create_modmail_ticket(staff_channel.id, user, interaction.guild_id)
        mention = await self.staff_mention(interaction.guild)
        await staff_channel.send(f"Created Staff channel for anonymous messaging to {user.mention}\n {mention}")
        await interaction.response.send_message(f'ticket opened {staff_channel.jump_url}')

    @discord.app_commands.command(name="closeticket", description="close ticket")
    #@is_staff()
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def closeTicket(self, interaction: discord.Interaction):
        if not await staff_message_ticket(interaction.channel):
            await interaction.response.send_message('command cannot be used outside of a ticket channel')
        await close_ticket(interaction, self.bot)

    @commands.command(name="send")
    async def send(self, ctx, *message):
        print('in command logic')
        # ignore command if not in a channel for an opened ticket
        if not await staff_message_ticket(ctx.channel):
            print('not in ticket')
            return
        # since using normal command, if message is sent it would be split in a list of args
        print('after check')
        message = ' '.join(message)
        await send_staff_message(ctx, message)

    @commands.Cog.listener('on_message')
    async def handle_message(self, message):
        ticket = await user_message_ticket(message.author.id)
        if not ticket:
            print('in event logic')
            return

        await send_user_message(message, self.bot)


async def setup(bot):
    await bot.add_cog(ModMail(bot))