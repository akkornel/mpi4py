#!/bin/env python3
# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 et

# Copyright © 2019 The Board of Trustees of the Leland Stanford Junior University.
# SPDX-License-Identifier: GPL-3.0-only

"""
This file shows how to use MPI in Python, using the mpi4py package!
It was written by A. Karl Kornel <akkornel@stanford.edu>

You should run this, not with `python`, but with `mpirun`.
Or, you can run it in a SLURM job, using `srun` (or `mpirun`).
Read the README.md for more details!
"""

# Import MPI at the start, as we'll use it everywhere.
from mpi4py import MPI

# We'll need to query the environment
from os import environ

# We use type hints.  Do you use type hints?  You should use type hints.
# NOTE: This code is compatible with Python 2.7 and 3.5+.
# For Python 2.7, install `typing` from PyPI.
from typing import *

# Create a type variable for the types of MPI communicator objects we can use.
MPIComm = Union[MPI.Intracomm, MPI.Intercomm]

# Our main routine.  It sanity-checks MPI and calls the correct code.
def main():
    # type: () -> int
    """Executed when called via the CLI.

    Performs some sanity checks, and then calls the appropriate method.
    """

    # Get our MPI communicator, our rank, and the world size.
    mpi_comm = MPI.COMM_WORLD
    mpi_rank = mpi_comm.Get_rank()
    mpi_size = mpi_comm.Get_size()

    # Do we only have one process?  If yes, then exit.
    if mpi_size == 1:
        print('You are running an MPI program with only one slot/task!')
        print('Are you using `mpirun` (or `srun` when in SLURM)?')
        print('If you are, then please use an `-n` of at least 2!')
        print('(Or, when in SLURM, use an `--ntasks` of at least 2.)')
        print('If you did all that, then your MPI setup may be bad.')
        return 1

    # Is our world size over 999?  The output will be a bit weird.
    # NOTE: Only rank zero does anything, so we don't get duplicate output.
    if mpi_size >= 1000 and mpi_rank == 0:
        print('WARNING:  Your world size {} is over 999!'.format(mpi_size))
        print("The output formatting will be a little weird, but that's it.")

    # Sanity checks complete!

    # Call the appropriate function, based on our rank
    if mpi_rank == 0:
        return mpi_root(mpi_comm)
    else:
        return mpi_nonroot(mpi_comm)

# This program has two parts: The controller and the worker part.
# The controller is executed by rank 0; the workers by everyone else.
# SOME TERMINOLOGY:
# MPI World: All of the MPI processes, spawned by `mpirun` or SLURM/srun.
# MPI Size: The number of MPI slots (or SLURM tasks).
#     Within a SLURM job, this is the number of tasks (--ntasks) for the job.
#     Outside of a SLURM job, this is the `-n` option given to `mpirun`.
#     (Or, with `mpirun`, by providing a list of hosts on which to run.)
# MPI Rank: An integer number, in the range [0, MPI size).
#     The MPI rank is unique to each worker.

# This program follows the convention that rank 0 is the "controller", and all
# non-zero ranks are "workers".  This is important when using things like
# broadcast, or scatter/gather.  But if you are only doing simple send/receive
# (which we do not), then you don't need to stick to the controller-worker
# paradigm.  But it's still a good idea!

# Our code for rank 0
def mpi_root(mpi_comm):
    # type: (MPIComm) -> int
    """Routine for the controller (MPI rank 0).

    Generates a non-negative 32-bit number, and broadcasts it.
    Then, gathers responses from every other MPI rank.
    Each MPI rank should return a tuple of (string, int).
    The string is an MPI "CPU Identifier" (normally a hostname).
    The int is the result of `random_number + MPI_rank`.

    Once all results are gathered, output each result (the gathered array is
    sorted by MPI rank).  Verify that each int returned is correct, by doing
    the math (`returned int == random_number + MPI_rank`) locally.

    At the end, send each worker (via a unicast message) an `int` zero.  Then,
    wait for everyone to be at the same point in code (via a battier).  Then
    we're done!
    """

    # We import `random` here because we only use it here.
    import random

    # Get our random number, broadcast it, and print it to standard output.
    # NOTE: The lower-case methods (like `bcast()`) take Python object, and do
    # the serialization for us (yay!). 
    # `bast()` is blocking, in the sense that it does not return until
    # the data have been sent, but it is _not_ synchronizing.
    # There's also no guarantee as to _how_ the data were conveyed.
    # NOTE: In Python 3.6+, we should use `secret` instead of `random`.
    random_number = random.randrange(2**32)
    mpi_comm.bcast(random_number)
    print('Controller @ MPI Rank   0:  Input {}'.format(random_number))

    # Gather all of our responses
    # `gather()` takes a parameter, which for the root is `None`.
    # Again, from an MPI perspective this is blocking, and it is synchronizing
    # in the sense that we know all of workers have sent something.  But this
    # is still not proper synchronization.
    # NOTE: The returned array puts our parameter into slot 0.  So, the length
    # of the returned array should match the MPI world size.
    GatherResponseType = List[Tuple[str, int]]
    response_array = mpi_comm.gather(None) # type: GatherResponseType

    # Sanity check: Did we get back a response from everyone?
    mpi_size = mpi_comm.Get_size()
    if len(response_array) != mpi_size:
        print('ERROR!  The MPI world has {} members, but we only gathered {}!'
            .format(mpi_size, len(response_array))
        )
        return 1

    # Output each worker's results.
    # NOTE: We skip entry zero, because rank 0 is us, and we gathered `None`.
    for i in range(1, mpi_size):
        # Sanity check: Did we get a tuple of (string, int)?
        if len(response_array[i]) != 2:
            print('WARNING!  MPI rank {} sent a mis-sized ({}) tuple!'
                .format(
                    i,
                    len(response_array[i])
                )
            )
            continue
        if type(response_array[i][0]) is not str:
            print('WARNING!  MPI rank {} sent a tuple with a {} instead of a str!'
                .format(
                    i,
                    str(type(response_array[i][0]))
                )
            )
            continue
        if type(response_array[i][1]) is not int:
            print('WARNING!  MPI rank {} sent a tuple with a {} instead of an int!'
                .format(
                    i,
                    str(type(response_array[i][1]))
                )
            )
            continue

        # Is the result OK?  Check if random_number + i == response
        if random_number + i == response_array[i][1]:
            result = 'OK'
        else:
            result = 'BAD'

        # Output the message.
        # The first field `{: >3}` translates as...
        # `:  -> Take the next parameter from `format()`
        # ` ` -> Use spaces as the fill character
        # `>` -> Right-align
        # `3` -> Normal width is three characters
        print('   Worker at MPI Rank {: >3}: Output {} is {} (from {})'
            .format(
                i,
                response_array[i][1],
                result,
                response_array[i][0],
            )
        )

        # Send the worker a unidirectional MPI message, signifying
        # "You can exit now!".  But really, this is just showing off MPI
        # unidirectional messaging.
        # NOTE: This will be slow!  Since we have to (a) reach out to that
        # specific node, and (b) wait for that node to be ready to receive.
        mpi_comm.send(
            obj=0,
            dest=i,
            tag=0,
        )

    # Before we finish, do an MPI synchronization barrier.
    # This the only proper way of doing synrhconization with MPI.
    # Do we need it here?  Nope!  We're just showing it off.
    mpi_comm.barrier()

    # We're all done!
    return 0

# Our code for ranks 1 and up
def mpi_nonroot(mpi_comm):
    # type: (MPIComm) -> int
    """Routine for the MPI workers (ranks 1 and up).

    Receives a number from a broadcast.
    To that received number, add our MPI rank (a positive, non-zero integer).

    Return, via the gather process, a tuple with two items:
    * The MPI "CPU Identifier" (normally a hostname)
    * The calculated number, above.

    Then, enter a loop: We receive a number (an `int`) from the controller.  If
    the number is zero, we exit the loop.  Otherwise, we divide the number by
    two, convert the result to an int, and send the result to the controller.

    Finally, after the loop is over, we synchronize via an MPI barrier.
    """

    # Get our MPI rank.
    # This is a unique number, in the range [0, MPI_size), which identifies us
    # in this MPI world.
    mpi_rank = mpi_comm.Get_rank()

    # Get the number broadcast to us.
    # `bcast()` takes a parameter, but since we're not sending, we use `None`.
    # NOTE: This blocks until rank zero broadcasts something, but it's not
    # synchronizing, in that rank zero might have moved on already.
    # And again, no way to know exactly how this got to us.
    random_number = mpi_comm.bcast(None) # type: int

    # Sanity check: Did we actually get an int?
    if type(random_number) is not int:
        print('ERROR in MPI rank {}: Received a non-integer "{}" from the broadcast!'
            .format(
                mpi_rank,
                random_number,
            )
        )
        return 1

    # Our response is the random number + our rank
    response_number = random_number + mpi_rank

    # Return our response
    # `gather()` knows that we're not the root, and so we're returning.
    response = (
        MPI.Get_processor_name(),
        response_number,
    )
    mpi_comm.gather(response)

    # Receive a unidirectional message (an `int`) from the controller.
    # Every time we get a non-zero integer, we return `floor(int/2)`.
    # When we get a zero, we stop.

    # Move message-receiving into a helper.
    def get_message(mpi_comm):
        # type: (MPIComm) -> Union[int, None]
        message = mpi_comm.recv(
            source=0,
            tag=0,
        ) # type: int
        if type(message) is not int:
            print('ERROR in MPI rank {}: Received a non-integer message!'
                .format(
                    mpi_rank,
                )
            )
            return None
        else:
            return message

    # Start looping!
    message = get_message(mpi_comm)
    while (message is not None) and (message != 0):
        # Divide the number by 2, and send it back
        mpi_comm.send(
            obj=int(message/2),
            dest=0,
            tag=0,
        )

        # Get a new message
        message = get_message(mpi_comm)

    # Did we get an error?
    if message is None:
        return 1

    # Before we finish, do an MPI synchronization barrier.
    # This the only proper way of doing synrhconization with MPI.
    # Do we need it here?  Nope!  We're just showing it off.
    mpi_comm.barrier()

    # That's it!
    return 0

# Run main()
if __name__ == '__main__':
    import sys
    sys.exit(main())
