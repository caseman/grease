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
"""Grease tutorial game revision 3"""

import os
import math
import random
import itertools
import pyglet
from pyglet.window import key
import grease
from grease import component, controller, geometry, collision, renderer, mode
from grease.controls import KeyControls

## Utility functions ##

SCRIPT_DIR_PATH = os.path.dirname(__file__)
pyglet.font.add_file(os.path.join(SCRIPT_DIR_PATH, 'font', 'Vectorb.ttf'))

def load_sound(name, streaming=False):
    """Load a sound from the `sfx` directory"""
    return pyglet.media.load(
        os.path.join(SCRIPT_DIR_PATH, 'sfx', name), streaming=streaming)

def looping_sound(name):
    """Load a sound from the `sfx` directory and configure it too loop
    continuously
    """
    sound = load_sound(name)
    looper = pyglet.media.SourceGroup(sound.audio_format, None)
    looper.loop = True
    looper.queue(sound)
    player = pyglet.media.Player()
    player.queue(looper)
    return player

## Define entity classes ##

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
    GUN_SOUND = load_sound('pewpew.wav')
    THRUST_SOUND = looping_sound('thrust.wav')
    DEATH_SOUND = load_sound('dead.wav')

    def __init__(self, world, invincible=False):
        self.position.position = (0, 0)
        self.position.angle = 0
        self.movement.velocity = (0, 0)
        self.movement.rotation = 0
        self.shape.verts = self.SHAPE_VERTS
        self.shape.closed = False
        self.renderable.color = self.COLOR
        self.collision.radius = self.COLLISION_RADIUS
        self.gun.cool_down = self.GUN_COOL_DOWN
        self.gun.sound = self.GUN_SOUND
        self.set_invincible(invincible)
    
    def turn(self, direction):
        self.movement.rotation = self.TURN_RATE * direction
    
    def thrust_on(self):
        thrust_vec = geometry.Vec2d(0, self.THRUST_ACCEL)
        thrust_vec.rotate(self.position.angle)
        self.movement.accel = thrust_vec
        self.shape.verts[2] = (0, -16 - random.random() * 16)
        self.THRUST_SOUND.play()
    
    def thrust_off(self):
        self.movement.accel = (0, 0)
        self.shape.verts[2] = (0, -8)
        self.THRUST_SOUND.pause()
    
    def set_invincible(self, invincible):
        """Set the invincibility status of the ship. If invincible is
        True then the ship will not collide with any obstacles and will
        blink to indicate this. If False, then the normal collision 
        behavior is restored
        """
        if invincible:
            self.collision.into_mask = 0
            self.collision.from_mask = 0
            self.world.clock.schedule_interval(self.blink, 0.15)
            self.world.clock.schedule_once(lambda dt: self.set_invincible(False), 3)
        else:
            self.world.clock.unschedule(self.blink)
            self.renderable.color = self.COLOR
            self.collision.from_mask = 0xffffffff
            self.collision.into_mask = self.COLLIDE_INTO_MASK
    
    def blink(self, dt):
        """Blink the ship to show invincibility"""
        if self.renderable:
            del self.renderable
        else:
            self.renderable.color = self.COLOR
    
    def on_collide(self, other, point, normal):
        self.explode()
        self.THRUST_SOUND.pause()
        self.DEATH_SOUND.play()
        self.world.systems.game.player_died()


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
    
    def __init__(self, world, radius=45, position=None, parent_velocity=None, points=25):
        if position is None:
            self.position.position = (
                random.choice([-1, 1]) * random.randint(50, window.width / 2), 
                random.choice([-1, 1]) * random.randint(50, window.height / 2))
        else:
            self.position.position = position
        self.movement.velocity = (random.gauss(0, 700 / radius), random.gauss(0, 700 / radius))
        if parent_velocity is not None:
            self.movement.velocity += parent_velocity
        self.movement.rotation = random.gauss(0, 15)
        verts = [(random.gauss(x*radius, radius / 7), random.gauss(y*radius, radius / 7))
            for x, y in self.UNIT_CIRCLE]
        self.shape.verts = verts
        self.renderable.color = "#aaa"
        self.collision.radius = radius
        self.collision.from_mask = PlayerShip.COLLIDE_INTO_MASK
        self.collision.into_mask = self.COLLIDE_INTO_MASK
        self.award.points = points

    def on_collide(self, other, point, normal):
        if self.collision.radius > 15:
            chunk_size = self.collision.radius / 2.0
            for i in range(2):
                Asteroid(self.world, chunk_size, self.position.position, 
                    self.movement.velocity, self.award.points * 2)
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
        self.world.systems.game.award_points(other)
        self.delete()
    
    def expire(self, dt):
        self.delete()

## Define game systems ##

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
                if entity.gun.sound is not None:
                    entity.gun.sound.play()
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

    CHIME_SOUNDS = [
        load_sound('chime1.wav'), 
        load_sound('chime2.wav'),
    ]
    MAX_CHIME_TIME = 2.0
    MIN_CHIME_TIME = 0.6

    def set_world(self, world):
        KeyControls.set_world(self, world)
        self.level = 0
        self.lives = 3
        self.score = 0
        self.player_ship = PlayerShip(self.world)
        self.start_level()
    
    def start_level(self):
        self.level += 1
        for i in range(self.level * 3 + 1):
            Asteroid(self.world)
        self.chime_time = self.MAX_CHIME_TIME
        self.chimes = itertools.cycle(self.CHIME_SOUNDS)
        if self.level == 1:
            self.chime()
    
    def chime(self, dt=0):
        """Play tension building chime sounds"""
        if self.lives:
            next(self.chimes).play()
            self.chime_time = max(self.chime_time - dt * 0.01, self.MIN_CHIME_TIME)
            if not self.world[Asteroid].entities:
                self.start_level()
            self.world.clock.schedule_once(self.chime, self.chime_time)

    def award_points(self, entity):
        """Get points for destroying stuff"""
        if entity.award:
            self.score += entity.award.points
    
    def player_died(self):
        self.lives -= 1
        self.player_ship.delete()
        self.world.clock.schedule_once(self.player_respawn, 3.0)
        
    def player_respawn(self, dt=None):
        """Rise to fly again, with temporary invincibility"""
        if self.lives:
            self.player_ship = PlayerShip(self.world, invincible=True)
        if self.world.is_multiplayer:
            # Switch to the next player
            if self.lives:
                window.current_mode.activate_next()
            else:
                window.current_mode.remove_submode()
    
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
    
    @KeyControls.key_press(key.P)
    def pause(self):
        self.world.running = not self.world.running    

    def on_key_press(self, key, modifiers):
        """Start the world with any key if paused"""
        if not self.world.running:
            self.world.running = True
        KeyControls.on_key_press(self, key, modifiers)



class Hud(grease.Renderer):
    """Heads-up display renderer"""
    
    def set_world(self, world):
        self.world = world
        self.last_lives = 0
        self.last_score = None
        self.game_over_label = None
        self.paused_label = None
        self.create_lives_entities()
    
    def create_lives_entities(self):
        """Create entities to represent the remaining lives"""
        self.lives = []
        verts = geometry.Vec2dArray(PlayerShip.SHAPE_VERTS[3:])
        left = -window.width // 2 + 25
        top = window.height // 2 - 25
        for i in range(20):
            entity = grease.Entity(self.world)
            entity.shape.verts = verts.transform(scale=0.75)
            entity.position.position = (i * 20 + left, top)
            self.lives.append((i, entity))

    def draw(self):
        game = self.world.systems.game
        if self.last_lives != game.lives:
            for i, entity in self.lives:
                if game.lives > i:
                    entity.renderable.color = PlayerShip.COLOR
                else:
                    entity.renderable.color = (0,0,0,0)
            self.last_lives = game.lives
        if self.last_score != game.score:
            self.score_label = pyglet.text.Label(
                str(game.score),
                color=(180, 180, 255, 255),
                font_name='Vector Battle', font_size=14, bold=True,
                x=window.width // 2 - 25, y=window.height // 2 - 25, 
                anchor_x='right', anchor_y='center')
            self.last_score = game.score
        self.score_label.draw()
        if game.lives == 0:
            if self.game_over_label is None:
                self.game_over_label = pyglet.text.Label(
                    "GAME OVER",
                    font_name='Vector Battle', font_size=36, bold=True,
                    color=(255, 0, 0, 255),
                    x = 0, y = 0, anchor_x='center', anchor_y='center')
            self.game_over_label.draw()
        if not self.world.running:
            if self.paused_label is None:
                self.player_label = pyglet.text.Label(
                    self.world.player_name,
                    color=(150, 150, 255, 255),
                    font_name='Vector Battle', font_size=18, bold=True,
                    x = 0, y = 20, anchor_x='center', anchor_y='bottom')
                self.paused_label = pyglet.text.Label(
                    "press a key to begin",
                    color=(150, 150, 255, 255),
                    font_name='Vector Battle', font_size=16, bold=True,
                    x = 0, y = -20, anchor_x='center', anchor_y='top')
            self.player_label.draw()
            self.paused_label.draw()


class TitleScreenControls(KeyControls):
    """Title screen key event handler system"""

    @KeyControls.key_press(key._1)
    def start_single_player(self):
        window.push_mode(Game())
    
    @KeyControls.key_press(key._2)
    def start_two_player(self):
        window.push_mode(mode.Multi(
            Game('Player One'), 
            Game('Player Two')))


class BaseWorld(grease.World):

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
            cool_down=float, 
            sound=object)
        self.components.award = component.Component(points=int)

        self.systems.movement = controller.EulerMovement()
        self.systems.collision = collision.Circular(
            handlers=[collision.dispatch_events])
        self.systems.sweeper = Sweeper()
        self.systems.gun = Gun()
        self.systems.wrapper = PositionWrapper()

        self.renderers.camera = renderer.Camera(
            position=(window.width / 2, window.height / 2))
        self.renderers.vector = renderer.Vector(line_width=1.5)


class TitleScreen(BaseWorld):
    """Game title screen world and mode"""
    
    def configure(self):
        BaseWorld.configure(self)
        self.renderers.title = pyglet.text.Label(
            "Blasteroids",
            color=(150, 150, 255, 255),
            font_name='Vector Battle', font_size=32, bold=True,
            x=0, y=50, anchor_x='center', anchor_y='bottom')
        self.renderers.description = pyglet.text.Label(
            "A demo for the Grease game engine",
            color=(150, 150, 255, 255),
            font_name='Vector Battle', font_size=16, bold=True,
            x=0, y=20, anchor_x='center', anchor_y='top')
        self.renderers.one_player = pyglet.text.Label(
            "Press 1 for one player",
            color=(150, 150, 255, 255),
            font_name='Vector Battle', font_size=16, bold=True,
            x=0, y=-100, anchor_x='center', anchor_y='top')
        self.renderers.two_player = pyglet.text.Label(
            "Press 2 for two players",
            color=(150, 150, 255, 255),
            font_name='Vector Battle', font_size=16, bold=True,
            x=0, y=-130, anchor_x='center', anchor_y='top')

        self.systems.controls = TitleScreenControls()
        for i in range(15):
            Asteroid(self, radius=random.randint(12, 45))


class Game(BaseWorld):
    """Main game world and mode"""

    def __init__(self, player_name=""):
        BaseWorld.__init__(self)
        self.player_name = player_name
        self.is_multiplayer = self.player_name != ""

    def configure(self):
        BaseWorld.configure(self)
        self.systems.game = GameSystem()
        self.renderers.hud = Hud()
    
    def activate(self, manager):
        """Start paused in multiplayer"""
        grease.World.activate(self, manager)
        if self.is_multiplayer:
            self.running = False


def main():
    """Initialize and run the game"""
    global window
    window = mode.ManagerWindow()
    window.push_mode(TitleScreen())
    pyglet.app.run()

if __name__ == '__main__':
    main()


# vim: ai ts=4 sts=4 et sw=4

