import sqlite3


class RoleError(Exception):
	def __init__(self, message):
		self.message = message


class RL:
	conn = sqlite3.connect("ranks.db")

	@staticmethod
	def get_elem_ids():
		c = RL.conn.cursor()
		c.execute('SELECT id FROM Elems')
		_elem_ids = c.fetchall()
		c.close()
		return [_elem[0] for _elem in _elem_ids]

	@staticmethod
	def get_elem_names():
		c = RL.conn.cursor()
		c.execute('SELECT name FROM Elems')
		_elem_names = c.fetchall()
		c.close()
		return [_elem[0] for _elem in _elem_names]

	@staticmethod
	def get_zodiac_id():
		c = RL.conn.cursor()
		c.execute('SELECT id FROM Roles WHERE name="Zodiac"')
		zodiac_id = c.fetchone()
		c.close()
		return zodiac_id[0]

	@staticmethod
	def get_chairman_id():
		c = RL.conn.cursor()
		c.execute('SELECT id FROM Roles WHERE name="Chairman"')
		chairman_id = c.fetchone()
		c.close()
		return chairman_id[0]

	@staticmethod
	def get_stars(hunter_id):
		c = RL.conn.cursor()
		c.execute('SELECT starcount FROM Stars WHERE user_id=?', (hunter_id, ))
		stars = c.fetchone()
		c.close()
		if stars is None:
			return 0
		return stars[0]

	@staticmethod
	def set_stars(hunter_id, starcount):
		c = RL.conn.cursor()
		c.execute('UPDATE Stars SET starcount=? WHERE user_id=?', (starcount, hunter_id))
		RL.conn.commit()
		c.close()

	@staticmethod
	def get_elem_from_member(member):
		c = RL.conn.cursor()
		for role in member.roles:
			c.execute('SELECT * FROM Elems WHERE id=?', (role.id, ))
			if c.fetchone() is not None:
				c.close()
				return role
		c.close()
		return None

	@staticmethod
	def get_all_elems(guild):
		elem_ids = RL.get_elem_ids()
		elem_roles = {}
		for role in guild.roles:
			if role.id in elem_ids:
				elem_roles[role.name] = role

		return elem_roles

	@staticmethod
	def get_free_elems(guild):
		taken_elems = {}
		elem_roles = RL.get_all_elems(guild)
		for member in guild.members:
			erole = RL.get_elem_from_member(member)
			if erole is not None:
				taken_elems[erole.name] = erole

		elems = RL.get_elem_names()
		free_elems = {}
		for elem in elems:
			if elem not in taken_elems:
				free_elems[elem] = elem_roles[elem]
		return free_elems

	# TODO: fix ça apres putain
	@staticmethod
	def elem_command(elemname, zodiac, guild):
		zodiac_id = RL.get_zodiac_id()
		zrole = None
		for role in zodiac.roles:
			if role.id == zodiac_id:
				zrole = role
				break

		elems = RL.get_elem_names()
		if zrole is not None:
			free_elems = RL.get_free_elems(guild)
			if elemname in elems:
				if elemname in free_elems.keys():
					return free_elems[elemname]
				else:
					# arg is an already taken elem role
					raise RoleError(
									f"Oops, I'm afraid the elemental role **{elemname}** is already taken!\n"
									f"Here is the list of the free elemental roles:\n"
									f"**{'**, **'.join(free_elems.keys())}**")
			else:
				# arg is not an elem role
				raise RoleError(
								f"Ahem, **{elemname}** is not an elemental role.\n"
								f"Let me write you the list of the free elemental roles:\n"
								f"**{'**, **'.join(free_elems.keys())}**")
		else:
			# user is not a zodiac
			raise RoleError(f"Given your Hunter license I can see you are not a Zodiac sir. Only Zodiacs can have an elemental role.")

	@staticmethod
	def color_command(color, zodiac):
		# Check if the command user is a zodiac
		zodiac_id = RL.get_zodiac_id()
		elems_id = RL.get_elem_ids()
		zrole = None
		erole = None
		for role in zodiac.roles:
			if role.id == zodiac_id:
				zrole = role
				if erole is not None:
					break
			elif role.id in elems_id:
				erole = role
				if zrole is not None:
					break
		# Check if the user is a zodiac
		if zrole is not None:
				# Check if he has an elemental role
				if erole is not None:
					# Get the hex color
					try:
						hexcode = int(color, 16)
						if 0x000000 <= hexcode <= 0xFFFFFF:
							return erole
						else:
							raise RoleError(f"A proper color hex code should be 6 digits long, but **\"{color}\"** is not so I can't use it.")
					except ValueError:
						raise RoleError(f"**\"{color}\"** isn't a hex code!")
				else:
					raise RoleError(
								"Uh-oh, you're indeed a Zodiac but you don't have an elemental role!"
								" I know administrative stuff is boring you but please take your job seriously.\n"
								"You can use **!elem typename** to get your elemental role if it's not taken!")
		else:
			raise RoleError("I'm sorry but only Zodiac members have an elemental role, you can't set its color since you don't have one...")

	@staticmethod
	def promote_command(hunter):
		stars = RL.get_stars(hunter.id)
		if stars < 3:
			stars += 1
		else:
			raise RoleError(f"Hem, Chairman you must be sleeping! {hunter.display_name} has 3 stars already he can't be promoted!")
		RL.set_stars(hunter.id, stars)
		return stars

	@staticmethod
	def demote_command(hunter):
		stars = RL.get_stars(hunter.id)
		if stars > 0:
			stars -= 1
			RL.set_stars(hunter.id, stars)
		else:
			raise RoleError(f"Is it a joke? Chairman you can't demote a Hunter that has 0 stars ...")
		return stars

	@staticmethod
	def get_starname(star_count):
		if star_count == 0:
			return "0 Star Hunter"
		elif star_count == 1:
			return "Single Star Hunter"
		elif star_count == 2:
			return "Double Star Hunter"
		elif star_count == 3:
			return "Triple Star Hunter"

	@staticmethod
	def get_id_from_tag(tag):
		return ''.join(filter(lambda x: x.isdigit(), tag))
