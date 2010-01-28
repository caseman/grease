"""Minimal vector graphics example using pyglet"""

import math
import random
import pyglet
import grease
from grease import component, controller, renderer, vector

manager = grease.ComponentEntityManager(
	position=component.Position(),
	movement=component.Movement(),
	shape=component.Shape(),
	renderable=component.Renderable(),
	controllers=[
		controller.EulerMovement(),
	]
)

renderer = renderer.VectorRenderer(manager, line_width=1.0)

window = pyglet.window.Window()
@window.event
def on_draw():
	window.clear()
	renderer.draw()

@window.event
def on_mouse_scroll(x, y, dx, dy):
	renderer.scale += dy * 0.02
	renderer.line_width = max(1.0, renderer.line_width + dx * 0.01)
	print renderer.scale, renderer.line_width

def add_shape(dt=None):
	sides = random.randint(2,6)
	shape = manager.new_entity()
	shape.position.xy = (window.width / 2, window.height / 2)
	shape.position.angle = random.randint(0, 359)
	shape.movement.velocity = (random.gauss(0, 50), random.gauss(0, 50))
	shape.movement.rotation = random.gauss(0, 90)
	size = max(10, random.gauss(30, 15))
	step = math.pi * 2 / sides
	shape.shape.verts = [(math.sin(step * i) * size, math.cos(step * i) * size) 
		for i in range(sides)]
	shape.renderable.color = (random.random(), random.random(), random.random(), 1)
	pyglet.clock.schedule_once(add_shape, random.expovariate(5.0))

pyglet.clock.schedule_interval(manager.controllers.run, 1.0/60.0)
add_shape()
pyglet.app.run()

