#!/bin/bash
# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 et

# Copyright © 2019 The Board of Trustees of the Leland Stanford Junior University.
# SPDX-License-Identifier: GPL-3.0-only

# This shows how you can run mpi4.py via a SLURM batch script.
# It was written by A. Karl Kornel <akkornel@stanford.edu>

# Set some of the job's resource requirements.
# This requires that you have access to at least two nodes.
# The main thing missing from here is --ntasks, the number of tasks to run.
# This should be set as part of running `sbatch`.
# You might also need to set things like --partition or --qos.
##SBATCH --time 0:05:00
##SBATCH --cpus-per-task 1
##SBATCH --mem-per-cpu 512M
##SBATCH --nodes 2-

# This batch script will run on one of the compute nodes.
# You could actually do this interactively, if you ran `srun` with all of the
# SLURM options that are mentioned above (`srun --time 0:05:00 … /bin/bash`).
# The environment in which this batch script runs has all of the
# information (via SLURM_* environment variables) to leverage resources on
# all of the nodes.  It does this by calling either `srun` or `mpirun`.

# First, bring things into our environment.
# This batch script is set up for Stanford's FarmShare environment,
# so we just bring in OpenMPI.  You might need to bring in Python.
# Or, maybe you don't need to load anything!
module load openmpi/3.0.0

# What Python do we run?  Either set the PYTHON_PROGRAM environment variable,
# or we will default to whatever `python3` happens to be.
# We support Python 2.7, and Python 3.5 or later.
PYTHON_PROGRAM=${PYTHON_PROGRAM:-python3}

# What MPI runner do we use?
# This is important, because it sets up all of the inter-process communications,
# on both this node and all of the other nodes running this job.
# We prefer letting SLURM handle MPI setup, via `srun --mpi=openmpi`.
# But, you can override it by setting the RUN_COMMAND environment variable.
# NOTE that SLURM's slurm.conf specifies a default MPI to use (in case `--mpi`
# is not specified).  FarmShare has "openmpi" set as the default, so we really
# don't need to include `--mpi`.
# If the default doesn't work, try one of these:
#   srun
#   srun --mpi=pmi2
#   srun --mpi=pmi
#   mpirun
# NOTE that if you use mpirun, make sure your MPI has SLURM support built in.
# (This is normally the case for OpenMPI.)
RUN_COMMAND=${RUN_COMMAND:-srun --mpi=openmpi}

# Run it!
exec ${RUN_COMMAND} ${PYTHON_PROGRAM} mpi4.py
