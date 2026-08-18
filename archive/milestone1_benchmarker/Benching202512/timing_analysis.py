import json
import numpy as np
import sys


with open(sys.argv[1]) as f:
    data = json.load(f)

Fortran = np.array(data["Fortran"])[1:]
NDSL = np.array(data["GFDL 1M Numerics"])[1:]
ALL = np.array(data["GFDL 1M"])[1:]
ALLvsFortran = ALL - Fortran
NDSLvsFortran = NDSL - Fortran
NDSLvsInterface = ALL - NDSL
PctDiffNDSLFromFortran = (NDSLvsFortran / Fortran) * 100.0
PctDiffAllFromFortran = (ALLvsFortran / Fortran) * 100.0
PctDiffCostOfInterface = (NDSLvsInterface / ALL) * 100.0

print(data["Header"])
print(f"Samples: {len(ALL)}")

print(f"\nFortran median runtime: {np.median(Fortran):.4f}")
print(f"NDSL median runtime: {np.median(NDSL):.4f}")
print(f"NDSL Interface median runtime: {np.median(NDSLvsInterface):.4f}")
print(f"NDSL + Interface median runtime: {np.median(ALL):.4f}")

print("\nNDSL vs Fortran difference in %, negative is faster")
print("\t\t\tMedian    Min     Max")
print(
    f" NDSL + Interface:\t{np.median(PctDiffAllFromFortran):.2f}"
    f" | {min(PctDiffAllFromFortran):.2f} "
    f" | {max(PctDiffAllFromFortran):.2f}"
)
print(
    f" NDSL:\t\t\t{np.median(PctDiffNDSLFromFortran):.2f}"
    f" | {min(PctDiffNDSLFromFortran):.2f}"
    f" | {max(PctDiffNDSLFromFortran):.2f}"
)
print("\n")
print(f"Cost of interface: {np.median(PctDiffCostOfInterface):.2f}% {np.median(NDSLvsFortran):.3f}s")


if "GFDL 1M DaCe Marshalling" in data.keys():
    NDSLDaCeMarshalling = np.array(data["GFDL 1M DaCe Marshalling"])[1:]
    PctDiffDaceMarshalling = (NDSLDaCeMarshalling / NDSL) * 100.0
    print(
        f"Cost of DaCe marshalling (part of runtime): {np.median(PctDiffDaceMarshalling):.2f}% {np.median(NDSLDaCeMarshalling):.4f}s"
    )
    print(f"    True runtime: {np.median(NDSL - NDSLDaCeMarshalling):.4f}s")
