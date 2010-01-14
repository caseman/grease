import math
import random
import pyglet
import grease
from grease import component, system

window = pyglet.window.Window()
window.clear()

cm = grease.ComponentEntityManager(
	position=component.Position(),
	movement=component.Movement(),
	script=component.Script(),
	physics=component.ChipmunkPhysics(),
	shape=component.Shape(),
	# Custom components
	asteroids=component.Component(),
	systems=[
		system.ChipmunkPhysics(),
		system.PygletEventHandler(window),
		system.VectorRenderer(scale=20),
	]
)

def create_player_ship():
	ship = cm.entity()
	ship.position.xy = (0, 0)
	verts = [(0, -0.5), (0.5, -1), (0, 1), (-0.5, -1)]
	ship.movement.velocity = (0, 0)
	ship.physics.mass = 10
	ship.physics.shapes.add(grease.chipmunk.PolygonShape(verts))
	ship.shape.verts = verts
	ship.shape.line_color = (0.5, 1, 0.5)
	return ship

asteroid_starting_domain = grease.domain.Disc(center=(0, 0), 
		inner_radius=400, outer_radius=800)
unit_circle = [(math.sin(math.radians(a)), math.cos(math.radians(a))) 
	for a in range(0, 360, 36)]

def create_asteroid(radius=60):
	roid = cm.entity()
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


