"""Basic vector graphics arcade game built with Grease"""

import math
import random
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
	player=component.Component(thrust_accel=float, turn_rate=float),
	gun=component.Component(firing=bool, last_fire_time=float, cool_down=float),
)
world.systems.add(
	('movement', controller.EulerMovement()),
	('collision', collision.Circular(handlers=[collision.dispatch_events])),
)
world.renderers = (
	renderer.Camera(position=(window.width / 2, window.height / 2)),
	renderer.Vector(line_width=1.5),
)


## Define entity classes ##

class PlayerShip(grease.Entity):
	"""Thrust ship piloted by the player"""

	COLLIDE_INTO_MASK = 0x1
	GUN_COOL_DOWN = 0.75

	def __init__(self):
		self.player.thrust_accel = 75
		self.player.turn_rate = 240
		verts = [(0, -8), (9, -12), (0, 12), (-8, -12)]
		self.shape.verts = verts
		self.renderable.color = (0.5, 1, 0.5)
		self.collision.radius = 7.5
		self.collision.into_mask = self.COLLIDE_INTO_MASK
		self.reset()
	
	def reset(self):
		self.position.position = (0, 0)
		self.position.angle = 0
		self.movement.velocity = (0, 0)
		self.movement.rotation = 0
		self.gun.firing = False
		self.gun.last_fire_time = 0
		self.gun.cool_down = self.GUN_COOL_DOWN
	
	def on_collide(self, other, point, normal):
		self.reset()


class Asteroid(grease.Entity):
	"""Big floating space rock"""

	COLLIDE_INTO_MASK = 0x2

	UNIT_CIRCLE = [(math.sin(math.radians(a)), math.cos(math.radians(a))) 
		for a in range(0, 360, 18)]
	
	def __init__(self, radius=45, position=None):
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
		self.collision.radius = radius * 0.8
		self.collision.from_mask = PlayerShip.COLLIDE_INTO_MASK
		self.collision.into_mask = self.COLLIDE_INTO_MASK
		self.renderable.color = (0.75, 0.75, 0.75)

	def on_collide(self, other, point, normal):
		if self.collision.radius > 10:
			debris_size = self.collision.radius / 1.6
			debris_count = 2 if self.collision.radius > 20 else 3
			for i in range(debris_count):
				world.Asteroid(debris_size, self.position.position)
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
		self.delete()
	
	def expire(self, dt):
		self.delete()


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
				entity.gun.last_fire_time = world.time
		

class Game(KeyControls):
	"""Main game logic system

	This subclass KeyControls so that the controls can be bound
	directly to the game logic here
	"""

	def __init__(self):
		KeyControls.__init__(self)
		self.level = 0
		self.player_ship = world.PlayerShip()
		self.start_level()
	
	def start_level(self):
		self.level += 1
		self.player_ship.reset()
		for i in range(self.level * 3 + 2):
			world.Asteroid()
	
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
	
	@KeyControls.key_release(key.UP)
	@KeyControls.key_release(key.W)
	def stop_thrust(self):
		self.player_ship.movement.accel = geometry.Vec2d(0, 0)

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

world.systems.add(
	('wrapper', PositionWrapper()),
	('guh', Gun()),
	('game', Game()),
)
pyglet.app.run()

