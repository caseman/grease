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
	"""::class::`pyglet.event.EventDispatcher` object that the
	active mode receive events from.
	"""

	@property
	def current_mode(self):
		"""The current active mode or None. Read-only"""
		try:
			return self.modes[-1]
		except IndexError:
			return None
	
	def on_last_mode_pop(self, mode):
		"""Hook executed when the last mode is popped from the manager.
		Implementing this method is optional for subclasses.

		Args:
			`mode` (Mode): The mode object just popped from the manager
		"""
	
	def push_mode(self, mode):
		"""Push a mode to the top of the mode stack and make it active
		
		Args:
			`mode` (Mode): The mode object to make active
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

		Returns:
			`mode` (Mode): The mode object popped from the stack
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
		one, but without activating the mode previous to the current mode or
		executing :method:`on_last_mode_pop()` if there is no previous mode.

		Returns:
			`mode` (Mode): The mode object that was deactivated and replaced.
		"""
		mode = self.modes.pop()
		mode.deactivate(self)
		self.event_dispatcher.remove_handlers(mode)
		self.modes.append(mode)
		self.event_dispatcher.push_handlers(mode)
		mode.activate(self)
		return mode


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

	Args:
		Constructor arguments are identical to :class:`pyglet.window.Window`
	"""
	
	def __init__(self, *args, **kw):
		super(ManagerWindow, self).__init__(*args, **kw)
		self.modes = []
		self.event_dispatcher = self


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
		"""Tick the mode's clock."""
		self.time += dt
		self.clock.tick(poll=False)
	
	@abc.abstractmethod
	def step(self, dt):
		"""Execute a timestep for this mode"""

	def activate(self, mode_manager):
		"""Activate the mode for the given mode manager, if the mode is already active, 
		do nothing

		The default implementation schedules time steps at `step_rate` per
		second, sets the `manager` and sets the `active` flag to True.
		"""
		if not self.active:
			self.master_clock.schedule(self.tick)
			self.manager = mode_manager
			self.active = True

	def deactivate(self, mode_manager):
		"""Deactivate the mode, if the mode is not active, do nothing

		The default implementation unschedules time steps for the mode and
		sets the `active` flag to False.
		"""
		self.master_clock.unschedule(self.tick)
		self.active = False

