.. _tut-chapter-3:

########################
Grease Tutorial Part III
########################

Crash, Bang, Boom!
==================

Let's start by having some fun with some sound effects. The sound functionality itself is provided by Pyglet, but we will be seeing how to tie it into the game logic we already have. To start with, let's define some helper functions to help with loading and configuring the sounds:

.. literalinclude:: blasteroids3.py
   :start-after: ## Utility functions ##
   :end-before: font
.. literalinclude:: blasteroids3.py
   :pyobject: load_sound
.. literalinclude:: blasteroids3.py
   :pyobject: looping_sound

First we define a constant :obj:`SCRIPT_DIR_PATH` to store the path to the script's directory. The ``__file__`` module global is set by Python to the file path of the running script. Using :func:`os.path.dirname` we get the path to the containing directory so that we can construct file paths relative to it. This way we can find our sound files regardless of the current working directory when the script is run.

The :func:`load_sound` function is a simple wrapper around :func:`pyglet.media.load` that loads sound files from the ``sfx`` directory adjacent to the script. The false default value for the :attr:`streaming` argument means that by default the files will be preloaded into memory, which is best for short sound effects.

The :func:`load_sound` function creates fire-and-forget sounds that always play all the way through. We also add a :func:`looping_sound` function for continous-play sounds. This creates the sounds as streaming, which is suitable for longer sound effects or music. It also returns a full fledged :class:`pyglet.media.Player` object which affords us more control than a simple sound object.

For a simple game like this, with relatively few sounds, we can ensure that all the sounds are preloaded by storing them as class attributes in the entities that will use them. This will work because these class attributes are evaluated right after the script, or module, is first loaded by Python. In a more complex game with more assets to load, a more sophisticated preloading mechanism that provides feedback to the player is probably warranted.

Let's modify the :class:`PlayerShip` class to load some sounds:

.. literalinclude:: blasteroids3.py
   :pyobject: PlayerShip
   :end-before: __init__

We can play the death sound when the player's ship is destroyed, by adding a line to the :meth:`on_collide` method:

.. literalinclude:: blasteroids3.py
   :pyobject: PlayerShip.on_collide
   :end-before: player_died

The thrust sound is a looping sound. It should loop continously so long as the thrust is on and stop as soon as the thrust is off. This is accomplished by some simple modifications to the :meth:`thrust_on` and :meth:`thrust_off` methods to play and pause the thrust sound:

.. literalinclude:: blasteroids3.py
   :pyobject: PlayerShip.thrust_on
.. literalinclude:: blasteroids3.py
   :pyobject: PlayerShip.thrust_off

The gun sound is a bit more involved. Since the :class:`PlayerShip` class does not fire the gun directly, we will not actually play the sound here. We need to provide the sound to the :class:`Gun` system, so that it can play it when the gun actually fires. A good way to do this is to store the sound in a field of the gun component. We can modify the :class:`PlayerShip` constructor to do this like so::

    def __init__(self, world):
        ...
        self.gun.cool_down = self.GUN_COOL_DOWN
        self.gun.sound = self.GUN_SOUND


For this to work, we will need to reconfigure the gun component in the :class:`GameWorld` class, adding a :attr:`sound` field::

		class GameWorld(grease.World):

			def configure(self):
				"""Configure the game world's components, systems and renderers"""
				...
				self.components.gun = component.Component(
					firing=bool, 
					last_fire_time=float, 
					cool_down=float, 
					sound=object)
				...

By assigning a type of ``object`` to the :attr:`sound` field, we can assign any Python object to it, which is perfect for this purpose.

Last we need to modify the :class:`Gun` system to play the sound when the gun is fired (lines 8-9 below):

.. literalinclude:: blasteroids3.py
   :pyobject: Gun
   :linenos:

.. note:: Another viable solution would be to add this sound to the :class:`Shot` entity, but using the component is more flexible and illustrates how you can leverage object fields.

With some simple modifications to the :class:`Asteroid` entity class, we can add sounds when they explode. First let's load three hit sounds in a class attribute:

.. literalinclude:: blasteroids3.py
   :pyobject: Asteroid
   :end-before: UNIT_CIRCLE

Then play one of these sounds at random when the asteroid is hit::

    def on_collide(self, other, point, normal):
        random.choice(self.HIT_SOUNDS).play()
        self.explode()
        self.delete()

It's amazing what an improvement these simple sound effects make to the game. These sounds were created using the brilliant, free 8-bit sound effect generator: sfxr. You can download it `for Windows <http://games.softpedia.com/get/Tools/sfxr.shtml>`_ , and `for Mac <http://mac.softpedia.com/get/Developer-Tools/cfxr.shtml>`_.

He Shoots, He Scores!
=====================

No self-respecting arcade game can show its face in public without scoring. How am I to know how much better I am than the next guy? Obviously we need to implement some scoring before going any further.

Currently when you shoot an asteroid, it is simply destroyed. This is not much of a challenge. Like the classic game, we need to make the asteroids break into fragments when they are hit. The smaller asteroid fragments will move faster than their parents and give the player more points when shot. Let's refactor the :class:`Asteroid` entity class to provide these features:

.. literalinclude:: blasteroids3.py
   :pyobject: Asteroid
   :linenos:

First some arguments are added to the constructor: :attr:`position`, :attr:`parent_velocity`, and :attr:`points` (line 14). If :attr:`position` is provided, it is used as the initial asteroid position rather than always having a random initial position (line 20). If :attr:`parent_velocity` is provided, it is added to the random velocity vector (line 22-23), this way fragments are influenced by their parent's movement. Last, we store the point value for the asteroid in a new :attr:`award` component (line 32). Of course we'll need to add this component to our :class:`GameWorld`::

    class GameWorld(grease.World):

        def configure(self):
            """Configure the game world's components, systems and renderers"""
            ...
            self.components.award = component.Component(points=int)
            ...

There's also some changes to :meth:`on_collide` above. On line 35, we check the size of the asteroid that was hit. If the asteroid is large enough it is split into fragments, otherwise it is destroyed. The larger asteroids are split into 2 asteroids half the size at the same position. The smaller asteroids are worth double the points of their parents.

Scoring and Levels
------------------

We now know how many points the asteroids are worth, but we still need to keep track of the game score for the player. Since the score goes with the game, we can add store it in the :class:`GameSystem` where we bind the keyboard controls. if we had a game with multiple simultaneous players all with separate scores, we might choose to store the scores in a component instead. 

We refactor :class:`GameSystem` adding some attributes and methods:

.. literalinclude:: blasteroids3.py
   :pyobject: GameSystem
   :end-before: player_died
   :linenos:

While we're at it, we're going to add in some background chime sounds. The chime sounds will increase in frequency over time to build tension. At the beginning of each level, the frequency of the chimes is reset. We load the chime sounds and setup some other timing attributes in lines 8-13.

In the :meth:`set_world` method (line 15), we add attributes for :attr:`level` number, remaining :attr:`lives` and accumulated :attr:`score`. At the end we also call a new method :meth:`start_level`, which we define next.

:meth:`start_level` (line 23) does what its name implies. It increments the level number, creates some asteroids (3 more each increasing level), and resets the chime sounds. Using :func:`itertools.cycle` is a simple way to create an infinite iterator that alternates between our two chime sounds.

Next we define a :meth:`chime` method to sound the chimes (line 32). This method plays the next chime sound, slightly reduces the chime interval, and schedules the next chime sound. We also opportunistically check if all of the asteroids have been destroyed. If so, we start a new level. The reason to do that here is to provide a small time between when the last asteroid is destroyed and when the next level begins. Alternately, we could override the :meth:`step` method and put this logic there, but this is a bit simpler, if a little less tidy.

The last new method we add here is :meth:`award_points` (line 41). This simply accepts an entity, checks if it provides any points, and adds it to the total score if so. The :func:`hasattr` check on line 43 is a simple way to check if an entity has a particular component value. If the entity is not a member of the :obj:`award` component, this will return ``False``. 

We want to get points when the player shoots things. This means we need to call the :meth:`award_points` when a shot collides with something. Adding the call to the :class:`Shot` class' :meth:`on_collide` method does the trick::

    class Shot(grease.Entity):
        """Pew Pew!"""
        ...
.. literalinclude:: blasteroids3.py
   :pyobject: Shot.on_collide

Remember that :meth:`award_points` does the right thing if the other entity has points associated with it or not. That means the caller can just pass in whatever entity the shot runs into without additional logic.


