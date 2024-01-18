import os
import json
from typing import Dict, List, Union
import traceback

import emoji
import discord
from discord.ext import commands

from botutils import *

class ReactionRole():
    def __init__(self, master, name):
        self.master: ReactionRolesMaster = master
        self.guild: discord.Guild = self.master.guild
        self.path: str = f"guilds/guild_{self.guild.id}/reactionroles/{name}.json"
        self.rolemaps: Dict[str, int] = self.load()

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding = "utf-8") as file:
                data = json.loads(file.read())
            return data
        else:
            return {"null": 0}

    def save(self):
        with open(self.path, "w", encoding = "utf-8") as file:
            file.write(json.dumps(self.rolemaps))

    def add(self, emoji: str, role_id: int):
        self.rolemaps[emoji] = role_id
        self.save()

    def delete(self, emoji: str):
        try:
            del self.rolemaps[emoji]
            self.save()
            return True
        except:
            return False

    def checks(self, emoji: str):
        return self.rolemaps.get(emoji, 0)

class ReactionRolesMaster():
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        self.guild_path = f"guilds/guild_{self.guild.id}/"
        if not os.path.exists(self.guild_path + "reactionroles"):
            os.makedirs(self.guild_path + "reactionroles")
        self.reactionroles = self.load()
        with open(f"guilds/guild_{self.guild.id}/reaction_roles.json", "r", encoding = "utf-8") as file:
            raw = json.loads(file.read())
        self.raw = raw

    def load(self) -> Dict[int, ReactionRole]:
        try:
            with open(f"guilds/guild_{self.guild.id}/reaction_roles.json", "r", encoding = "utf-8") as file:
                data: Dict[str, Dict[str, str]] = json.loads(file.read())
        except:

            with open(f"guilds/guild_{self.guild.id}/reaction_roles.json", "w", encoding = "utf-8") as file:
                file.write(json.dumps({"messages": {}}))
            data = {"messages": {}}
        reactionroles: Dict[int, ReactionRole] = {}
        for message_id, reactionrole in data["messages"].items():
            reactionroles[int(message_id)] = ReactionRole(self, reactionrole)
        return reactionroles

    def update(self):
        with open(f"guilds/guild_{self.guild.id}/reaction_roles.json", "w", encoding = "utf-8") as file:
            file.write(json.dumps(self.raw))

    def add(self, message_id: int, name: str):
        reactionrole = ReactionRole(self, name)
        self.raw["messages"][str(message_id)] = name
        self.reactionroles[message_id] = reactionrole
        self.update()
        return reactionrole

    def get(self, message_id: int) -> ReactionRole:
        return self.reactionroles[message_id]

    def checks(self, reaction: discord.RawReactionActionEvent):
        if reaction.message_id not in self.reactionroles:
            return 0
        if reaction.emoji.is_custom_emoji():
            return 0
        reactionrole = self.reactionroles[reaction.message_id]
        #role_id = reactionrole.checks(str(reaction.emoji.id) if reaction.is_custom_emoji() else reaction.emoji)
        role_id = reactionrole.checks(reaction.emoji)
        return role_id

class ReactionRolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        pass

    @commands.Cog.listener("on_raw_reaction_add")
    @commands.Cog.listener("on_raw_reaction_remove")
    async def on_raw_reaction_add_remove(self, payload: discord.RawReactionActionEvent):
        try:
            if payload.guild_id is None:
                return
            guild = self.bot.get_guild(payload.guild_id)
            roles = ReactionRolesMaster(guild)
            role_id = roles.checks(payload)
            if role_id == 0:
                return
            role = guild.get_role(role_id)
            member = guild.get_member(payload.user_id)
            #if payload.event_type == "REACTION_ADD":
            await member.add_roles(role)
            #else:
            #    await member.remove_roles(role)
        except Exception as e:
            traceback.print_exception(e)
    
    @commands.hybrid_command(name = "add_reaction_role_message")
    async def add_reaction_role_message(self, ctx: commands.Context, message_id: int, name: str, reaction: str, role: discord.Role):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)

        if not ctx.guild:
            return await command_not_used_in_guild(ctx)
        if not ctx.author.guild_permissions.manage_roles and not ctx.author.guild_permissions.manage_guild:
            if not ctx.author.id == self.bot.owner().id:
                return await insuf_perms(ctx, "manage_roles, manage_guild")

        if not emoji.is_emoji(reaction):
            return await ctx.send("This is not an emoji! (Please note that you cannot use custom emojis yet.)")

        guildroles = ReactionRolesMaster(ctx.guild)
        reactionrole: ReactionRole = guildroles.add(message_id, name)

        reactionrole.add(reaction, role.id)

        message = await ctx.channel.fetch_message(message_id)
        await message.add_reaction(reaction)
    
    @commands.hybrid_command(name = "add_reaction_role_to_message")
    async def add_reaction_role_to_message(self, ctx: commands.Context, message_id: int, reaction: str, role: discord.Role):
        update_total_commands_stat()
        await self.bot.do_log(f"User {ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id}) used command {ctx.command.name} in channel {ctx.channel.id}", ctx.guild.id if ctx.guild else None, ctx)

        if not ctx.guild:
            return await command_not_used_in_guild(ctx)
        if not ctx.author.guild_permissions.manage_roles and not ctx.author.guild_permissions.manage_guild:
            if not ctx.author.id == self.bot.owner().id:
                return await insuf_perms(ctx, "manage_roles, manage_guild")

        if not emoji.is_emoji(reaction):
            return await ctx.send("This is not an emoji! (Please note that you cannot use custom emojis yet.)")

        guildroles = ReactionRolesMaster(ctx.guild)
        reactionrole: ReactionRole = guildroles.get(message_id)

        reactionrole.add(reaction, role.id)

        message = await ctx.channel.fetch_message(message_id)
        await message.add_reaction(reaction)
        
