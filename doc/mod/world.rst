:mod:`grease.world` -- Entity Environment
=========================================

.. automodule:: grease.world
   :synopsis: Container and environment for entities, component, systems and renderers

.. autoclass:: World(step_rate=60, master_clock=pyglet.clock)
   :members:
   :inherited-members:

   .. automethod:: __getitem__

.. autoclass:: Parts
   :members:

.. autoclass:: ComponentParts
   :members:
   :inherited-members:

.. autoclass:: EntityExtent
    :members: __getattr__, entities

