MPI is a complicated beast, conjuring thoughts of grey-beards sitting in front
of amber screens, typing Fortran code that runs in distant, dark computing
halls.

But it's not like that!  MPI is something that anyone can use!  If you have
code that would normally `fork()` (or `clone()`) itself, but your single
machine does not have enough CPU cores to meet your needs, MPI is a way to run
the same code across multiple machines, without needing to think about setting
up or coordinating IPC.

The code and docs in this repository are targeted at Python developers, and
will take you from zero to running a simple MPI Python script!

# Quick Start

Start with an Ubuntu Bionic (18.04) system, and run these commands to install
software and run this code!

```
git clone https://github.com/akkornel/mpi4py.git
sudo -s
apt install python3-mpi4py
echo 'btl_base_warn_component_unused = 0' > /etc/openmpi/openmpi-mca-params.conf 
exit
cd mpi4py
mpirun -n 20 python3 mpi4.py
```

See it in action:
[![asciicast](https://asciinema.org/a/gd64eQj99Tnvew9q27Ia9ciXe.svg)](https://asciinema.org/a/gd64eQj99Tnvew9q27Ia9ciXe?autoplay=1)

The Python code is simple: It has one 'controller', and one or more 'workers':

1. The controller generates a random number, and broadcasts it to everyone.

2. Each worker has a unique ID (its "rank"), and the hostname of the machine
   where it is running.  The worker receives the random number, adds its rank,
   and sends the result (the new number) and its hostname back to the
   controller.

3. The controller "gathers" all of the results (which come to it sorted by
   rank), and displays them.  The output includes an "OK" if the math (random
   number + rank) is correct.

The Python code is simple: it does not have to deal with launching workers, and
it does not have to set up communications between them (inter-process
communications, or IPC).

The above example showed 20 copies of mpi4.py, all running on the local system.
But, if you have two identical machines, you can spread the workers out across
all hosts, without any changes:

[![asciicast](https://asciinema.org/a/K05Tqig8AcbFv68O1qlSDFwbd.svg)](https://asciinema.org/a/K05Tqig8AcbFv68O1qlSDFwbd?autoplay=1)

If you have access to a compute environment running SLURM, you can let SLURM do
all of the work for you:

[![asciicast](https://asciinema.org/a/XyPGpX7gTG5ZrEWWQ4KS3OzEl.svg)](https://asciinema.org/a/XyPGpX7gTG5ZrEWWQ4KS3OzEl?autoplay=1)

Read on for information on the technologies that make all this work, and how to
try it for yourself!

# Behind the Scenes

Behind the above example, there are many moving pieces.  Here is an explanation
of each one.

## MPI

MPI is an API specification for inter-process communication.  The specification
defines bindings for both C/C++ and Fortran, which are used as the basis for
other languages (in our case, Python).  MPI provides for many IPC needs,
including…

* Bi-directional communication, both blocking and non-blocking

* Scatter-gather and broadcast communication

* Shared access to files, and to pools ("windows") of memory

The latest published version of the standard is
[MPI-3.1](https://www.mpi-forum.org/docs/mpi-3.1/mpi31-report.pdf), published
June 4, 2015.  MPI specification versions have an "MPI-" prefix to distinguish
them from implementation versions.  Specifications are developed by the [MPI
Forum](https://www.mpi-forum.org).

MPI is interesting in that it only specifies an API; it is up to other groups
to provide the implementations of the API.  In fact, MPI does not specify
things like encodings, or wire formats, or even transports.  The implementation
has full reign to use (what it feels is) the most efficient encoding, and to
support whatever transport it wants.  Most MPI implementations support
communications over Infiniband (using native Infiniband verbs) or TCP
(typically over Ethernet).  Newer implementations also support native
communication over modern 'converged' high-performance platforms, like
[RoCE](http://www.mellanox.com/related-docs/whitepapers/WP_RoCE_vs_iWARP.pdf).

Because each MPI implementation has control over how the MPI API is
implemented, a given "world" of programs (or, more accurately, a world of
copies of a single program) must all use the same MPI implementation.

## OpenMPI

[OpenMPI](https://www.open-mpi.org/) is an implementation of the MPI API,
providing libraries and headers for C, C++, Fortran, and Java; and supporting
interfaces from TCP to Infiniband to RoCE.  OpenMPI is fully
[open-source](https://github.com/open-mpi/ompi), with contributors from
adademic and research fields (IU, UT, HPCC) to commercial entities (Cisco,
Mellanox, and nVidia).  It is licensed under the 3-clause BSD license.  Your
Linux distribution probably has it packaged already.

**NOTE**: When running OpenMPI for the first time, you may get a warning which
says "A high-performance Open MPI point-to-point messaging module was unable to
find any relevant network interfaces".  That is OpenMPI complaining that it is
not able to find anything other than a basic Ethernet interface.

To suppress the warning about no high-performance network interfaces, edit the
file at path `/etc/openmpi/openmpi-mca-params.conf`, and insert the line
`btl_base_warn_component_unused = 0`.

## Python

As this is a Python demonstration, you will need Python!  MPI has been around
for a long time, and so many versions of Python are supported.  The code in
this repo works with Python 2.7, and also Python 3.5 and later.

The Python code in this repository includes type annotations.  To run in Python
2.7, you will need to install the
[typing](https://pypi.org/project/typing/) package (it comes as part of the
standard library in 3.5 and later).

## mpi4py

There are no MPI implementations written specifically for Python.  Instead, the
[mpi4py](https://pypi.org/project/mpi4py/) package provides a Python wrapper
around your choice of MPI implementation.  In addition, mpi4py provides two
ways to interface with MPI: You can provide binary data (as a `bytes` string or
a `bytearray`); or you can provide a Python object, which mpi4py will serialize
for you (using `pickle`).  This adds a massive convenience for Python
programmers, because you do not have to deal with serialization (other than
ensuring your Python objects are pickleable).

**WARNING**: Although mpi4py will handle serialization for you, you are still
responsible for checking what data are being received.  It is your code running
at the other end, but you may not be sure exactly what state the other copy is
in right now.

**NOTE**: If you plan on building mpi4py yourself, you should be aware that MPI
was created at a time when
[`pkg-config`](https://www.freedesktop.org/wiki/Software/pkg-config/) did not
exist.  Instead of storing things like compiler flags in a `.pc` file, it
provides a set of wrapper scripts (`mpicc`, and the like), which you should
call instead of calling the normal compiler programs.  The commands are built
as part of a normal OpenMPI installation, and mpi4py's `setup.py` script knows
to use them, and so `pip install --user mpi4py` should work.

## Tested Configurations

The code in this repository was tested by the author on the following
OS, OpenMPI, and mpi4py configurations, on an x64 platform:

* Ubuntu 16.04.6

  OpenMPI 3.0.0 (built from upstream) was used in all tests.

  mpi4py version 3.0.2 (built from upstream) was used in all tests.  The
  Ubuntu-supplied version (1.10.2-8ubuntu1) was tested, but reliably crashed
  with a buffer overflow.

  The above software was tested in the following Python versions:

  * Python 2.7 (2.7.12-1~16.04)

  * Python 3.5 (3.5.1-3)

  * Python 3.6.8 from upstream

  * Python 3.7.3 from upstream

* Ubuntu 18.04.2

  OpenMPI 2.1.1 (2.1.1-8) was used in all tests.

  mpi4py 2.0.0 (2.0.0-3) was used in all tests.

  The above software was tested in the following Python versions:

  * Python 2.7 (2.7.15~rc1-1).

  * Python 3.6 (3.6.7-1~18.04).

# Running

You can run this demonstration code multiple ways.  This documentation explains
how to run directly (with `mpirun`).  This works automatically on one machine,
and can be configured to run on multiple machines.  Information is also
provided for people with access to a SLURM environment.

## mpirun

The easiest way to run your code is with the `mpirun` command.  This command,
run in a shell, will launch multiple copies of your code, and set up
communications between them.

Here is an example of running `mpirun` on a single machine, to launch five
copies of the script:

```
akkornel@machine1:~/mpi4py$ mpirun -n 5 python3 mpi4.py
Controller @ MPI Rank   0:  Input 773507788
   Worker at MPI Rank   1: Output 773507789 is OK (from machine1)
   Worker at MPI Rank   2: Output 773507790 is OK (from machine1)
   Worker at MPI Rank   3: Output 773507791 is OK (from machine1)
   Worker at MPI Rank   4: Output 773507792 is OK (from machine1)
```

The `-n` (or `-np`) option specifies the number of MPI tasks to run.

Note above how all of the MPI tasks ran on the same machine.  If you want to
run your code across multiple machines (which is probably the reason why you
came here!), there are some steps you'll need to take:

* All machines should be running the same architecture, and the same versions
  of OS, MPI implementation, Python, and mpi4py.

  Minor variations in the version numbers may be tolerable (for example, one
  machine running Ubuntu 18.04.1 and one machine running Ubuntu 18.04.2), but
  you should examine what is different between versions.  For example, if one
  machine is running a newer mpi4py, and that version fixed a problem that
  applies to your code, you should make sure mpi4py is *at least* that version
  across all machines.

* There should be no firewall block: Each host needs to be able to communicate
  with each other host, on any TCP or UDP port.  You can limit the ports used,
  but that is out of the scope of this quick-start.

* SSH should be configured so that you can get an SSH prompt on each machine
  without needing to enter a password or answer a prompt.  In other words,
  you'll need public-key auth configured.

* The code should either live on shared storage, or should be identical on all
  nodes.

  `mpirun` will not copy your code to each machine, so it needs to be present
  at the same path on all nodes.  If you do not have shared storage available,
  one way to ensure this is to keep all of your code in a version-controlled
  repository, and check the commit ID (or revision number, etc.) before
  running.

Assuming all of those conditions are met, you just need to tell `mpirun` what
hosts to use, like so:

```
akkornel@machine1:~/mpi4py$ cat host_list
machine1
machine2
akkornel@machine1:~/mpi4py$ mpirun -n 5 --hostfile host_list python3 mpi4.py
Controller @ MPI Rank   0:  Input 1421091723
   Worker at MPI Rank   1: Output 1421091724 is OK (from machine1)
   Worker at MPI Rank   2: Output 1421091725 is OK (from machine1)
   Worker at MPI Rank   3: Output 1421091726 is OK (from machine2)
   Worker at MPI Rank   4: Output 1421091727 is OK (from machine2)
```

OpenMPI will spread out the MPI tasks evenly across nodes.  If you would like
to limit how many tasks a host may run, add `slots=X` to the file, like so:

```
machine1 slots=2
machine2 slots=4
```

In the above example, machine1 has two cores (or, one hyper-threaded core) and
machine2 has four cores.

**NOTE**: If you specify a slot count on *any* machine, `mpirun` will fail if
you ask for more slots that what is available.

And that's it!  You should now be up and running with MPI across multiple
hosts.

## SLURM

Many compute environments, especially in HPC, use the
[SLURM](https://slurm.schedmd.com) job scheduler.  SLURM is able to communicate
node and slot information to programs that use MPI, and in some MPI
implementations SLURM is able to do all of the communications setup on its own.

With SLURM, there are two ways of launching our MPI job.  The first is to use
`srun`, launching the job in a synchronous fasion (that was shown in the
example at the top of this page).  The second is to use `sbatch`, providing a
batch script that will be run asynchronously.

Regardless of the method of execution (that is, regardless of the SLURM command
we run), we will need to tell SLURM what resources we will require:

* **Time**.  Our job takes less than five minutes to complete.

* **Number of Tasks**.  This is the equivalent to the `-n` option for `mpirun`.
  We need to specify how many MPI tasks to run.

* **CPUs/cores**.  Our code is single-threaded, so this is "1 per task".

* **Memory**.  We are running a single Python interpreter in each task, but
  let's overestimate and say "512 MB per core".  Note that SLURM specifies
  memory either per core or per node, not per task.

Note that in our request we never specified how many machines to run on.  As
long as all machines have access to the same storage (which is normal in a
compute environment), we do not care exactly where our program runs.  All of
our tasks may run on a single machine, or they may be spread out across
multiple machines.

Note also that SLURM has support for many different MPI implementations, but in
some cases, special care may need to be taken.  For OpenMPI, nothing special is
required: SLURM supports OpenMPI natively, and OpenMPI supports SLURM by
default.  More information on other MPI implementations is available [from
SLURM](https://slurm.schedmd.com/mpi_guide.html).  To see which MPIs are
supported by your SLURM environment, run the command `srun --mpi list`.  You
can check the default by looking at the environment's `slurm.conf` file (which
is normally located in `/etc` on each machine).  The setting is named
"MpiDefault".

In the examples which follow, we will always be requesting at least two nodes.

## Synchronous SLURM with salloc

Running "synchronously" means you submit the work to SLURM, and you wait for
results to come back.  Any messages output by your code (for example, via
standard output or standard error) will be displayed in the terminal.

To run synchronously, we use the `srun` command, like so:

```
akkornel@rice15:~/mpi4py$ module load openmpi/3.0.0
akkornel@rice15:~/mpi4py$ srun --time 0:05:00 --ntasks 10 --cpus-per-task 1 --mem-per-cpu 512M --nodes 2-10 python3 mpi4.py
Controller @ MPI Rank   0:  Input 3609809428
   Worker at MPI Rank   1: Output 3609809429 is OK (from wheat09)
   Worker at MPI Rank   2: Output 3609809430 is OK (from wheat10)
   Worker at MPI Rank   3: Output 3609809431 is OK (from wheat11)
   Worker at MPI Rank   4: Output 3609809432 is OK (from wheat12)
   Worker at MPI Rank   5: Output 3609809433 is OK (from wheat13)
   Worker at MPI Rank   6: Output 3609809434 is OK (from wheat14)
   Worker at MPI Rank   7: Output 3609809435 is OK (from wheat15)
   Worker at MPI Rank   8: Output 3609809436 is OK (from wheat16)
   Worker at MPI Rank   9: Output 3609809437 is OK (from wheat17)
```

In the above example, OpenMPI is provided via an [Lmod
module](https://lmod.readthedocs.io/en/latest/), instead of a system package.
We have already built mpi4py using that version of OpenMPI.  So, before running
our code, we first load the same OpenMPI module used to build mpi4py.

(We don't need to run `module load` on the remote system, because Lmod modules
do their work by manipulating environment variables, which SLURM copies over to
the compute nodes.)

Once that is complete, we use the `srun` command to run our job.  SLURM finds
enough nodes to run our job, runs it, and prints the contents of standard
output and standard error.

Note that the above example assumes OpenMPI is configured as SLURM's default
MPI.   If not , you can provide `--mpi=openmpi` to the `srun` command, to force
it to use native OpenMPI.

## SLURM batch jobs with sbatch

When running as a batch job, most of the resource options should be specified
in the script that is provided to `sbatch`.  That script should include (via
`##SBATCH` special comments) all of the resource-setting options that you
previously included in the `srun` command line, *except* for `--ntasks` (and
possibly also `--time`).

Since the code supports any number of workers (as is typical for an MPI
program), you should provide `--ntasks` on the `sbatch` command-line, so that
you can adjust it to fit your current needs.

This example uses the sbatch script included in this repository.  Ten workers
are requested.

```
akkornel@rice15:~/mpi4py$ sbatch --ntasks 10 mpi4.py.sbatch
Submitted batch job 1491736
akkornel@rice15:~/mpi4py$ sleep 10
akkornel@rice15:~/mpi4py$ squeue -j 1491736
             JOBID PARTITION     NAME     USER ST       TIME  NODES NODELIST(REASON)
akkornel@rice15:~/mpi4py$ cat slurm-1491736.out
Controller @ MPI Rank   0:  Input 3761677288
   Worker at MPI Rank   1: Output 3761677289 is OK (from wheat08)
   Worker at MPI Rank   2: Output 3761677290 is OK (from wheat08)
   Worker at MPI Rank   3: Output 3761677291 is OK (from wheat08)
   Worker at MPI Rank   4: Output 3761677292 is OK (from wheat08)
   Worker at MPI Rank   5: Output 3761677293 is OK (from wheat08)
   Worker at MPI Rank   6: Output 3761677294 is OK (from wheat08)
   Worker at MPI Rank   7: Output 3761677295 is OK (from wheat08)
   Worker at MPI Rank   8: Output 3761677296 is OK (from wheat08)
   Worker at MPI Rank   9: Output 3761677297 is OK (from wheat08)
```

When SLURM launches the job, the batch script is executed on one of the nodes
allocated to the job.  The batch script is responsible for setting up the
environment (in this case, loading the OpenMPI module), and then executing
`srun`.  Note that in the batch script, `srun` does not have any command-line
options (except for `--mpi`); `srun` is able to recognize that it is running
inside a batch job, and will automatically scale itself to use all of the
resources available.

That's it!  Without having to change any Python code, your work is now being
run via a job scheduler, with all of the resource scheduling and IPC facilities
manged for you.

# Where to go next?

This was only a dip of the toe into the world of MPI.  To continue on, you
should first access the [mpi4py
documentation](https://mpi4py.readthedocs.io/en/stable/).  As most MPI
publications provide their code in C, the mpi4py docs will guide you on how to
convert that C code into Python calls.  You can also use the built-in help
system, like so:

```
akkornel@rice13:~$ python3.5
Python 3.5.2 (default, Nov 12 2018, 13:43:14)
[GCC 5.4.0 20160609] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from mpi4py import MPI
>>> mpi_comm = MPI.COMM_WORLD
>>> help(mpi_comm.Get_rank)
Help on built-in function Get_rank:

Get_rank(...) method of mpi4py.MPI.Intracomm instance
    Comm.Get_rank(self)

    Return the rank of this process in a communicator
```

The mpi4py docs also has a tutorial, which you should read!

Now that is done, the next thing to do is to think of a problem, and to try
solving it using MPI!  Focus on a problem that can be parallelized easily.

The Lawrence Livermore National Lab has a tutorial on MPI, featuring some
exercises that you can try.  For example, try [going to the
tutorial](https://computing.llnl.gov/tutorials/mpi/) and skipped ahead to the
_Point to Point Communication Routines_ section, which guides you through one
of the ways of calculating the digits of Pi.

Other tutorials include Rajeev Thakur's [Introduction to
MPI](https://courses.cs.washington.edu/courses/csep524/13wi/Thakur-MPI.pdf)
slide deck, which has been condenced by Brad Chamberlain of the University of
Washington (for a course there); and the [MPI for
Dummies](https://htor.inf.ethz.ch/teaching/mpi_tutorials/ppopp13/2013-02-24-ppopp-mpi-basic.pdf)
slide deck, created for the [PPoPP
conference](https://conf.researchr.org/series/PPoPP).

If you are interested in spreading your MPI code out across multiple machines,
you might want to set up a SLURM environment.  First, get some shared storage
by setting up an NFS server (in
[Ubuntu](https://help.ubuntu.com/community/SettingUpNFSHowTo), or you could use
[Amazon EFS](https://aws.amazon.com/efs/) or [Google Cloud
Filestore](https://cloud.google.com/filestore/)).  Then, check out the [SLURM
Quick Start](https://slurm.schedmd.com/quickstart_admin.html).  On RPM-based
systems, the quick-start walks you through creating RPMs; on Debian-based
systems, the packages are already available under the name "slurm-llnl".

Once you are done with all that, start looking at nearby universities and
research institutions.  They may have a job opening for you!

# Copyright & License

The contents of this repository are Copyright © 2019 the Board of Trustees of
the Leland Stanford Junior University.

The code and docs (with the exception of the `.gitignore` file) are licensed
under the GNU General Public License, version 3.0.
