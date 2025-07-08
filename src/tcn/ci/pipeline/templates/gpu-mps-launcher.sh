#!/bin/sh

# USAGE: mpirun/srun -n N gpu-mpi-wrapper my_executable args1 args 2

# For debug of this script
#set -x

HOSTNAME=`hostname`
if [ ${OMPI_COMM_WORLD_LOCAL_RANK:0} ]; then
    LOCAL_RANK=$OMPI_COMM_WORLD_LOCAL_RANK
elif [ ${SLURM_LOCALID:0} ]; then
    LOCAL_RANK=$SLURM_LOCALID
else
    if [ $LOCAL_RANK -eq 0 ]; then
        echo "Unimplemented MPI environement, can't read local rank. Exiting."
    fi
    exit 1
fi

# Hardware sampling is a python tools that reads at intervals
# various hardware sensors (power, usage, memory load...)
if [ -z ${HARDWARE_SAMPLING} ]; then
    if [ $LOCAL_RANK -eq 0 ]; then
        echo "Hardware sampling is OFF"
    fi
else
    if [ $LOCAL_RANK -eq 0 ]; then
        echo "Hardware sampling is ON"
    fi
    # We restrict usage to (world) rank 0
    if [ $SLURM_PROCID -eq 0 ]; then
        geosongpu_hws server &
        sleep 10
        geosongpu_hws client start
    fi
fi

# Nvidia's Multi Process Service required to run multiple processed
# at the same time on one GPU

# We open GPU visibility to full node at first
export CUDA_VISIBLE_DEVICES=0,1,2,3

if [ -z ${MPS_ON} ]; then
    if [ $LOCAL_RANK -eq 0 ]; then
        echo "MPS is OFF"
    fi
    # No MPS, we assume rank==GPU
    GPU=$LOCAL_RANK
    export CUDA_VISIBLE_DEVICES=$GPU
else
    if [ $LOCAL_RANK -eq 0 ]; then
        echo "MPS is ON"
    fi
    if [ -z ${PER_DEVICE_PROCESS} ]; then
        if [ $LOCAL_RANK -eq 0 ]; then
            echo "PER_DEVICE_PROCESS needs to be setup on MPS. Exiting."
        fi
        exit 1
    fi
    # All ranks needs to know where to look
    export CUDA_MPS_PIPE_DIRECTORY=./nvidia-mps/$HOSTNAME
    export CUDA_MPS_LOG_DIRECTORY=./nvidia-log/$HOSTNAME
    # Only 1 rank per node (local rank 0) handles the server chatter
    if [ $LOCAL_RANK -eq 0 ]; then
        echo "Turn nvidia-cuda-mps-control on for node $HOSTNAME"
        mkdir -p $CUDA_MPS_PIPE_DIRECTORY
        mkdir -p $CUDA_MPS_LOG_DIRECTORY
        # sudo nividia -i 0 -c 3 # Per docs, we should insure GPU is in EXCLUSIVE mode but we might be curtail by HPC settings
        nvidia-cuda-mps-control -d
    fi
    # MPS server is socket base, leave time for the filesystem
    sleep 3
    # Server should be spun, we restrict this rank to a single GPU
    GPU=$((LOCAL_RANK/PER_DEVICE_PROCESS))
    export CUDA_VISIBLE_DEVICES=$GPU
fi

echo "Node: $HOSTNAME | Rank: $LOCAL_RANK, pinned to GPU: $CUDA_VISIBLE_DEVICES"

# Run program with or without log dump in file
if [ -z ${LOCAL_REDIRECT_LOG} ]; then
    $*
else
    $* > log.redirect_local.$HOSTNAME.$LOCAL_RANK.out 2>&1
fi

# Clean up of all tools
if [ -z ${HARDWARE_SAMPLING} ]; then
    echo ""
else
    if [ $LOCAL_RANK -eq 0 ]; then
        geosongpu_hws client dump
        geosongpu_hws client stop
    fi
fi
if [ -z ${MPS_ON} ]; then
    echo ""
else
    if [ $LOCAL_RANK -eq 0 ]; then
        echo quit | nvidia-cuda-mps-control
        # sudo nividia -i 0 -c 0 # Per docs, we should insure GPU is flipped back to DEFAULT mode but we might be curtail by HPC settings
    fi
fi
