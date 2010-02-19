import abc
import pyglet

class Manager(object):
	"""Manages modes for a given window"""

	def __init__(self, window):
		self._window = window
		self.modes = []
	
	@property
	def current_mode(self):
		"""The current mode running in the window or None"""
		try:
			return self.modes[-1]
		except IndexError:
			return None
	
	@property
	def window(self):
		"""::class::`pyglet.Window` object that the modes will use"""
		return self._window
	
	def on_last_mode_pop(self, mode):
		"""Executed when the last mode is popped from the manager.
		The default action is to close the window. May be overridden
		in subclasses

		Args:
			`mode` (Mode): The mode object just popped from the manager
		"""
		self.window.close()
	
	def push_mode(self, mode):
		"""Push a mode to the top of the mode stack and make it active
		
		Args:
			`mode` (Mode): The mode object to make active
		"""
		current = self.current_mode
		if current is not None:
			current.deactivate()
			self.window.remove_handlers(current)
		self.modes.append(mode)
		self.window.push_handlers(mode)
		mode.activate(self.window)
	
	def pop_mode(self):
		"""Pop the current mode off the top of the stack and deactivate it.
		The mode remaining at the top of the stack, if any is activated.

		Returns:
			`mode` (Mode): The mode object popped from the stack
		"""
		mode = self.modes.pop()
		mode.deactivate()
		self.window.remove_handlers(mode)
		current = self.current_mode
		if current is not None:
			self.window.push_handlers(current)
			current.activate(self.window)
		else:
			self.on_last_mode_pop(mode)
		return mode


class Mode(object):
	"""Application mode abstract base class

	Subclasses must implement the :method:`step()` method
	"""
	__metaclass__ = abc.ABCMeta

	clock = None
	"""The :class:`pyglet.clock.Clock` instance used as this mode's clock.
	You should use this clock to schedule tasks for this mode, so they
	properly respect when the mode is active or inactive
	"""

	window = None
	"""The :class:`pyglet.window.Window` the mode is being used for"""

	def __init__(self, step_rate=60, master_clock=pyglet.clock):
		self.step_rate = step_rate
		self.active = False
		self.time = 0.0
		self.master_clock = master_clock
		self.clock = pyglet.clock.Clock(time_function=self._clock_time)
		self.clock.schedule_interval(self.step, 1.0 / step_rate)
	
	def _clock_time(self):
		"""Return the current time value for the mode's clock"""
		return self.time
	
	def tick(self, dt):
		"""Tick the mode's clock."""
		self.time += dt
		self.clock.tick(poll=False)
	
	@abc.abstractmethod
	def step(self, dt):
		"""Execute a timestep for this mode"""
	
	@abc.abstractmethod
	def on_draw(self):
		"""Draw the contents of the current window"""

	def activate(self, window):
		"""Activate the mode for the given window, if the mode is already active, 
		do nothing

		The default implementation schedules time steps at `step_rate` per
		second
		"""
		if not self.active:
			self.master_clock.schedule(self.tick)
			self.window = window
			self.active = True

	def deactivate(self):
		"""Deactivate the mode, if the mode is not active, do nothing

		The default implementation unschedules time steps for the mode
		"""
		self.master_clock.unschedule(self.tick)
		self.running = False


class WorldMode(Mode):
	"""A mode that wraps a single :class:`grease.World`"""

	def __init__(self, step_rate=60, master_clock=pyglet.clock):
		self.world = self.create_world()
		super(WorldMode, self).__init__(step_rate, master_clock)
		self.world.clock = self.clock
	
	@abc.abstractmethod
	def create_world(self):
		"""Create the world used by this mode. Override in subclasses
		to construct and configure the world.

		Returns:
			:class:`grease.World` object to use by this mode
		"""
	
	def activate(self, window):
		"""Activate the mode for the given window, if the mode is already active, 
		do nothing

		The systems for the mode's world are pushed onto the window
		as handlers
		"""
		if not self.active:
			for system in self.world.systems:
				window.push_handlers(system)
		super(WorldMode, self).activate(window)
	
	def deactivate(self):
		"""Deactivate the mode, if the mode is not active, do nothing

		Removes the system handlers from the window
		"""
		for system in self.world.systems:
			self.window.remove_handlers(system)
		super(WorldMode, self).deactivate(window)

	def tick(self, dt):
		"""Tick the mode's clock, but only if the world is currently running"""
		if self.world.running:
			super(WorldMode, self).tick(dt)
	
	def step(self, dt):
		"""Execute a timestep for the mode's world
		
		Note that the specified time delta will be pinned to 10x the
		configured step rate. For example if the step rate is 60,
		then dt will be pinned at a maximum of 0.1666. This avoids 
		pathological behavior when the time between steps goes
		much longer than expected.
		"""
		dt = min(dt, 10.0 / self.step_rate)
		self.world.step(dt)

	def on_draw(self, gl=pyglet.gl):
		"""Clear the window, reset the model/view matrix and invoke the world's 
		`draw()` method.
		"""
		self.window.clear() # XXX this only clears color and depth buffers by default
		gl.glLoadIdentity()
		self.world.draw()

