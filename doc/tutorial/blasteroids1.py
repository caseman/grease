import math
import random
import pyglet
import grease
from grease import component, controller, renderer


class Asteroid(grease.Entity):
    """Big floating space rock"""

    UNIT_CIRCLE = [(math.sin(math.radians(a)), math.cos(math.radians(a))) 
        for a in range(0, 360, 18)]

    def __init__(self, world, radius=45):
        self.position.position = (
            random.choice([-1, 1]) * random.randint(50, window.width / 2), 
            random.choice([-1, 1]) * random.randint(50, window.height / 2))
        self.movement.velocity = (random.gauss(0, 700 / radius), random.gauss(0, 700 / radius))
        self.movement.rotation = random.gauss(0, 15)
        verts = [(random.gauss(x*radius, radius / 7), random.gauss(y*radius, radius / 7))
            for x, y in self.UNIT_CIRCLE]
        self.shape.verts = verts
        self.renderable.color = (0.75, 0.75, 0.75)


class GameWorld(grease.World):

    def configure(self):
        """Configure the game world's components, systems and renderers"""
        self.components.position = component.Position()
        self.components.movement = component.Movement()
        self.components.shape = component.Shape()
        self.components.renderable = component.Renderable()

        self.systems.movement = controller.EulerMovement()

        self.renderers.camera = renderer.Camera(
            position=(window.width / 2, window.height / 2))
        self.renderers.vector = renderer.Vector(line_width=1.5)


def main():
    """Initialize and run the game"""
    global window
    window = pyglet.window.Window()
    world = GameWorld()
    pyglet.clock.schedule(world.tick)
    window.push_handlers(world)
    for i in range(8):
        Asteroid(world)
    pyglet.app.run()

if __name__ == '__main__':
    main()


