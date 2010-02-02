
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
			position.last_xy = position.xy
			position.xy += movement.velocity * dt
			position.last_angle = position.angle
			position.angle += movement.rotation * dt

