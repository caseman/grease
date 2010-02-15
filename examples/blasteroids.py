"""Basic vector graphics arcade game built with Grease"""

import os
import math
import random
import itertools
import pyglet
from pyglet import gl
from pyglet.window import key
import grease
from grease import component, controller, geometry, collision, renderer
from grease.pygletsys import KeyControls

window = pyglet.window.Window()
window.clear()


## Create and configure the game world ##

world = grease.World(window)
world.components.map(
	position=component.Position(),
	movement=component.Movement(),
	shape=component.Shape(),
	renderable=component.Renderable(),
	collision=component.Collision(),
	# Custom components
	player=component.Component(thrust_accel=float, turn_rate=float, invincible=int),
	gun=component.Component(firing=bool, last_fire_time=float, cool_down=float, sound=object),
	award=component.Component(points=int),
)
world.systems.add(
	('movement', controller.EulerMovement()),
	('collision', collision.Circular(handlers=[collision.dispatch_events])),
)

## Helper functions ##

def load_sound(name, streaming=False):
	return pyglet.media.load(
		'%s/sfx/%s' % (os.path.dirname(__file__), name), streaming=streaming)

def looping_sound(name):
	player = pyglet.media.Player()
	player.queue(load_sound(name, streaming=True))
	player.eos_action = player.EOS_LOOP
	return player

## Define entity classes ##

class BlasteroidsEntity(grease.Entity):
	"""Entity base class"""

	def explode(self):
		"""Segment the entity shape into itty bits"""
		shape = self.shape.verts.transform(angle=self.position.angle)
		for segment in shape.segments():
			debris = world.Debris()
			debris.shape.verts = segment
			debris.position.position = self.position.position
			debris.movement.velocity = self.movement.velocity
			debris.movement.velocity += segment[0].normalized() * random.gauss(50, 20)
			debris.movement.rotation = random.gauss(0, 45)
			debris.renderable.color = self.renderable.color


class Debris(BlasteroidsEntity):
	"""Floating space junk"""


class PlayerShip(BlasteroidsEntity):
	"""Thrust ship piloted by the player"""

	SHAPE_VERTS = [
		(-8, -12), (-4, -10), (0, -8), (4, -10), (8, -12), # flame
		(0, 12), (-8, -12), (0, -8), (8, -12)]
	COLOR = (0.5, 1, 0.5)
	GUN_COOL_DOWN = 0.5
	GUN_SOUND = load_sound('pewpew.wav')
	THRUST_SOUND = looping_sound('thrust.wav')
	DEATH_SOUND = load_sound('dead.wav')
	COLLISION_RADIUS = 7.5
	COLLIDE_INTO_MASK = 0x1

	def __init__(self):
		self.player.thrust_accel = 75
		self.player.turn_rate = 240
		self.player.invincible = 0
		self.gun.cool_down = self.GUN_COOL_DOWN
		self.gun.sound = self.GUN_SOUND
		self.shape.verts = self.SHAPE_VERTS
		self.shape.closed = False
		self.collision.radius = 7.5
		self.collision.into_mask = self.COLLIDE_INTO_MASK
		self.reset()
	
	def blink(self, dt):
		"""Blink the ship to show invincbility"""
		self.player.invincible += 1
		if self.player.invincible > 12:
			self.player.invincible = 0
			self.renderable.color = self.COLOR
			self.collision.from_mask = 0xffffffff
			self.collision.into_mask = self.COLLIDE_INTO_MASK
			pyglet.clock.unschedule(self.blink)
		elif self.player.invincible % 2 == 0:
			del self.renderable
		else:
			self.renderable.color = self.COLOR
	
	def reset(self, dt=None):
		"""Reset player ship for new life"""
		self.position.position = (0, 0)
		self.position.angle = 0
		self.movement.velocity = (0, 0)
		self.movement.rotation = 0
		self.renderable.color = self.COLOR
		self.gun.firing = False
		self.gun.last_fire_time = 0
	
	def respawn(self, dt=None):
		"""Rise to fly again, with temporary invincibility"""
		self.player.invincible = 1
		self.reset()
		pyglet.clock.schedule_interval(self.blink, 0.3)
	
	def on_collide(self, other, point, normal):
		if not self.player.invincible:
			self.explode()
			self.DEATH_SOUND.play()
			self.collision.from_mask = 0
			self.collision.into_mask = 0
			del self.renderable
			world.systems.game.player_died()


class Asteroid(BlasteroidsEntity):
	"""Big floating space rock"""

	COLLIDE_INTO_MASK = 0x2
	HIT_SOUNDS = [
		load_sound('hit1.wav'),
		load_sound('hit2.wav'),
		load_sound('hit3.wav'),
	]

	UNIT_CIRCLE = [(math.sin(math.radians(a)), math.cos(math.radians(a))) 
		for a in range(0, 360, 18)]
	
	def __init__(self, radius=45, position=None, points=25):
		if position is None:
			self.position.position = (
				random.choice([-1, 1]) * random.randint(50, window.width / 2), 
				random.choice([-1, 1]) * random.randint(50, window.height / 2))
		else:
			self.position.position = position
		deviation = radius / 7
		self.movement.velocity = (random.gauss(0, 600 / radius), random.gauss(0, 700 / radius))
		self.movement.rotation = random.gauss(0, 15)
		verts = [(random.gauss(x*radius, deviation), random.gauss(y*radius, deviation))
			for x, y in self.UNIT_CIRCLE]
		self.shape.verts = verts
		self.collision.radius = radius
		self.collision.from_mask = PlayerShip.COLLIDE_INTO_MASK
		self.collision.into_mask = self.COLLIDE_INTO_MASK
		self.renderable.color = (0.75, 0.75, 0.75)
		self.award.points = points

	def on_collide(self, other, point, normal):
		if self.collision.radius > 15:
			chunk_size = self.collision.radius / 2.0
			for i in range(2):
				world.Asteroid(chunk_size, self.position.position, self.award.points * 2)
		random.choice(self.HIT_SOUNDS).play()
		self.explode()
		self.delete()	


class Shot(grease.Entity):
	"""Pew Pew!
	
	Args:
		`shooter` (Entity): entity that is shooting the shot. Used
		to determine the collision mask, position and velocity 
		so the shot doesn't hit the shooter.
		
		`angle` (float): Angle of the shot trajectory in degrees.
	"""

	SPEED = 300
	TIME_TO_LIVE = 0.75 # seconds
	
	def __init__(self, shooter, angle):
		offset = geometry.Vec2d(0, shooter.collision.radius)
		offset.rotate(angle)
		self.position.position = shooter.position.position + offset
		self.movement.velocity = (
			offset.normalized() * self.SPEED + shooter.movement.velocity)
		self.shape.verts = [(0, 1.5), (1.5, -1.5), (-1.5, -1.5)]
		self.collision.radius = 2.0
		self.collision.from_mask = ~shooter.collision.into_mask
		self.renderable.color = (1.0, 1.0, 1.0)
		pyglet.clock.schedule_once(self.expire, self.TIME_TO_LIVE)

	def on_collide(self, other, point, normal):
		world.systems.game.award_points(other)
		self.delete()
	
	def expire(self, dt):
		self.delete()

class HudEntity(grease.Entity):
	"""Entities used by the HUD"""


## Define game systems ##

class PositionWrapper(object):
	"""Wrap positions around when they go off the edge of the window"""

	MARGIN = 60
	HALF_WIDTH = window.width / 2 + MARGIN
	HALF_HEIGHT = window.height / 2 + MARGIN

	def step(self, dt):
		for entity in world.Entity.position.position.x < -self.HALF_WIDTH:
			entity.position.position.x += window.width + self.MARGIN * 2
		for entity in world.Entity.position.position.x > self.HALF_WIDTH:
			entity.position.position.x -= window.width + self.MARGIN * 2
		for entity in world.Entity.position.position.y < -self.HALF_HEIGHT:
			entity.position.position.y += window.height + self.MARGIN * 2
		for entity in world.Entity.position.position.y > self.HALF_HEIGHT:
			entity.position.position.y -= window.height + self.MARGIN * 2


class Gun(object):
	"""Fires Shot entities"""

	def step(self, dt):
		for entity in world.Entity.gun.firing == True:
			if world.time >= entity.gun.last_fire_time + entity.gun.cool_down:
				world.Shot(entity, entity.position.angle)
				if entity.gun.sound is not None:
					entity.gun.sound.play()
				entity.gun.last_fire_time = world.time


class Sweeper(object):
	"""Clears out space debris"""

	SWEEP_TIME = 2.0

	def step(self, dt):
		fade = dt / self.SWEEP_TIME
		for entity in tuple(world.Debris.entities):
			color = entity.renderable.color
			if color.a > 0.2:
				color.a = max(color.a - fade, 0)
			else:
				entity.delete()


class Game(KeyControls):
	"""Main game logic system

	This subclass KeyControls so that the controls can be bound
	directly to the game logic here
	"""

	CHIME_SOUNDS = [
		load_sound('chime1.wav'), 
		load_sound('chime2.wav'),
	]
	MAX_CHIME_TIME = 2.0
	MIN_CHIME_TIME = 0.6

	def __init__(self):
		KeyControls.__init__(self)
		self.level = 0
		self.lives = 3
		self.score = 0
		self.player_ship = world.PlayerShip()
		self.start_level()
	
	def start_level(self):
		self.level += 1
		for i in range(self.level * 3 + 1):
			world.Asteroid()
		self.chime_time = self.MAX_CHIME_TIME
		self.chimes = itertools.cycle(self.CHIME_SOUNDS)
		if self.level == 1:
			self.chime()
	
	def award_points(self, entity):
		"""Get points for destroying stuff"""
		if hasattr(entity.award, 'points'):
			self.score += entity.award.points
	
	def player_died(self):
		self.lives -= 1
		if self.lives:
			pyglet.clock.schedule_once(self.player_ship.respawn, 3.0)

	def chime(self, dt=0):
		"""Play tension building chime sounds"""
		if world.running and self.lives:
			self.chimes.next().play()
			self.chime_time = max(self.chime_time - dt * 0.01, self.MIN_CHIME_TIME)
			if not world.Asteroid.entities:
				self.start_level()
		pyglet.clock.schedule_once(self.chime, self.chime_time)
	
	@KeyControls.key_press(key.LEFT)
	@KeyControls.key_press(key.A)
	def start_turn_left(self):
		self.player_ship.movement.rotation = -self.player_ship.player.turn_rate

	@KeyControls.key_release(key.LEFT)
	@KeyControls.key_release(key.A)
	def stop_turn_left(self):
		if self.player_ship.movement.rotation < 0:
			self.player_ship.movement.rotation = 0

	@KeyControls.key_press(key.RIGHT)
	@KeyControls.key_press(key.D)
	def start_turn_left(self):
		self.player_ship.movement.rotation = self.player_ship.player.turn_rate

	@KeyControls.key_release(key.RIGHT)
	@KeyControls.key_release(key.D)
	def stop_turn_left(self):
		if self.player_ship.movement.rotation > 0:
			self.player_ship.movement.rotation = 0
	
	@KeyControls.key_hold(key.UP)
	@KeyControls.key_hold(key.W)
	def thrust(self, dt):
		thrust_vec = geometry.Vec2d(0, self.player_ship.player.thrust_accel)
		thrust_vec.rotate(self.player_ship.position.angle)
		self.player_ship.movement.accel = thrust_vec
		self.player_ship.shape.verts[2] = geometry.Vec2d(0, -16 - random.random() * 16)
		self.player_ship.THRUST_SOUND.play()
	
	@KeyControls.key_release(key.UP)
	@KeyControls.key_release(key.W)
	def stop_thrust(self):
		self.player_ship.movement.accel = geometry.Vec2d(0, 0)
		self.player_ship.shape.verts[2] = geometry.Vec2d(0, -8)
		self.player_ship.THRUST_SOUND.pause()

	@KeyControls.key_press(key.SPACE)
	def start_firing(self):
		self.player_ship.gun.firing = True

	@KeyControls.key_release(key.SPACE)
	def stop_firing(self):
		self.player_ship.gun.firing = False
	
	@KeyControls.key_press(key.P)
	def pause(self):
		if self.world.running:
			self.world.stop()
		else:
			self.world.start()


class Hud(object):
	"""Heads-up display renderer"""
	
	pyglet.font.add_file(os.path.dirname(__file__) + '/font/Vectorb.ttf')
	HUD_FONT = pyglet.font.load('Vector Battle')

	def __init__(self):
		self.last_lives = 0
		self.last_score = None
		self.game_over_label = None
		self.create_lives_entities()

	def draw(self):
		game = world.systems.game
		if self.last_lives != game.lives:
			for i, entity in self.lives:
				if game.lives > i:
					entity.renderable.color = (0.8,0.8,0.8)
				else:
					entity.renderable.color = (0,0,0,0)
			self.last_lives = game.lives
		if self.last_score != game.score:
			self.score_label = pyglet.text.Label(
				str(game.score),
				font_name='Vector Battle', font_size=14, bold=True,
				x=window.width // 2 - 25, y=window.height // 2 - 25, 
				anchor_x='right', anchor_y='center')
			self.last_score = game.score
		if game.lives == 0:
			if self.game_over_label is None:
				self.game_over_label = pyglet.text.Label(
					"GAME OVER",
					font_name='Vector Battle', font_size=36,
					x = 0, y = 0, anchor_x='center', anchor_y='center')
			self.game_over_label.draw()
		self.score_label.draw()
	
	def create_lives_entities(self):
		"""Create entities to represent the remaining lives"""
		self.lives = []
		verts = geometry.Vec2dArray(PlayerShip.SHAPE_VERTS[3:])
		left = -window.width // 2 + 25
		top = window.height // 2 - 25
		for i in range(20):
			entity = world.HudEntity()
			entity.shape.verts = verts.transform(scale=0.75)
			entity.position.position = (i * 20 + left, top)
			self.lives.append((i, entity))


world.systems.add(
	('wrapper', PositionWrapper()),
	('gun', Gun()),
	('sweeper', Sweeper()),
	('game', Game()),
)
world.renderers = (
	renderer.Camera(position=(window.width / 2, window.height / 2)),
	renderer.Vector(line_width=1.5),
	Hud(),
)
pyglet.app.run()

