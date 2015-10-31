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
"""Control systems for binding controls to game logic"""

import grease
from pyglet.window import key

class KeyControls(grease.System):
	"""System that maps subclass-defined action methods to keys. 

	Keys may be mapped in the subclass definition using decorators
	defined here as class methods or at runtime using the ``bind_key_*`` 
	instance methods.

	See :ref:`an example implementation in the tutorial <tut-controls-example>`.
	"""
	MODIFIER_MASK = ~(key.MOD_NUMLOCK | key.MOD_SCROLLLOCK | key.MOD_CAPSLOCK)
	"""The MODIFIER_MASK allows you to filter out modifier keys that should be
	ignored by the application. By default, capslock, numlock, and scrolllock 
	are ignored.
	"""

	world = None
	""":class:`grease.World` object this system is bound to"""

	def __init__(self):
		self._key_press_map = {}
		self._key_release_map = {}
		self._key_hold_map = {}
		for name in self.__class__.__dict__:
			member = getattr(self, name)
			if hasattr(member, '_grease_hold_key_binding'):
				for binding in member._grease_hold_key_binding:
					self.bind_key_hold(member, *binding)
			if hasattr(member, '_grease_press_key_binding'):
				for binding in member._grease_press_key_binding:
					self.bind_key_press(member, *binding)
			if hasattr(member, '_grease_release_key_binding'):
				for binding in member._grease_release_key_binding:
					self.bind_key_release(member, *binding)
		self.held_keys = set()

	## decorator methods for binding methods to key input events ##

	@classmethod
	def key_hold(cls, symbol, modifiers=0):
		"""Decorator to bind a method to be executed where a key is held down"""
		def bind(f):
			if not hasattr(f, '_grease_hold_key_binding'):
				f._grease_hold_key_binding = []
			f._grease_hold_key_binding.append((symbol, modifiers & cls.MODIFIER_MASK))
			return f
		return bind

	@classmethod
	def key_press(cls, symbol, modifiers=0):
		"""Decorator to bind a method to be executed where a key is initially depressed"""
		def bind(f):
			if not hasattr(f, '_grease_press_key_binding'):
				f._grease_press_key_binding = []
			f._grease_press_key_binding.append((symbol, modifiers & cls.MODIFIER_MASK))
			return f
		return bind

	@classmethod
	def key_release(cls, symbol, modifiers=0):
		"""Decorator to bind a method to be executed where a key is released"""
		def bind(f):
			if not hasattr(f, '_grease_release_key_binding'):
				f._grease_release_key_binding = []
			f._grease_release_key_binding.append((symbol, modifiers & cls.MODIFIER_MASK))
			return f
		return bind
	
	## runtime binding methods ##
	
	def bind_key_hold(self, method, key, modifiers=0):
		"""Bind a method to a key at runtime to be invoked when the key is
		held down, this replaces any existing key hold binding for this key.
		To unbind the key entirely, pass ``None`` for method.
		"""
		if method is not None:
			self._key_hold_map[key, modifiers & self.MODIFIER_MASK] = method
		else:
			try:
				del self._key_hold_map[key, modifiers & self.MODIFIER_MASK]
			except KeyError:
				pass

	def bind_key_press(self, method, key, modifiers=0):
		"""Bind a method to a key at runtime to be invoked when the key is initially
		pressed, this replaces any existing key hold binding for this key. To unbind
		the key entirely, pass ``None`` for method.
		"""
		if method is not None:
			self._key_press_map[key, modifiers & self.MODIFIER_MASK] = method
		else:
			try:
				del self._key_press_map[key, modifiers & self.MODIFIER_MASK]
			except KeyError:
				pass

	def bind_key_release(self, method, key, modifiers=0):
		"""Bind a method to a key at runtime to be invoked when the key is releaseed,
		this replaces any existing key hold binding for this key. To unbind
		the key entirely, pass ``None`` for method.
		"""
		if method is not None:
			self._key_release_map[key, modifiers & self.MODIFIER_MASK] = method
		else:
			try:
				del self._key_release_map[key, modifiers & self.MODIFIER_MASK]
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

	def on_key_press(self, key, modifiers):
		"""Handle pyglet key press. Invoke key press methods and
		activate key hold functions
		"""
		key_mod = (key, modifiers & self.MODIFIER_MASK)
		if key_mod in self._key_press_map:
			self._key_press_map[key_mod]()
		self.held_keys.add(key_mod)
	
	def on_key_release(self, key, modifiers):
		"""Handle pyglet key release. Invoke key release methods and
		deactivate key hold functions
		"""
		key_mod = (key, modifiers & self.MODIFIER_MASK)
		if key_mod in self._key_release_map:
			self._key_release_map[key_mod]()
		self.held_keys.discard(key_mod)


if __name__ == '__main__':
	import pyglet

	class TestKeyControls(KeyControls):
		
		MODIFIER_MASK = ~(key.MOD_NUMLOCK | key.MOD_SCROLLLOCK | key.MOD_CTRL)

		remapped = False
		
		@KeyControls.key_hold(key.UP)
		@KeyControls.key_hold(key.W)
		def up(self, dt):
			print('UP!')
		
		@KeyControls.key_hold(key.LEFT)
		@KeyControls.key_hold(key.A)
		def left(self, dt):
			print('LEFT!')
		
		@KeyControls.key_hold(key.RIGHT)
		@KeyControls.key_hold(key.D)
		def right(self, dt):
			print('RIGHT!')
		
		@KeyControls.key_hold(key.DOWN)
		@KeyControls.key_hold(key.S)
		def down(self, dt):
			print('DOWN!')

		@KeyControls.key_press(key.SPACE)
		def fire(self):
			print('FIRE!')

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
	controls = TestKeyControls()
	window.push_handlers(controls)
	pyglet.clock.schedule_interval(controls.step, 0.5)
	pyglet.app.run()

