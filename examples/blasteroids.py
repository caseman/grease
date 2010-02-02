import math
import random
import pyglet
from pyglet.window import key
import grease
from grease import component, system, vector
from grease.system.pygletsys import KeyControls

window = pyglet.window.Window()
window.clear()
paused = False


class PlayerControls(KeyControls):

	@KeyControls.key_hold(key.LEFT)
	def turn_left(self, dt):
		ship = self.manager.player.entity
		ship.movement.rotation = -ship.player.turn
	
	@KeyControls.key_hold(key.RIGHT)
	def turn_right(self, dt):
		ship = self.manager.player.entity
		ship.movement.rotation = ship.player.turn
	
	@KeyControls.key_hold(key.UP)
	def thrust(self, dt):
		ship = self.manager.player.entity
		ship.physics.body.apply_local_force(ship.player.thrust * dt)
	
	@KeyControls.key_press(key.P)
	def pause(self, dt):
		global paused
		paused = not paused
		

manager = grease.ComponentEntityManager(
	position=component.Position(),
	movement=component.Movement(),
	shape=component.Shape(),
	renderable=component.Renderable(),
	collision=component.Collision(),
	# Custom components
	asteroids=component.Component(),
	player=component.Singleton(thrust=vector.Vec2d, turn=float),
	controllers=[
		PlayerControls(window),
		system.VectorRenderer(scale=20),
	]
)

renderer = VectorRenderer(manager, scale=20)

def reset_player_ship():
	ship = manager.player.entity or manager.new_entity()
	ship.player.thrust = (0, 100)
	ship.player.turn = 90
	ship.position.xy = (0, 0)
	ship.position.angle = 0
	verts = [(0, -0.5), (0.5, -1), (0, 1), (-0.5, -1)]
	ship.movement.velocity = (0, 0)
	ship.movement.rotation = 0
	ship.physics.body.mass = 10
	ship.physics.shapes.add(grease.chipmunk.PolygonShape(verts))
	ship.shape.verts = verts
	ship.shape.line_color = (0.5, 1, 0.5)
	return ship

asteroid_starting_domain = grease.domain.Disc(center=(0, 0), 
		inner_radius=400, outer_radius=800)
unit_circle = [(math.sin(math.radians(a)), math.cos(math.radians(a))) 
	for a in range(0, 360, 36)]

def create_asteroid(radius=60):
	roid = manager.new_entity()
	roid.position.xy = asteroid_starting_domain.random_point()
	deviation = radius / 5
	verts = [(random.gauss(x*radius, deviation), random.gauss(y*radius, deviation)
		for x, y in unit_circle]
	roid.movement.velocity = (random.gauss(0, 50), random.gauss(0, 50))
	roid.movment.rotation = random.gauss(0, 15)
	roid.physics.shapes.add(grease.chipmunk.PolygonShape(verts))
	roid.shape.verts = verts
	roid.shape.line_color = (0.75, 0.75, 0.75)
	return roid

level = 0

def next_level(asteroid_count):
	global level
	reset_player_ship()
	manager.entities.delete(manager.asteroids)
	level += 1
	for i in range(level + 4):
		create_asteroid()

	

keys = key.KeyStateHandler()
window.push_handlers(keys)


