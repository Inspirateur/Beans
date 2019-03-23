from discord.ext import commands
from discord import Colour
from role_manager import RL, RoleError
from math import pow, exp, factorial

bot = commands.Bot(command_prefix="!", description='At your service!')
SHINY_CHANCE = 0.00024414062


# ----- EVENTS -----
@bot.event
async def on_ready():
	print("Ready")


@bot.event
async def on_message(message):
	# print(message.content)
	if message.author != bot:
		await bot.process_commands(message)


# ----- ROLE MANAGEMENT -----
@bot.command(brief="- Zodiacs only: Set your elemental role", pass_context=True)
async def elem(ctx, *args):
	if len(args) != 1:
		await ctx.send("Type **!elem element** to set your elemental role!")
	else:
		zodiac = ctx.message.author
		guild = ctx.message.channel.guild
		elemname = args[0].title()
		try:
			# Return the role asked by the user, or raise an exception if the user can't have it
			role = RL.elem_command(elemname, zodiac, guild)
			# Get the elem role of the zodiac or None
			erole = RL.get_elem_from_member(zodiac)
			# If the zodiac has another elemental role it's removed
			if erole is not None:
				await zodiac.remove_roles(erole)
			# Finally the new elemental role is added to the zodiac
			await zodiac.add(role)
			await ctx.send("Alright! Your new elemental role has been set, be worthy of it! You can set its color with **!color hexcode**.")
		except RoleError as err:
			await ctx.send(err.message)


@bot.command(brief="- Zodiacs only: Set your elemental color", pass_context=True)
async def color(ctx, *args):
	if len(args) != 1:
		await ctx.send("Type **!color hexcode** to change your elemental role color!")
	else:
		hexcode = "0x"+args[0]
		zodiac = ctx.message.author
		try:
			# Get the elemental role if the color is correct
			elemrole = RL.color_command(hexcode, zodiac)
			newcol = Colour(int(hexcode, 16))
			await elemrole.edit(colour=newcol)
			await ctx.send("Great! Your new elemental color was set!")
		except RoleError as err:
			await ctx.send(err.message)


@bot.command(pass_context=True, hidden=True)
async def constitution(ctx):
	user_id = ctx.message.author.id
	if user_id == RL.get_chairman_id():
		with open("constitution.txt", "r", encoding="utf-8") as constitfile:
			await ctx.send(constitfile.read())


# The command is trusted to be used on Hunter only (there's no checking)
@bot.command(pass_context=True, hidden=True)
async def promote(ctx, *args):
	if ctx.message.author.id == RL.get_chairman_id():
		if len(args) != 1:
			await ctx.send("Chairman, have you forgotten to give me the Hunter id of the one that needed promotion?")
		else:
			try:
				hunter_id = int(RL.get_id_from_tag(args[0]))
				hunter = ctx.message.channel.guild.get_member(hunter_id)
				if hunter is None:
					await ctx.send("Chairman... I can't identify the Hunter you want to promote, maybe the ID is wrong ?")
				else:
					try:
						stars = RL.promote_command(hunter)
						name = await rename_command(hunter, hunter.display_name)
						await ctx.send(f"Ok! **{name}** is now a **{RL.get_starname(stars)}**!")
					except RoleError as err:
						await ctx.send(err.message)
			except ValueError:
				await ctx.send("This is not an ID, I can't promote him!")
	else:
		await ctx.send("Only the Chaiman of the Hunter Association can promote a Hunter.")


# The command is trusted to be used on Hunter only (there's no checking)
@bot.command(pass_context=True, hidden=True)
async def demote(ctx, *args):
	if ctx.message.author.id == RL.get_chairman_id():
		if len(args) != 1:
			await ctx.send("Chairman, I think you forgot to give me the ID of the Hunter that needed demotion.")
		else:
			try:
				hunter_id = int(RL.get_id_from_tag(args[0]))
				hunter = ctx.message.channel.guild.get_member(hunter_id)
				if hunter is None:
					await ctx.send("Chairman... I can't find the Hunter you want to demote, are you sure it's the good ID ?")
				else:
					try:
						stars = RL.demote_command(hunter)
						name = await rename_command(hunter, hunter.display_name)
						await ctx.send(f"**{name}** is now a **{RL.get_starname(stars)}**.")
					except RoleError as err:
						await ctx.send(err.message)
			except ValueError:
				await ctx.send("This is not an ID, I can't demote him!")
	else:
		await ctx.send("Only the Chaiman of the Hunter Association can demote a Hunter.")


async def rename_command(hunter, name):
	stars = RL.get_stars(hunter.id)
	bannedchar = "★☆⚝✩✪✫✬✭🟉🟊✮✯✰⭑⭒⭐🌟⋆*⍟🞯🞰🞱🞲🞳🞴⛤⛥⛦"
	for c in bannedchar:
		if c in name:
			name = name.replace(c, "")
	await hunter.edit(nick=f"{name} {stars*'★'}")
	return name


@bot.command(pass_context=True, brief="- To change your Hunter name")
async def rename(ctx, *args):
	if len(args) == 0:
		await ctx.send("I cannot rename you if you don't provide me the name.")
	else:
		name = " ".join(args)
		newname = await rename_command(ctx.message.author, name)
		await ctx.send(f"Ok! From now on your new Hunter name is {newname}.")


# ----- UTIL ------
def luckscale(s):
	if s <= 1:
		return ":scream:"
	elif s <= 15:
		return ":grin:"
	elif s <= 30:
		return ":grinning:"
	else:
		return ":slight_smile:"


def unluckscale(s):
	if s <= 1:
		return ":sob:"
	elif s <= 15:
		return ":cry:"
	elif s <= 30:
		return ":worried:"
	else:
		return ":slight_frown:"


@bot.command(pass_context=True, brief="shinies encounter - To calculate your luck")
async def shiny(ctx, *args):
	if len(args) != 2:
		await ctx.send("Type `!shiny shinies encounter`, to know if you were lucky or not. For exemple: !shiny 5 12500")
	else:
		try:
			shinies = int(args[0])
			try:
				encounter = int(args[1])
				if shinies <= encounter:
					prob = encounter*SHINY_CHANCE
					s = 0
					e = exp(-prob)
					for i in range(shinies+1):
						s += pow(prob, i)*e/factorial(i)
					exactprob = pow(prob, shinies)*e/factorial(shinies)
					# Sum represents the chance of having x shinies or less in y encounter
					if s >= 0.5:
						s = int((1 - s + exactprob)*10000)/100
						await ctx.send(f"{luckscale(s)} You had **{s}%** chance to encounter **{shinies}** shinies **or more** with **{encounter}** encounters!")
					else:
						s = int(s*10000)/100
						if shinies == 0:
							add = ""
						else:
							add = " **or less**"
						await ctx.send(f"{unluckscale(s)} You had **{s}%** chance to encounter **{shinies}** shinies{add} with **{encounter}** encounters!")
				else:
					await ctx.send("`!shiny shinies encounter` -> shinies can't be greater than encounter!")
			except ValueError:
				await ctx.send(f'`!shiny shinies encounter` -> encounter must be a **number** but you gave me "**{args[1]}**"')
		except ValueError:
			await ctx.send(f'`!shiny shinies encounter` -> shinies must be a **number** but you gave me "**{args[0]}**"')


# ----- EXECUTION -----
with open("token.txt", "r") as tfile:
	bot.run(tfile.read())
