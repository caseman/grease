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
"""Blocks are slighly specialized numpy arrays that are used for storing
dynamically sized arrays of data.
"""

import numpy

_missing = object()


class Block(numpy.ndarray):
	
	def grow(self, size, fill_value=_missing):
		"""Resize the block with extra space for additional growth.  The
		resulting block array may be larger than the requested size.

		You can use fill_value to fill the added elements with a particular
		default. Since the number of filled elements is arbitrary, it probably
		only makes sense to use a single fill value for all calls for a given
		block.
		"""
		old_size = len(self)
		if old_size < size:
			if size < 64:
				size = max(size * 2, 4)
			else:
				size = size * 5 // 4
			self.resize(size, refcheck=False)
			if fill_value is not _missing:
				self[old_size:].fill(fill_value)

