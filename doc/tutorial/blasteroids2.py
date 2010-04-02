#############################################################################
#
# Copyright (c) 2010 by Casey Duncan and contributors
# All Rights Reserved.
#
# This software is subject to the provisions of the MIT License
# A copy of the license should accompany this distribution.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#
#############################################################################
"""Grease tutorial game revision 2"""

import math
import random
import pyglet
import grease
from grease import component, controller, renderer, geometry, collision
from pyglet.window import key
from grease.controls import KeyControls


class BlasteroidsEntity(grease.Entity):
    """Entity base class"""

    def explode(self):
        """Segment the entity shape into itty bits"""
        shape = self.shape.verts.transform(angle=self.position.angle)
        for segment in shape.segments():
            debris = Debris(self.world)
            debris.shape.verts = segment
            debris.position.position = self.position.position
            debris.movement.velocity = self.movement.velocity
            debris.movement.velocity += segment[0].normalized() * random.gauss(50, 20)
            debris.movement.rotation = random.gauss(0, 45)
            debris.renderable.color = self.renderable.color


class Debris(grease.Entity):
    """Floating space junk"""


class PlayerShip(BlasteroidsEntity):
    """Thrust ship piloted by the player"""

    THRUST_ACCEL = 75
    TURN_RATE = 240
    SHAPE_VERTS = [
        (-8, -12), (-4, -10), (0, -8), (4, -10), (8, -12), # flame
        (0, 12), (-8, -12), (0, -8), (8, -12)]
    COLOR = "#7f7"
    COLLISION_RADIUS = 7.5
    COLLIDE_INTO_MASK = 0x1
    GUN_COOL_DOWN = 0.5

    def __init__(self, world, invincible=False):
        self.position.position = (0, 0)
        self.position.angle = 0
        self.movement.velocity = (0, 0)
        self.movement.rotation = 0
        self.shape.verts = self.SHAPE_VERTS
        self.shape.closed = False
        self.renderable.color = self.COLOR
        self.collision.into_mask = self.COLLIDE_INTO_MASK
        self.collision.radius = self.COLLISION_RADIUS
        self.gun.cool_down = self.GUN_COOL_DOWN


    def turn(self, direction):
        self.movement.rotation = self.TURN_RATE * direction
    
    def thrust_on(self):
        thrust_vec = geometry.Vec2d(0, self.THRUST_ACCEL)
        thrust_vec.rotate(self.position.angle)
        self.movement.accel = thrust_vec
        self.shape.verts[2] = (0, -16 - random.random() * 16)        

    def thrust_off(self):
        self.movement.accel = (0, 0)
        self.shape.verts[2] = (0, -8)

    def on_collide(self, other, point, normal):
        """Collision response handler"""
        self.explode()
        self.delete()


class Asteroid(BlasteroidsEntity):
    """Big floating space rock"""

    COLLIDE_INTO_MASK = 0x2
    UNIT_CIRCLE = [(math.sin(math.radians(a)), math.cos(math.radians(a))) 
        for a in range(0, 360, 18)]

    def __init__(self, world, radius=45):
        self.position.position = (
            random.choice([-1, 1]) * random.randint(50, window.width / 2), 
            random.choice([-1, 1]) * random.randint(50, window.height / 2))
        self.movement.velocity = (random.gauss(0, 700 / radius), random.gauss(0, 700 / radius))
        self.movement.rotation = random.gauss(0, 15)
        verts = [(random.gauss(x * radius, radius / 7), random.gauss(y * radius, radius / 7))
            for x, y in self.UNIT_CIRCLE]
        self.shape.verts = verts
        self.renderable.color = "#aaa"
        self.collision.radius = radius
        self.collision.from_mask = PlayerShip.COLLIDE_INTO_MASK
        self.collision.into_mask = self.COLLIDE_INTO_MASK

    def on_collide(self, other, point, normal):
        """Collision response handler"""
        self.explode()
        self.delete()


class Shot(grease.Entity):
    """Pew Pew!"""

    SPEED = 300
    TIME_TO_LIVE = 0.75 # seconds
    
    def __init__(self, world, shooter, angle):
        offset = geometry.Vec2d(0, shooter.collision.radius)
        offset.rotate(angle)
        self.position.position = shooter.position.position + offset
        self.movement.velocity = (
            offset.normalized() * self.SPEED + shooter.movement.velocity)
        self.shape.verts = [(0, 1.5), (1.5, -1.5), (-1.5, -1.5)]
        self.collision.radius = 2.0
        self.collision.from_mask = ~shooter.collision.into_mask
        self.renderable.color = "#ffc"
        world.clock.schedule_once(self.expire, self.TIME_TO_LIVE)

    def on_collide(self, other, point, normal):
        self.delete()
    
    def expire(self, dt):
        self.delete()


class PositionWrapper(grease.System):
    """Wrap positions around when they go off the edge of the window"""

    def __init__(self):
        self.half_width = window.width / 2
        self.half_height = window.height / 2

    def step(self, dt):
        for entity in self.world[...].collision.aabb.right < -self.half_width:
            entity.position.position.x += window.width + entity.collision.aabb.width
        for entity in self.world[...].collision.aabb.left > self.half_width:
            entity.position.position.x -= window.width + entity.collision.aabb.width
        for entity in self.world[...].collision.aabb.top < -self.half_height:
            entity.position.position.y += window.height + entity.collision.aabb.height 
        for entity in self.world[...].collision.aabb.bottom > self.half_height:
            entity.position.position.y -= window.height + entity.collision.aabb.height


class Gun(grease.System):
    """Fires Shot entities"""

    def step(self, dt):
        for entity in self.world[...].gun.firing == True:
            if self.world.time >= entity.gun.last_fire_time + entity.gun.cool_down:
                Shot(self.world, entity, entity.position.angle)
                entity.gun.last_fire_time = self.world.time



class Sweeper(grease.System):
    """Clears out space debris"""

    SWEEP_TIME = 2.0

    def step(self, dt):
        fade = dt / self.SWEEP_TIME
        for entity in tuple(self.world[Debris].entities):
            color = entity.renderable.color
            if color.a > 0.2:
                color.a = max(color.a - fade, 0)
            else:
                entity.delete()


class GameSystem(KeyControls):
    """Main game logic system

    This subclass KeyControls so that the controls can be bound
    directly to the game logic here
    """

    def set_world(self, world):
        KeyControls.set_world(self, world)
        self.player_ship = PlayerShip(self.world)

    @KeyControls.key_press(key.LEFT)
    @KeyControls.key_press(key.A)
    def start_turn_left(self):
        if self.player_ship.exists:
            self.player_ship.turn(-1)

    @KeyControls.key_release(key.LEFT)
    @KeyControls.key_release(key.A)
    def stop_turn_left(self):
        if self.player_ship.exists and self.player_ship.movement.rotation < 0:
            self.player_ship.turn(0)

    @KeyControls.key_press(key.RIGHT)
    @KeyControls.key_press(key.D)
    def start_turn_right(self):
        if self.player_ship.exists:
            self.player_ship.turn(1)

    @KeyControls.key_release(key.RIGHT)
    @KeyControls.key_release(key.D)
    def stop_turn_right(self):
        if self.player_ship.exists and self.player_ship.movement.rotation > 0:
            self.player_ship.turn(0)
    
    @KeyControls.key_hold(key.UP)
    @KeyControls.key_hold(key.W)
    def thrust(self, dt):
        if self.player_ship.exists:
            self.player_ship.thrust_on()
        
    @KeyControls.key_release(key.UP)
    @KeyControls.key_release(key.W)
    def stop_thrust(self):
        if self.player_ship.exists:
            self.player_ship.thrust_off()
            
    @KeyControls.key_press(key.SPACE)
    def start_firing(self):
        if self.player_ship.exists:
            self.player_ship.gun.firing = True

    @KeyControls.key_release(key.SPACE)
    def stop_firing(self):
        if self.player_ship.exists:
            self.player_ship.gun.firing = False


class GameWorld(grease.World):

    def configure(self):
        """Configure the game world's components, systems and renderers"""
        self.components.position = component.Position()
        self.components.movement = component.Movement()
        self.components.shape = component.Shape()
        self.components.renderable = component.Renderable()
        self.components.collision = component.Collision()        
        self.components.gun = component.Component(
            firing=bool, 
            last_fire_time=float, 
            cool_down=float)

        self.systems.movement = controller.EulerMovement()
        self.systems.game = GameSystem()
        self.systems.collision = collision.Circular(
            handlers=[collision.dispatch_events])
        self.systems.sweeper = Sweeper()
        self.systems.gun = Gun()
        self.systems.wrapper = PositionWrapper()

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
    window.push_handlers(world.systems.game)
    for i in range(8):
        Asteroid(world)
    pyglet.app.run()

if __name__ == '__main__':
    main()


# vim: ai ts=4 sts=4 et sw=4

