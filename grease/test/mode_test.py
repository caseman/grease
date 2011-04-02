import unittest
import pyglet


class TestEventDispatcher(object):
	
	def __init__(self):
		self.handlers = []
	
	def push_handlers(self, handlers):
		self.handlers.append(handlers)
	
	def pop_handlers(self):
		return self.handlers.pop()
	
	def remove_handlers(self, handlers):
		self.handlers.remove(handlers)


class TestMode(object):
	active = False
	activations = 0
	manager = None

	def activate(self, manager):
		self.activations += 1
		self.active = True
		self.manager = manager
	
	def deactivate(self, manager):
		self.active = False
		self.manager = manager


class ModeManagerTestBase(object):

	def test_push_mode(self):
		manager = self.createManager()
		self.assertFalse(manager.modes)
		self.assertTrue(manager.current_mode is None)
		mode1 = TestMode()
		mode2 = TestMode()
		manager.push_mode(mode1)
		self.assertTrue(manager.current_mode, mode1)
		self.assertEqual(manager.event_dispatcher.handlers, [mode1])
		self.assertTrue(mode1.active)
		self.assertTrue(mode1.manager is manager)
		self.assertEqual(mode1.activations, 1)
		manager.push_mode(mode2)
		self.assertFalse(manager.current_mode is mode1)
		self.assertTrue(manager.current_mode is mode2)
		self.assertEqual(manager.event_dispatcher.handlers, [mode2])
		self.assertFalse(mode1.active)
		self.assertTrue(mode2.active)
		self.assertTrue(mode2.manager is manager)
		self.assertEqual(mode1.activations, 1)
		self.assertEqual(mode2.activations, 1)
		return manager, mode1, mode2
	
	def test_pop_mode(self):
		manager, mode1, mode2 = self.test_push_mode()
		mode3 = TestMode()
		manager.push_mode(mode3)
		self.assertFalse(manager.current_mode is mode1)
		self.assertFalse(manager.current_mode is mode2)
		self.assertTrue(manager.current_mode is mode3)
		self.assertEqual(manager.event_dispatcher.handlers, [mode3])
		self.assertFalse(mode1.active)
		self.assertFalse(mode2.active)
		self.assertTrue(mode3.active)
		self.assertTrue(mode3.manager is manager)
		self.assertEqual(mode1.activations, 1)
		self.assertEqual(mode2.activations, 1)
		self.assertEqual(mode3.activations, 1)
		popped = manager.pop_mode()
		self.assertTrue(popped is mode3)
		self.assertFalse(manager.current_mode is mode1)
		self.assertTrue(manager.current_mode is mode2)
		self.assertFalse(manager.current_mode is mode3)
		self.assertEqual(manager.event_dispatcher.handlers, [mode2])
		self.assertFalse(mode1.active)
		self.assertTrue(mode2.active)
		self.assertFalse(mode3.active)
		self.assertEqual(mode1.activations, 1)
		self.assertEqual(mode2.activations, 2)
		self.assertEqual(mode3.activations, 1)
		self.assertTrue(mode3.manager is manager)
		popped = manager.pop_mode()
		self.assertTrue(popped is mode2)
		self.assertTrue(manager.current_mode is mode1)
		self.assertFalse(manager.current_mode is mode2)
		self.assertFalse(manager.current_mode is mode3)
		self.assertEqual(manager.event_dispatcher.handlers, [mode1])
		self.assertTrue(mode1.active)
		self.assertFalse(mode2.active)
		self.assertFalse(mode3.active)
		self.assertEqual(mode1.activations, 2)
		self.assertEqual(mode2.activations, 2)
		self.assertEqual(mode3.activations, 1)
		self.assertTrue(mode2.manager is manager)
	
	def test_over_pop(self):
		manager, mode1, mode2 = self.test_push_mode()
		manager.pop_mode()
		manager.pop_mode()
		self.assertFalse(manager.modes)
		self.assertEqual(manager.event_dispatcher.handlers, [])
		self.assertTrue(manager.current_mode is None)
		self.assertRaises(IndexError, manager.pop_mode)
		self.assertEqual(manager.event_dispatcher.handlers, [])
	
	def test_pop_last_mode(self):
		class ModeManager(self.ManagerClass):
			def on_last_mode_pop(self, mode):
				self.last_popped = mode
		manager = self.createManager(ModeManager)
		mode = TestMode()
		manager.push_mode(mode)
		manager.pop_mode()
		self.assertEqual(manager.event_dispatcher.handlers, [])
		self.assertTrue(manager.current_mode is None)
		self.assertTrue(manager.last_popped is mode)
	
	def test_swap_modes(self):
		manager, mode1, mode2 = self.test_push_mode()
		mode3 = TestMode()
		swapped = manager.swap_modes(mode3)
		self.assertTrue(swapped is mode2)
		self.assertFalse(manager.current_mode is mode1)
		self.assertFalse(manager.current_mode is mode2)
		self.assertTrue(manager.current_mode is mode3)
		self.assertEqual(manager.event_dispatcher.handlers, [mode3])
		self.assertFalse(mode1.active)
		self.assertFalse(mode2.active)
		self.assertTrue(mode3.active)
		self.assertTrue(mode3.manager is manager)
		self.assertEqual(mode1.activations, 1)
		self.assertEqual(mode2.activations, 1)
		self.assertEqual(mode3.activations, 1)
		popped = manager.pop_mode()
		self.assertTrue(popped is mode3)
		self.assertTrue(manager.current_mode is mode1)
		self.assertFalse(manager.current_mode is mode2)
		self.assertFalse(manager.current_mode is mode3)
		self.assertEqual(manager.event_dispatcher.handlers, [mode1])
		self.assertTrue(mode1.active)
		self.assertFalse(mode2.active)
		self.assertFalse(mode3.active)
		self.assertEqual(mode1.activations, 2)
		self.assertEqual(mode2.activations, 1)
		self.assertEqual(mode3.activations, 1)


class ManagerTestCase(ModeManagerTestBase, unittest.TestCase):

	def setUp(self):
		from grease import mode
		self.ManagerClass = mode.Manager
	
	def createManager(self, cls=None):
		cls = cls or self.ManagerClass
		return cls(TestEventDispatcher())
	
	def test_manager_init(self):
		dispatcher = TestEventDispatcher()
		manager = self.ManagerClass(dispatcher)
		self.assertTrue(manager.event_dispatcher is dispatcher)


class WindowManagerTestCase(ModeManagerTestBase, unittest.TestCase):

	def setUp(self):
		from grease import mode
		self.ManagerClass = mode.ManagerWindow
	
	def createManager(self, cls=None):
		cls = cls or self.ManagerClass
		manager = cls(visible=False)
		manager.event_dispatcher = TestEventDispatcher()
		return manager

	def test_is_pyglet_window(self):
		manager = self.createManager()
		self.assertTrue(isinstance(manager, pyglet.window.Window))
	
	def test_event_dispatcher_is_window(self):
		from grease import mode
		window = mode.ManagerWindow(visible=False)
		self.assertTrue(window.event_dispatcher is window)
	
	def test_last_pop_closes_window(self):
		from grease import mode
		event_loop = pyglet.app.EventLoop() # We need one for on_close() to do its thing
		event_loop._setup()
		window = mode.ManagerWindow(visible=False)
		window.push_mode(TestMode())
		self.assertTrue(window.current_mode)
		self.assertTrue(window in pyglet.app.windows)
		window.pop_mode()
		self.assertFalse(window.current_mode)
		self.assertFalse(window in pyglet.app.windows)


if __name__ == '__main__':
	unittest.main()	

