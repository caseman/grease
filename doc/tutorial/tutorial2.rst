###############
Grease Tutorial
###############

.. _tut-chapter-2:

******************************
Chapter 2: Making a Game of it
******************************

In :ref:`chapter 1 <tut-chapter-1>` the basis was laid for the *Blasteroids* game, but it is far from complete or even playable. By the end of this chapter, we'll have rectified that. To start with, let's build on the techniques we used to create the :class:`Asteroid` class, and create an entity for the player's ship.

The start should look pretty familar, and even a bit simpler than the asteroids:

.. literalinclude:: blasteroids2.py
   :lines: 10-27

First we have some class attributes that configure various aspects of the ship, including thrust acceleration, turn rate, shape (vertex points) and color. Separating these out of the code makes them easier to tweak while testing the game, and also will allow us to refer to them from other code, which can be convenient.

It's probably difficult to envision the shape from just the vertex coordinates, so here's what the ship will look like renderered:

.. figure:: ship_shape.png
   :align: left
   :figwidth: 100

The shape has some intentionally duplicated vertices (the part labelled `flame`), so we can easily create a simple animated flame effect coming from the rear of the ship when the thrust is activated.

In the constructor, we setup the initial position and angle (centered and pointing up), stationary movement and rotation. Next the shape is initialized, this time with the :attr:`closed` field set to false since we have overlapping vertices in the shape. Last, we set the color. This puts the ship entity into all of the components we need for movement and rendering.

Unlike asteroids, the player's ship needs to be able to move dynamically in response to player inputs. Specifically, the ship needs to be able to turn (rotate) left and right, and accelerate forward in the direction it is facing to simulate thrust. Let's start with the turn method:

.. literalinclude:: blasteroids2.py
   :pyobject: PlayerShip.turn

This simple method lets us turn the ship left or right by supplying the proper direction value: -1 for turn left, 1 for turn right, 0 for straight ahead.

Let's move on to the thrust method:

.. literalinclude:: blasteroids2.py
   :pyobject: PlayerShip.thrust_on

This method accelerates the ship in the direction it is facing. We start by defining an upward-facing vector with a magnitude set to the class's :attr:`THRUST_ACCEL` value. This vector is then rotated in-place to face the direction of the ship using :meth:`Vec2d.rotate()`. The :attr:`accel` field of the entity's movment component is then set to the rotated thrust vector. The :class:`controller.EulerMovement` system, already in the world takes care of calculating the ship's velocity and position over time based on the acceleration. 

The last line changes one of the shape vertices, moving it to a random position behind the ship. This will create a simple flickering flame animation that will act as an import cue to the player that the thrust is active. Notice that the vertex is simply moved to a random position vertically relative to the origin, the renderer will automatically take care of translating and rotating the vertex to the proper window coordinates according to the ship's current position and rotation, as well as the current camera settings.

We will be wiring the :meth:`thrust()` method to fire every frame that the thrust key is held down. That way the acceleration vector will always be pointing in the right direction if the ship is also turning and the thrust flame will continuously flicker.

The last thing we need is a method to turn the ship's thrust off. We'll wire this up to fire when the thrust key is released:

.. literalinclude:: blasteroids2.py
   :pyobject: PlayerShip.thrust_off

This resets the ship's acceleration and flame tip vertex back to their original values.

Controlling the Ship
====================

None of the capabilities we've coded for the player's ship mean anything unless the player can control them. Here we are going to see how easy it is to wire up our game logic to the keyboard.

To do this, we are going to create our own custom :class:`grease.System` to house our top-level game state, logic, and keyboard bindings. Because the example game is simple, we can easily fit all of these things into a single system class.

Remember that systems are behavioral aspects of our application, and are invoked each time step. So they are the perfect place to define and glue together the logic for the game.

.. literalinclude:: blasteroids2.py
   :lines: 6-7
.. literalinclude:: blasteroids2.py
   :pyobject: GameSystem
   :end-before: @

We start by defining our :class:`GameSystem` as a subclass of :class:`KeyControls`. :class:`KeyControls` is a system subclass that provides a convenient mechanism for binding its methods to keyboard events.

The :meth:`set_world` method is overridden to include a call to create a :class:`PlayerShip` entity and store it in the game state. Since there is only one player ship, this is an easy way to keep track of it so that we can call it's methods in response to particular key presses. We make the entity here in this method -- instead of, say :meth:`__init__` -- because this method is called when the system is added to the world. Since we need a reference to the world in order to create an entity, this is the most convenient place to do so.

Next let's add a method to turn the ship left when either the "a" or left arrow keys are pressed:

.. literalinclude:: blasteroids2.py
   :lines: 72-76

The first thing of interest are the two decorators at the top. The :meth:`KeyControls.key_press` decorator binds a method to a key press event for a specific key. As you can see from the code, we can have multiple key binding decorators for a given method to bind it to multiple keys. The decorator method takes one or two arguments. The first argument is the Pyglet key code from :obj:`pyglet.window.key`. The second optional argument is to specify modifier keys (shift, alt, etc). By default, no modifier keys are assumed.

The logic in this method is quite simple. First we check that the :obj:`player_ship` entity exists. This ensures that the entity has not been deleted from the world before we use it. Just holding a reference to an entity does not prevent it from being deleted. In this way entity references in your code are like weak references. This check will prove useful when the player ship can be destroyed later on. Next we call the ship entity's :meth:`turn_left` method we defined earlier passing it a direction of -1.

Next we add a complimentary method to stop turning left:

.. literalinclude:: blasteroids2.py
   :lines: 78-82

The decorators here bind this method to the key release event for the same keys. The methods check for the existence of the entity as above, but also that it is currently turning left (negative rotation). This is to properly handle simultaneous key presses, e.g., left down, right down, then left up.

The methods for handling turning right are the same as above with the direction reversed:

.. literalinclude:: blasteroids2.py
   :lines: 84-94

Now let's define the methods for handling thrust:

.. literalinclude:: blasteroids2.py
   :lines: 96-106

For activating thrust, we use the :meth:`KeyControls.key_hold` decorator. This works differently than the key press and release decorators we used for turning. The press and release decorators configure a method to fire once for each specific key event. The key hold decorator configures a method to fire continuously, once per time step, as long as the specified key is held down. This is perfect for thrust, which needs to be adjusted continously as the ship turns, and runs a continuous animation while activated.

The :meth:`stop_thrust` method is simply bound to key release, to ensure the thrust is deactivated at the proper time.

With the key control logic code in place, the next step is to add the :class:`GameSystem` to our :class:`GameWorld`'s systems (Line #11 below):

.. literalinclude:: blasteroids2.py
   :pyobject: GameWorld
   :linenos:

We also modify the :func:`main` function to push the system's event handler onto the game window so that it receives the key events (Line #7 below):

.. literalinclude:: blasteroids2.py
   :pyobject: main
   :linenos:

Now we can control the ship and fly it around the screen.

.. image:: flying_around.png

Running Into Stuff
==================

Flying around is way too safe at the moment, since you can't actually run into anything! Let's see what we can do about that. Implementing collision requires that we add a component and a system to the :class:`GameWorld`: 

.. literalinclude:: blasteroids2.py
   :pyobject: GameWorld
   :linenos:

The :class:`component.Collision` component (line 9 above) has the fields we need to make the collision system (line 13-14 above) work. The fields in this component are:

`aabb`
    This is the axis-aligned bounding box that contains the entity. This box is used in the collision detection system to quickly reduce the number of collision checks that need to be performed. We can also use it for our own purposes when we need to find the top, left, bottom or right edges of entities.

`radius`
   The meaning of this field is up to the specific collision system used. For :class:`collision.Circular` systems, entities are approximated as circles for the purposes of collision detection. The radius value is simply the radius of the collision circle for an entity.

`from_mask` and `into_mask`
   Not all entities in the collision component need to be able to collide with each other. These two mask fields let you specify which entities can collide. Both mask fields are 32 bit integer bitmasks. When two entities are compared for collision, the :attr:`from_mask` value from each entity is bit-anded with the :attr:`into_mask` of the other. If this bit-and operation returns a non-zero result, then a collision is possible, if the result is zero, the entities cannot collide. Note that this happens in both directions, so a collision can occur between entity A and B if `A.collision.from_mask & B.collision.into_mask != 0 or B.collision.from_mask & A.collision.into_mask != 0`.

Let's take a closer look at how the collision system is configured above:

.. literalinclude:: blasteroids2.py
   :pyobject: GameWorld
   :start-after: self.systems.game
   :end-before: self.renderers.camera

There are two major steps to collision handling in Grease: *collision detection* and *collision response*. The detection step happens within the collision system. A set of pairs of the currently colliding entities can be found in the :attr:`collision_pairs` attribute of the collision system. Applications are free to use :attr:`collision_pairs` directly, but they can also register one or more handlers for more automated collision response. Collision handlers are simply functions that accept the collision system they are configured for as an argument. The handler functions are called each time step to deal with collision response.

Above we have configured :func:`grease.collision.dispatch_events` as the collision handler. This function calls :meth:`on_collide` on all entities that are colliding. The entities' :meth:`on_collide` handler methods can contain whatever logic desired to handle the collision. This method accepts three arguments: :attr:`other_entity`, :attr:`collision_point`, and :attr:`collision_normal`. These arguments are the other entity collided with, the point where the collision occured and the normal vector at the point of collision respectively. It is up to the handler method to decide how these values are used. Note that when two entities collide, both of their :meth:`on_collide` handler methods will be called, if defined.

In our game we will leverage the collision masks to make it so that the player's ship collides with asteroids, but the asteroids do not collide with each other. To do that we need to modify the :class:`Asteroid` and :class:`PlayerShip` constructors to set the collision component fields.

.. literalinclude:: blasteroids2.py
   :pyobject: PlayerShip
   :end-before: def turn

Lines 19-20 above initialize the collision settings for the player ship. Note that the radius is set slightly smaller than the farthest vertex in the shape (by 0.5 units). This is common when using circular collision shapes, it prevents the appearance of false positive collisions that can make the game feel unfair.

.. literalinclude:: blasteroids2.py
   :pyobject: Asteroid
   :linenos:

Lines 18-20 above setup collision for the asteroids. The radius is simply set to the asteroid's radius. The collision masks are configured so that the asteroids will collide with the player's ship, but not with each other.

To start with, will add a simple :meth:`on_collide` method to both the :class:`Asteroid` and :class:`PlayerShip` classes that simply delete the entities when they collide::

        def on_collide(self, other, point, normal):
            self.delete()

Blowing Stuff Up
================

When you run the game now, you'll notice that asteroids pass right through each other, but if you hit one with the ship, both the ship and asteroid disappear. This proves that the collision is working as expected, but it's not very interesting yet. What would really spice things up is some simple explosion effects when entities are destroyed. 

Here's what we need to implement to make this happen:

* A method to "explode" and entity into a bunch of debris fragments.

* A system that manages the debris, fading it out and cleaning it up over
  time.

Let's start with the :meth:`explode` method. Since asteroids and the player ship are basically the same except for their shape, they can share the method code. The most straightforward way to do this, is to create a common base class for both entities:

.. literalinclude:: blasteroids2.py
   :pyobject: BlasteroidsEntity
   :linenos:

We also define an entity class for the debris. This class defines no behavior of its own, it just serves to tag the debris entities so that we can easily manage them in the system we will be creating later:

.. literalinclude:: blasteroids2.py
   :pyobject: Debris

Let's take apart the :class:`BlasteroidsEntity` class and see how it works. In line 6 above, we take the base shape of the entity and transform it into a new shape, rotating it to the current angle of the entity that is exploding:

.. literalinclude:: blasteroids2.py
   :lines: 15

Next we create the debris. This is aided by the :meth:`shape.segments` method (line 7). This method returns an iterator of all of the individual line segments of the original shape as separate shapes. This effectively fragments our original entity shape. 

We loop over these fragment segments creating debris entities for each. The shape of each debris fragment is a single segment of the original entity's shape. We also set the initial position and velocity of the debris entity to that of the exploding entity (line 10-11). Next we add some random velocity outward from the exploding entity's position to make it "explode" (line 12). Because the base shapes are centered around the origin, we can just use one of the vertex positions to determine the approximate outward direction from the center. Normalizing the first vertex vector -- giving it a length of 1 -- and multiplying it by a random value gives us the desired outward push. A bit of random rotation adds a little spice to the effect (line 13). Last, we set the color of the debris to the same as the original entity so it appears to be pieces of the original.

