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
)
world.systems.add(
	('movement', controller.EulerMovement()),
	('collision', collision.Circular()),
)
world.renderers = (
	renderer.Camera(position=(window.width / 2, window.height / 2)),
	renderer.Vector(line_width=1.5),
)


## Define entity classes ##

class PlayerShip(grease.Entity):
	"""Thrust ship piloted by the player"""

	def __init__(self):
		self.player.thrust_accel = 75
		self.player.turn_rate = 240
		verts = [(0, -8), (9, -12), (0, 12), (-8, -12)]
		self.shape.verts = verts
		self.renderable.color = (0.5, 1, 0.5)
		self.reset()
	
	def reset(self):
		self.position.position = (0, 0)
		self.position.angle = 0
		self.movement.velocity = (0, 0)
		self.movement.rotation = 0


class Asteroid(grease.Entity):
	"""Big floating space rock"""

	UNIT_CIRCLE = [(math.sin(math.radians(a)), math.cos(math.radians(a))) 
		for a in range(0, 360, 18)]
	
	def __init__(self, radius=45):
		self.position.position = (
			random.choice([-1, 1]) * random.randint(50, window.width / 2), 
			random.choice([-1, 1]) * random.randint(50, window.height / 2))
		deviation = radius / 8
		self.movement.velocity = (random.gauss(0, 600 / radius), random.gauss(0, 600 / radius))
		self.movement.rotation = random.gauss(0, 15)
		verts = [(random.gauss(x*radius, deviation), random.gauss(y*radius, deviation))
			for x, y in self.UNIT_CIRCLE]
		self.shape.verts = verts
		self.renderable.color = (0.75, 0.75, 0.75)


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
	
	@KeyControls.key_press(key.P)
	def pause(self):
		if self.world.running:
			self.world.stop()
		else:
			self.world.start()

world.systems.add(
	('wrapper', PositionWrapper()),
	('game', Game()),
)
pyglet.app.run()

