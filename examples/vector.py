"""Minimal Grease vector graphics example using pyglet"""

import math
import random
import pyglet
import grease
from grease import component, controller, renderer

window = pyglet.window.Window()

# Create the grease world, bound to a window
# Binding the world to a window passes the window events
# to the world and sets up a renderer pipeline for that window
# By default the world is scheduled to step 60 times per second
world = grease.World(window)
world.components.map(
	# Components specify and contain the data for the world's entities
	position=component.Position(),
	movement=component.Movement(),
	shape=component.Shape(),
	renderable=component.Renderable(),
)
world.systems.add(
	# Systems provide behavior for the world
	('movement', controller.EulerMovement()),
)
# The render pipeline determines the world presentation
world.renderers = [renderer.Vector(line_width=2)]

class Shape(grease.Entity):
	"""Shape entity definition. 
	
	Entity types are automagically available as attributes of any world object.
	"""
	def __init__(self, num_sides, size):
		self.position.position = (window.width / 2, window.height / 2)
		self.position.angle = random.randint(0, 359)
		self.movement.velocity = (random.gauss(0, 50), random.gauss(0, 50))
		self.movement.rotation = random.gauss(0, 90)
		step = math.pi * 2 / num_sides
		self.shape.verts = [(math.sin(step * i) * size, math.cos(step * i) * size) 
			for i in range(num_sides)]
		self.renderable.color = (random.random(), random.random(), random.random(), 1)

def add_shape(dt=None):
	"""Add a random shape every so often"""
	world.Shape(num_sides=random.randint(2,6), size=max(10, random.gauss(30, 15)))
	pyglet.clock.schedule_once(add_shape, random.expovariate(5.0))

add_shape() # Add the first shape to prime the system
pyglet.app.run() # Start the main event loop
