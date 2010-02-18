import grease.component
import grease.geometry
import grease.collision
from grease.entity import Entity
from grease.world import World

import abc

class System(object):
	"""Grease system abstract base class"""
	__metaclass__ = abc.ABCMeta

	world = None
	"""The :class:`grease.World` this system belongs to"""

	def set_world(self, world):
		"""Bind the system to a world"""
		self.world = world
	
	@abc.abstractmethod
	def step(self, dt):
		"""Execute a time step for the system.

		Args:
			`dt` (float): Time since last step invocation
		"""


class Renderer(object):
	"""Grease renderer abstract base class"""
	__metaclass__ = abc.ABCMeta

	world = None
	"""The :class:`grease.World` this renderer belongs to"""

	def set_world(self, world):
		"""Bind the system to a world"""
		self.world = world

	@abc.abstractmethod
	def draw(self):
		"""Issue drawing commands for this renderer"""

