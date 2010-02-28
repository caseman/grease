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

__version__ = '$Id$'


class EulerMovement(object):
	"""Applies movement to position using Euler's method"""

	def __init__(self, position_component='position', movement_component='movement'):
		"""Initialize the system.

		position_component -- Name of Position component to update.

		movement_component -- Name of Movment component used to update position.
		"""
		self.position_component = position_component
		self.movement_component = movement_component
	
	def set_world(self, world):
		"""Bind the system to a world"""
		self.world = world
	
	def step(self, dt):
		"""Apply movement to position"""
		assert self.world is not None, "Cannot run with no world set"
		for position, movement in self.world.components.join(
			self.position_component, self.movement_component):
			movement.velocity += movement.accel * dt
			position.position += movement.velocity * dt
			position.angle += movement.rotation * dt

