#############################################################################
#
# Copyright (c) 2010, 2011 by Casey Duncan and contributors
# All Rights Reserved.
#
# This software is subject to the provisions of the MIT License
# A copy of the license should accompany this distribution.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#
#############################################################################
import numpy
from grease.block import Block


class EntitySet(object):
	"""Set of entities in a world"""

	world = None
	"""The |World| the entities in the set belong to"""

	blocks = None
	"""Entity array storage blocks"""

	def __init__(self, world):
		self.world = world
		self.blocks = {}
	
	def new_empty(self):
		"""Create a new empty set of the same type and world.
		This is a common interface for creating a set with no
		arguments.
		"""
		new = EntitySet.__new__(self.__class__)
		new.world = self.world
		new.blocks = {}
		return new
	
	def _get_block(self, block_id, index):
		try:
			block = self.blocks[block_id]
			block.grow(index + 1, 0)
		except KeyError:
			block = self.blocks[block_id] = Block(
				shape=index + 1, dtype="int32")
			block.fill(0)
		return block
	
	def add(self, entity):
		"""Add an entity to the set.
		
		:raises ValueError: If the entity is not part of the same
		world as the set, also for deleted entities.
		"""
		if entity.world is not self.world:
			raise ValueError("Cannot add entity from different world")
		if entity not in self.world.entities:
			raise ValueError("Cannot add deleted entity")
		gen, block, index = entity.entity_id
		self._get_block(block, index)[index] = gen
	
	def remove(self, entity):
		"""Remove an entity from the set. 
		
		:raises KeyError: if entity is not in the set.
		"""
		gen, block, index = entity.entity_id
		try:
			gen_in = self.blocks[block][index]
		except (KeyError, IndexError):
			raise KeyError(entity)
		if entity.world is self.world and gen_in == gen:
			self.blocks[block][index] = 0
		else:
			raise KeyError(entity)
	
	def discard(self, entity):
		"""Remove an entity from the set, do nothing if the entity is
		not in the set
		"""
		gen, block, index = entity.entity_id
		try:
			gen_in_set = self.blocks[block][index]
		except (KeyError, IndexError):
			return
		if entity.world is self.world and gen_in_set == gen:
			self.blocks[block][index] = 0
	
	def __contains__(self, entity):
		if entity.world is self.world:
			gen, block, index = entity.entity_id
			try:
				return self.blocks[block][index] == gen
			except (KeyError, IndexError):
				return False
		return False
	
	def __iter__(self):
		return self.world.entities.iter_intersection(self)
	
	def __nonzero__(self):
		for block in self.blocks.values():
			if block.any():
				return True
		return False

	def __len__(self):
		return sum(len(block.nonzero()[0]) for block in self.blocks.values())
	
	def __eq__(self, other):
		if self is other:
			return True
		if isinstance(other, EntitySet):
			self_blk_ids = set(self.blocks)
			other_blk_ids = set(other.blocks)
			for blk_id in (self_blk_ids - other_blk_ids):
				if self.blocks[blk_id].any():
					return False
			for blk_id in (other_blk_ids - self_blk_ids):
				if other.blocks[blk_id].any():
					return False
			for blk_id, blk in self.blocks.items():
				if blk_id in other.blocks:
					other_blk = other.blocks[blk_id]
					if len(blk) > len(other_blk):
						if not ((blk[:len(other_blk)] == other_blk).all() and
							(blk[len(other_blk):] == 0).all()):
							return False
					elif len(blk) < len(other_blk):
						if not ((other_blk[:len(blk)] == blk).all() and
							(other_blk[len(blk):] == 0).all()):
							return False
					elif not (blk == other_blk).all():
						return False
			return True
		else:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def _intersection(self, other, result):
		if self.world is not other.world:
			raise ValueError("Can't combine sets from different worlds")
		blocks = self.blocks
		result.blocks = {}
		for blk_id, blk in blocks.items():
			if blk_id in other.blocks:
				other_blk = other.blocks[blk_id]
				if len(blk) < len(other_blk):
					other_blk = other_blk[:len(blk)]
				elif len(blk) > len(other_blk):
					blk = blk[:len(other_blk)]
				result_blk = numpy.where(blk == other_blk, blk, 0)
				if result_blk.any():
					result.blocks[blk_id] = result_blk

	def intersection(self, other):
		"""Return a set which is the intersection of this set and another"""
		result = self.new_empty()
		self._intersection(other, result)
		return result
	
	__and__ = intersection

	def intersection_update(self, other):
		"""Return this set containing only elements in common with other"""
		self._intersection(other, self)
		return self
	
	__iand__ = intersection_update

	def _union(self, other, result):
		if self.world is not other.world:
			raise ValueError("Can't combine sets from different worlds")
		if result is not self:
			for blk_id, blk in self.blocks.items():
				if blk_id not in other.blocks:
					result.blocks[blk_id] = self.blocks[blk_id].copy()
		for blk_id, other_blk in other.blocks.items():
			if blk_id not in self.blocks:
				result.blocks[blk_id] = other_blk.copy()
			else:
				blk = self.blocks[blk_id]
				if len(blk) < len(other_blk):
					lblk = blk
					rblk = other_blk[:len(blk)]
				elif len(blk) > len(other_blk):
					lblk = blk[:len(other_blk)]
					rblk = other_blk
				else:
					lblk = blk
					rblk = other_blk
				result_blk = numpy.where(lblk >= rblk, lblk, rblk)
				if len(blk) < len(other_blk):
					result_blk = numpy.concatenate(
						(result_blk, other_blk[len(blk):]))
				elif len(blk) > len(other_blk):
					result_blk = numpy.concatenate(
						(result_blk, blk[len(other_blk):]))
				result.blocks[blk_id] = result_blk
		
	def union(self, other):
		"""Return a set which is the union of this set and another"""
		result = self.new_empty()
		self._union(other, result)
		return result
	
	__or__ = union

	def update(self, other):
		"""Return this set with entities added from other"""
		self._union(other, self)
		return self
	
	__ior__ = update

	def _difference(self, other, result):
		if self.world is not other.world:
			raise ValueError("Can't combine sets from different worlds")
		if result is not self:
			for blk_id, blk in self.blocks.items():
				if blk_id not in other.blocks:
					result.blocks[blk_id] = blk.copy()
		for blk_id, other_blk in other.blocks.items():
			if blk_id in self.blocks:
				blk = self.blocks[blk_id]
				if len(blk) > len(other_blk):
					lblk = blk[:len(other_blk)]
					result_blk = numpy.where(lblk > other_blk, lblk, 0)
					result_blk = numpy.concatenate(
						(result_blk, blk[len(other_blk):]))
				else:
					result_blk = numpy.where(
						blk > other_blk[:len(blk)], blk, 0)
				if result_blk.any():
					result.blocks[blk_id] = result_blk
				elif blk_id in result.blocks:
					del result.blocks[blk_id]
		return result

	def difference(self, other):
		"""Return a set which is the difference of this set and another"""
		result = self.new_empty()
		self._difference(other, result)
		return result
	
	__sub__ = difference

	def difference_update(self, other):
		"""Return this set with entities in other removed"""
		self._difference(other, self)
		return self
	
	__isub__ = difference_update


