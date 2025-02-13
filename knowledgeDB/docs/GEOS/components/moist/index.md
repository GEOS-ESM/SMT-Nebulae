# GEOS moist component

- **Component name** `GEOSmoist_GridComp`
- **NDSL port name** `pyMoist`
- **Sub-directory** [`GEOSgcm_GridComp/GEOSagcm_GridComp/GEOSphysics_GridComp/GEOSmoist_GridComp`](https://github.com/GEOS-ESM/GEOSgcm_GridComp/tree/dsl/develop/GEOSagcm_GridComp/GEOSphysics_GridComp/GEOSmoist_GridComp)
- **NDSL port** [`GEOSgcm_GridComp/GEOSagcm_GridComp/GEOSphysics_GridComp/GEOSmoist_GridComp/pyMoist`](https://github.com/GEOS-ESM/GEOSgcm_GridComp/tree/dsl/develop/GEOSagcm_GridComp/GEOSphysics_GridComp/GEOSmoist_GridComp/pyMoist)

## Notes on the Port

### Dead code

- Aer Activation (`GEOSmoist_GridComp/aer_actv_single_moment.F90`)
The pre-loop before computation in

```f90
!--- determining aerosol number concentration at cloud base
DO j=1,JM
  DO i=1,IM
       k            = kpbli(i,j)
       tk           = T(i,j,k)              ! K
       press        = plo(i,j,k)            ! Pa
       air_den      = press*28.8e-3/8.31/tk ! kg/m3
ENDDO;ENDDO
```
