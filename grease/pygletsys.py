#############################################################################
#
# Copyright (c) 2010 by Casey Duncan
# All Rights Reserved.
#
# This software is subject to the provisions of the MIT License
# A copy of the license should accompany this distribution.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#
#############################################################################
"""Grease systems specific to Pyglet"""

import grease
import new

class KeyControls(grease.System):
	"""Maps subclass-defined action methods to keys. 

	Keys may be mapped in the subclass definition using decorators
	defined here as class methods or at runtime using the bind_key_* 
	instance methods.
	"""

	world = None
	""":mod:`grease.World` object this system is bound to"""

	_cls_key_hold_map = {}
	_cls_key_press_map = {}
	_cls_key_release_map = {}

	def __init__(self):
		self.held_keys = set()

	def set_world(self, world):
		assert getattr(world, 'window', None) is not None, (
			'To use %s you must bind the world to a pyglet window' % self.__class__.__name__)
		self.world = world
		world.window.push_handlers(self)
		# Copy the class key mappings to the instance and bind the methods
		self._key_press_map = self._bind_mapped_methods(self._cls_key_press_map)
		self._key_release_map = self._bind_mapped_methods(self._cls_key_release_map)
		self._key_hold_map = self._bind_mapped_methods(self._cls_key_hold_map)

	## decorator methods for binding methods to key input events ##

	@classmethod
	def key_hold(cls, symbol, modifiers=0):
		"""Bind a method to be executed where a key is held down"""
		def bind(f):
			cls._cls_key_hold_map[symbol, modifiers] = f
			return f
		return bind

	@classmethod
	def key_press(cls, symbol, modifiers=0):
		"""Bind a method to be executed where a key is initially depressed"""
		def bind(f):
			cls._cls_key_press_map[symbol, modifiers] = f
			return f
		return bind

	@classmethod
	def key_release(cls, symbol, modifiers=0):
		"""Bind a method to be executed where a key is released"""
		def bind(f):
			cls._cls_key_release_map[symbol, modifiers] = f
			return f
		return bind
	
	def _bind_mapped_methods(self, key_map):
		"""Given a map of keys to unbound methods, return
		a new map with those methods bound to this instance
		"""
		bound_map = {}
		for key_mod, method in key_map.items():
			bound_map[key_mod] = new.instancemethod(method, self, self.__class__)
		return bound_map
	
	## runtime binding methods ##
	
	def bind_key_hold(self, method, key, modifiers=0):
		"""Bind a method to a key at runtime to be invoked when the key is held down,
		this replaces any existing key hold binding for this key. To unbind
		the key entirely, pass None for method.
		"""
		if method is not None:
			self._key_hold_map[key, modifiers] = method
		else:
			try:
				del self._key_hold_map[key, modifiers]
			except KeyError:
				pass

	def bind_key_press(self, method, key, modifiers=0):
		"""Bind a method to a key at runtime to be invoked when the key is initially
		pressed, this replaces any existing key hold binding for this key. To unbind
		the key entirely, pass None for method.
		"""
		if method is not None:
			self._key_press_map[key, modifiers] = method
		else:
			try:
				del self._key_press_map[key, modifiers]
			except KeyError:
				pass

	def bind_key_release(self, method, key, modifiers=0):
		"""Bind a method to a key at runtime to be invoked when the key is releaseed,
		this replaces any existing key hold binding for this key. To unbind
		the key entirely, pass None for method.
		"""
		if method is not None:
			self._key_release_map[key, modifiers] = method
		else:
			try:
				del self._key_release_map[key, modifiers]
			except KeyError:
				pass

	def step(self, dt):
		"""invoke held key functions"""
		already_run = set()
		for key in self.held_keys:
			func = self._key_hold_map.get(key)
			if func is not None and func not in already_run:
				already_run.add(func)
				func(dt)

	def on_key_press(self, *key):
		"""Handle pyglet key press. Invoke key press methods and
		activate key hold functions
		"""
		if key in self._key_press_map:
			self._key_press_map[key]()
		self.held_keys.add(key)
	
	def on_key_release(self, *key):
		"""Handle pyglet key release. Invoke key release methods and
		deactivate key hold functions
		"""
		if key in self._key_release_map:
			self._key_release_map[key]()
		self.held_keys.discard(key)


if __name__ == '__main__':
	import pyglet
	from pyglet.window import key

	class KeyControls(KeyControls):
		
		remapped = False
		
		@KeyControls.key_hold(key.UP)
		@KeyControls.key_hold(key.W)
		def up(self, dt):
			print 'UP!'
		
		@KeyControls.key_hold(key.LEFT)
		@KeyControls.key_hold(key.A)
		def left(self, dt):
			print 'LEFT!'
		
		@KeyControls.key_hold(key.RIGHT)
		@KeyControls.key_hold(key.D)
		def right(self, dt):
			print 'RIGHT!'
		
		@KeyControls.key_hold(key.DOWN)
		@KeyControls.key_hold(key.S)
		def down(self, dt):
			print 'DOWN!'

		@KeyControls.key_press(key.SPACE)
		def fire(self):
			print 'FIRE!'

		@KeyControls.key_press(key.R)
		def remap_keys(self):
			if not self.remapped:
				self.bind_key_hold(None, key.W)
				self.bind_key_hold(None, key.A)
				self.bind_key_hold(None, key.S)
				self.bind_key_hold(None, key.D)
				self.bind_key_hold(self.up, key.I)
				self.bind_key_hold(self.left, key.J)
				self.bind_key_hold(self.right, key.L)
				self.bind_key_hold(self.down, key.K)
			else:
				self.bind_key_hold(None, key.I)
				self.bind_key_hold(None, key.J)
				self.bind_key_hold(None, key.K)
				self.bind_key_hold(None, key.L)
				self.bind_key_hold(self.up, key.W)
				self.bind_key_hold(self.left, key.A)
				self.bind_key_hold(self.right, key.D)
				self.bind_key_hold(self.down, key.S)
			self.remapped = not self.remapped
			

	window = pyglet.window.Window()
	window.clear()
	controls = KeyControls(window)
	pyglet.clock.schedule_interval(controls.run, 0.5)
	pyglet.app.run()

