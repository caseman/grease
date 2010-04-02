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
	"""System that applies entity movement to position using Euler's method

	:param position_component: Name of :class:`grease.component.Position` 
		component to update.
	:param movement_component: Name of :class:`grease.component.Movement` 
		component used to update position.
	"""

	def __init__(self, position_component='position', movement_component='movement'):
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

