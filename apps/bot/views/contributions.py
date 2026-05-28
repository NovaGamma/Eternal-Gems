import discord
from core.config import EVENT_POINTS_OPTIONS
from core.db.mongo import DB

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
        await interaction.response.defer()
        await interaction.followup.edit_message(
            interaction.message.id,
            content="RSN sync cancelled",
            view=None
        )
        self.stop()

class ConfirmModal(discord.ui.Modal, title="Confirm Points"):

    def __init__(
        self,
        parent_view,
        reason_default="",
        points_default=""
    ):
        super().__init__()

        self.parent_view = parent_view

        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="Why are you giving points?",
            required=True,
            default=reason_default,
            max_length=200
        )

        self.custom_points = discord.ui.TextInput(
            label="Custom points (optional)",
            placeholder="Only fill if no dropdown selected",
            required=False,
            default=points_default,
            max_length=10
        )

        self.add_item(self.reason)
        self.add_item(self.custom_points)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
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

    async def on_submit(self, interaction: discord.Interaction):

        points = self.parent_view.selected_points


        if points is None:
            if not self.custom_points.value.strip():
                await interaction.response.send_message(
                    "You must select points or enter custom points.",
                    ephemeral=True
                )
                # Reopen modal with preserved values
                await interaction.followup.send(
                    modal=ConfirmModal(
                        self.parent_view,
                        reason_default=self.reason.value,
                        points_default=self.custom_points.value
                    )
                )
                return
            try:
                points = int(self.custom_points.value)
            except ValueError:
                await interaction.response.send_message(
                    "Custom points must be a valid integer.",
                    ephemeral=True
                )
                return


        users = self.parent_view.selected_users

        names = ", ".join(
            user.display_name
            for user in users
        )

        reason = self.reason.value

        db = DB()
        for user in users:
            result = await db.add_contribution(user.id, points, 'bot', reason=reason, author=interaction.user.id)
            if not result:
                await interaction.response.send_message(
                    f"Error: couldn't find user for {user.display_name} in database"
                )
                continue

        await interaction.response.send_message(
            f"Added {points} points to {names}\n"
            f"by {interaction.user.mention}\n"
            f"Reason: {reason}",
        )

class UserPicker(discord.ui.UserSelect):

    def __init__(self):
        super().__init__(
            placeholder="Select users...",
            min_values=1,
            max_values=10
        )

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

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_users = self.values
        await interaction.response.defer()


class PointsSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=f"{pts} Points", value=pts) for pts in EVENT_POINTS_OPTIONS]
        options = [
            discord.SelectOption(label="1 Point", value="1"),
            discord.SelectOption(label="5 Points", value="5"),
            discord.SelectOption(label="10 Points", value="10"),
            discord.SelectOption(label="20 Points", value="20"),
        ]

        super().__init__(
            placeholder="Choose number of points...",
            min_values=1,
            max_values=1,
            options=options
        )
    
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

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_points = int(self.values[0])
        await interaction.response.edit_message(
            view=self.view
        )


class PointsView(discord.ui.View):

    def __init__(self, end_callback):
        super().__init__(timeout=60)

        self.selected_users = []
        self.selected_points = None

        self.add_item(UserPicker())
        self.add_item(PointsSelect())

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

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.green,
        row=4
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not self.selected_users:
            await interaction.response.send_message(
                "Please select at least one user first.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            ConfirmModal(self)
        )

        names = ", ".join(user.display_name for user in self.selected_users)

        

        await interaction.response.send_message(
            f"Gave {self.selected_points} points to: {names}",
            ephemeral=True
        )

