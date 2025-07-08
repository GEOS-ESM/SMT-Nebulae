from mpi4py import MPI
import numpy as np
import cupy as cp

if MPI.COMM_WORLD.Get_rank() == 0:
    A = np.zeros((2, 2))
    B = np.zeros((2, 2))
    MPI.COMM_WORLD.Isend(A, 1)
    MPI.COMM_WORLD.Irecv(B, 1)
elif MPI.COMM_WORLD.Get_rank() == 1:
    A = np.ones((2, 2))
    B = np.ones((2, 2))
    MPI.COMM_WORLD.Irecv(B, 0)
    MPI.COMM_WORLD.Isend(A, 0)
else:
    raise RuntimeError(f"Too many ranks, needs 2 got {MPI.COMM_WORLD.Get_size()}")


MPI.COMM_WORLD.Barrier()

print(f"CPU @ {MPI.COMM_WORLD.Get_rank()}:\n{A}\n{B}")

if MPI.COMM_WORLD.Get_rank() == 0:
    A = cp.zeros((2, 2))
    B = cp.zeros((2, 2))
    MPI.COMM_WORLD.Isend(A, 1)
    MPI.COMM_WORLD.Irecv(B, 1)
else:
    A = cp.ones((2, 2))
    B = cp.ones((2, 2))
    MPI.COMM_WORLD.Irecv(B, 0)
    MPI.COMM_WORLD.Isend(A, 0)


MPI.COMM_WORLD.Barrier()

print(f"GPU @ {MPI.COMM_WORLD.Get_rank()}\n{A}\n{B}")
