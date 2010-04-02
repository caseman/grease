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
"""
Modes manage the state and transition between different application modes.
Typically such modes are presented as different screens that the user can
navigate between, similar to the way a browser navigates web pages. Individual
modes may be things like:

- Title screen
- Options dialog
- About screen
- In-progress game
- Inventory interface

The modal framework provides a simple mechanism to ensure that modes are
activated and deactivated properly. An activated mode is running and receives
events. A deactivated mode is paused and does not receive events.

Modes may be managed as a *last-in-first-out* stack, or as a list, or ring
of modes in sequence, or some combination of all.

For example usage see: :ref:`the mode section of the tutorial <tut-mode-section>`.
"""

__version__ = '$Id$'

import abc
import pyglet


class BaseManager(object):
	"""Mode manager abstract base class.
	
	The mode manager keeps a stack of modes where a single mode
	is active at one time. As modes are pushed on and popped from 
	the stack, the mode at the top is always active. The current
	active mode receives events from the manager's event dispatcher.
	"""

	modes = ()
	"""The mode stack sequence. The last mode in the stack is
	the current active mode. Read-only.
	"""

	event_dispatcher = None
	""":class:`pyglet.event.EventDispatcher` object that the
	active mode receive events from.
	"""

	@property
	def current_mode(self):
		"""The current active mode or ``None``. Read-only"""
		try:
			return self.modes[-1]
		except IndexError:
			return None
	
	def on_last_mode_pop(self, mode):
		"""Hook executed when the last mode is popped from the manager.
		Implementing this method is optional for subclasses.

		:param mode: The :class:`Mode` object just popped from the manager
		"""
	
	def push_mode(self, mode):
		"""Push a mode to the top of the mode stack and make it active
		
		:param mode: The :class:`Mode` object to make active
		"""
		current = self.current_mode
		if current is not None:
			current.deactivate(self)
			self.event_dispatcher.remove_handlers(current)
		self.modes.append(mode)
		self.event_dispatcher.push_handlers(mode)
		mode.activate(self)
	
	def pop_mode(self):
		"""Pop the current mode off the top of the stack and deactivate it.
		The mode now at the top of the stack, if any is then activated.

		:param mode: The :class:`Mode` object popped from the stack
		"""
		mode = self.modes.pop()
		mode.deactivate(self)
		self.event_dispatcher.remove_handlers(mode)
		current = self.current_mode
		if current is not None:
			self.event_dispatcher.push_handlers(current)
			current.activate(self)
		else:
			self.on_last_mode_pop(mode)
		return mode
	
	def swap_modes(self, mode):
		"""Exchange the specified mode with the mode at the top of the stack.
		This is similar to popping the current mode and pushing the specified
		one, but without activating the previous mode on the stack or
		executing :meth:`on_last_mode_pop()` if there is no previous mode.

		:param mode: The :class:`Mode` object that was deactivated and replaced.
		"""
		old_mode = self.modes.pop()
		old_mode.deactivate(self)
		self.event_dispatcher.remove_handlers(old_mode)
		self.modes.append(mode)
		self.event_dispatcher.push_handlers(mode)
		mode.activate(self)
		return old_mode
	
	def remove_mode(self, mode):
		"""Remove the specified mode. If the mode is at the top of the stack,
		this is equivilent to :meth:`pop_mode()`. If not, no other modes
		are affected. If the mode is not in the manager, do nothing.

		:param mode: The :class:`Mode` object to remove from the manager.
		"""
		if self.current_mode is mode:
			self.pop_mode()
		else:
			try:
				self.modes.remove(mode)
			except ValueError:
				pass


class Manager(BaseManager):
	"""A basic mode manager that wraps a single
	:class:`pyglet.event.EventDispatcher` object for use by its modes.
	"""

	def __init__(self, event_dispatcher):
		self.modes = []
		self.event_dispatcher = event_dispatcher


class ManagerWindow(BaseManager, pyglet.window.Window):
	"""An integrated mode manager and pyglet window for convenience.
	The window is the event dispatcher used by modes pushed to
	this manager.

	Constructor arguments are identical to :class:`pyglet.window.Window`
	"""
	
	def __init__(self, *args, **kw):
		super(ManagerWindow, self).__init__(*args, **kw)
		self.modes = []
		self.event_dispatcher = self

	def on_key_press(self, symbol, modifiers):
		"""Default :meth:`on_key_press handler`, pops the current mode on ``ESC``"""
		if symbol == pyglet.window.key.ESCAPE:
			self.pop_mode()

	def on_last_mode_pop(self, mode):
		"""Hook executed when the last mode is popped from the manager.
		When the last mode is popped from a window, an :meth:`on_close` event
		is dispatched.

		:param mode: The :class:`Mode` object just popped from the manager
		"""
		self.dispatch_event('on_close')


class Mode(object):
	"""Application mode abstract base class

	Subclasses must implement the :meth:`step` method
	
	:param step_rate: The rate of :meth:`step()` calls per second. 

	:param master_clock: The :class:`pyglet.clock.Clock` interface used
		as the master clock that ticks the world's clock. This 
		defaults to the main pyglet clock.
	"""
	__metaclass__ = abc.ABCMeta

	clock = None
	"""The :class:`pyglet.clock.Clock` instance used as this mode's clock.
	You should use this clock to schedule tasks for this mode, so they
	properly respect when the mode is active or inactive

	Example::

		my_mode.clock.schedule_once(my_cool_function, 4)
	"""

	manager = None
	"""The :class:`BaseManager` that manages this mode"""

	def __init__(self, step_rate=60, master_clock=pyglet.clock, 
		         clock_factory=pyglet.clock.Clock):
		self.step_rate = step_rate
		self.active = False
		self.time = 0.0
		self.master_clock = master_clock
		self.clock = clock_factory(time_function=lambda: self.time)
		self.clock.schedule_interval(self.step, 1.0 / step_rate)
	
	def tick(self, dt):
		"""Tick the mode's clock.

		:param dt: The time delta since the last tick
		:type dt: float
		"""
		self.time += dt
		self.clock.tick(poll=False)
	
	@abc.abstractmethod
	def step(self, dt):
		"""Execute a timestep for this mode. Must be defined by subclasses.
		
		:param dt: The time delta since the last time step
		:type dt: float
		"""

	def activate(self, mode_manager):
		"""Activate the mode for the given mode manager, if the mode is already active, 
		do nothing

		The default implementation schedules time steps at :attr:`step_rate` per
		second, sets the :attr:`manager` and sets the :attr:`active` flag to True.
		"""
		if not self.active:
			self.master_clock.schedule(self.tick)
			self.manager = mode_manager
			self.active = True

	def deactivate(self, mode_manager):
		"""Deactivate the mode, if the mode is not active, do nothing

		The default implementation unschedules time steps for the mode and
		sets the :attr:`active` flag to False.
		"""
		self.master_clock.unschedule(self.tick)
		self.active = False


class Multi(Mode):
	"""A mode with multiple submodes. One submode is active at one time.
	Submodes can be switched to directly or switched in sequence. If
	the Multi is active, then one submode is always active.

	Multis are useful when modes can switch in an order other than
	a LIFO stack, such as in "hotseat" multiplayer games, a
	"wizard" style ui, or a sequence of slides.

	Note unlike a normal :class:`Mode`, a :class:`Multi` doesn't have it's own
	:attr:`clock` and :attr:`step_rate`. The active submode's are used
	instead.
	"""
	active_submode = None
	"""The currently active submode"""

	def __init__(self, *submodes):
		# We do not invoke the superclass __init__ intentionally
		self.time = 0.0
		self.active = False
		self.submodes = list(submodes)
	
	def add_submode(self, mode, before=None, index=None):
		"""Add the submode, but do not make it active.

		:param mode: The :class:`Mode` object to add.

		:param before: The existing mode to insert the mode before. 
			If the mode specified is not a submode, raise
			ValueError.

		:param index: The place to insert the mode in the mode list.
			Only one of ``before`` or ``index`` may be specified.

			If neither ``before`` or ``index`` are specified, the
			mode is appended to the end of the list.
		"""
		assert before is None or index is None, (
			"Cannot specify both 'before' and 'index' arguments")
		if before is not None:
			index = self.submodes.index(mode)
		if index is not None:
			self.submodes.insert(index, mode)
		else:
			self.submodes.append(mode)
	
	def remove_submode(self, mode=None):
		"""Remove the submode.

		:param mode: The submode to remove, if omitted the active submode
			is removed. If the mode is not present, do nothing.  If the
			mode is active, it is deactivated, and the next mode, if any
			is activated. If the last mode is removed, the :class:`Multi`
			is removed from its manager. 
		"""
		# TODO handle multiple instances of the same subnode
		if mode is None:
			mode = self.active_submode
		elif mode not in self.submodes:
			return
		next_mode = self.activate_next()
		self.submodes.remove(mode)
		if next_mode is mode:
			if self.manager is not None:
				self.manager.remove_mode(self)
			self._deactivate_submode()
				
	def activate_subnode(self, mode, before=None, index=None):
		"""Activate the specified mode, adding it as a subnode
		if it is not already. If the mode is already the active
		submode, do nothing.

		:param mode: The mode to activate, and add as necesary.

		:param before: The existing mode to insert the mode before
			if it is not already a submode.  If the mode specified is not
			a submode, raise ValueError.

		:param index: The place to insert the mode in the mode list
			if it is not already a submode.  Only one of ``before`` or
			``index`` may be specified.

			If the mode is already a submode, the ``before`` and ``index``
			arguments are ignored.
		"""
		if mode not in self.submodes:
			self.add_submode(mode, before, index)
		if self.active_submode is not mode:
			self._activate_submode(mode)
	
	def activate_next(self, loop=True):
		"""Activate the submode after the current submode in order.  If there
		is no current submode, the first submode is activated.

		Note if there is only one submode, it's active, and `loop` is True
		(the default), then this method does nothing and the subnode remains
		active.

		:param loop: When :meth:`activate_next` is called 
			when the last submode is active, a True value for ``loop`` will
			cause the first submode to be activated.  Otherwise the
			:class:`Multi` is removed from its manager.
		:type loop: bool

		:return:
			The submode that was activated or None if there is no
			other submode to activate.
		"""
		assert self.submodes, "No submode to activate"
		next_mode = None
		if self.active_submode is None:
			next_mode = self.submodes[0]
		else:
			last_mode = self.active_submode
			index = self.submodes.index(last_mode) + 1
			if index < len(self.submodes):
				next_mode = self.submodes[index]
			elif loop:
				next_mode = self.submodes[0]
		self._activate_submode(next_mode)
		return next_mode

	def activate_previous(self, loop=True):
		"""Activate the submode before the current submode in order.  If there
		is no current submode, the last submode is activated.

		Note if there is only one submode, it's active, and `loop` is True
		(the default), then this method does nothing and the subnode remains
		active.
		
		:param loop: When :meth:`activate_previous` is called 
			when the first submode is active, a True value for ``loop`` will
			cause the last submode to be activated.  Otherwise the
			:class:`Multi` is removed from its manager.
		:type loop: bool

		:return:
			The submode that was activated or None if there is no
			other submode to activate.
		"""
		assert self.submodes, "No submode to activate"
		prev_mode = None
		if self.active_submode is None:
			prev_mode = self.submodes[-1]
		else:
			last_mode = self.active_submode
			index = self.submodes.index(last_mode) - 1
			if loop or index >= 0:
				prev_mode = self.submodes[index]
		self._activate_submode(prev_mode)
		return prev_mode
	
	def _set_active_submode(self, submode):
		self.active_submode = submode
		self.master_clock = submode.master_clock
		self.clock = submode.clock
		self.step_rate = submode.step_rate

	def _activate_submode(self, submode):
		"""Activate a submode deactivating any current submode. If the Multi
		itself is active, this happens immediately, otherwise the actual
		activation is deferred until the Multi is activated. If the submode
		is None, the Mulitmode is removed from its manager.

		If submode is already the active submode, do nothing.
		"""
		if self.active_submode is submode:
			return
		assert submode in self.submodes, "Unknown submode"
		self._deactivate_submode()
		self._set_active_submode(submode)
		if submode is not None:
			if self.active:
				self.manager.event_dispatcher.push_handlers(submode)
				submode.activate(self.manager)
		else:
			if self.manager is not None:
				self.manager.remove_mode(self)
	
	def _deactivate_submode(self, clear_subnode=True):
		"""Deactivate the current submode, if any. if `clear_subnode` is
		True, `active_submode` is always None when this method returns
		"""
		if self.active_submode is not None:
			if self.active:
				self.manager.event_dispatcher.remove_handlers(self.active_submode)
				self.active_submode.deactivate(self.manager)
			if clear_subnode:
				self.active_submode = None
				self.master_clock = None
				self.clock = None
				self.step_rate = None
	
	def activate(self, mode_manager):
		"""Activate the :class:`Multi` for the specified manager. The
		previously active submode of the :class:`Multi` is activated. If there
		is no previously active submode, then the first submode is made active. 
		A :class:`Multi` with no submodes cannot be activated
		"""
		assert self.submodes, "No submode to activate"
		self.manager = mode_manager
		if self.active_submode is None:
			self._set_active_submode(self.submodes[0])
		else:
			self._set_active_submode(self.active_submode)
		self.manager.event_dispatcher.push_handlers(self.active_submode)
		self.active_submode.activate(self.manager)
		super(Multi, self).activate(mode_manager)
	
	def deactivate(self, mode_manager):
		"""Deactivate the :class:`Multi` for the specified manager.
		The `active_submode`, if any, is deactivated.
		"""
		self._deactivate_submode(clear_subnode=False)
		super(Multi, self).deactivate(mode_manager)
	
	def tick(self, dt):
		"""Tick the active submode's clock.

		:param dt: The time delta since the last tick
		:type dt: float
		"""
		self.time += dt
		if self.active_submode is not None:
			self.active_submode.clock.tick(poll=False)
	
	def step(self, dt):
		"""No-op, only the active submode is actually stepped"""

