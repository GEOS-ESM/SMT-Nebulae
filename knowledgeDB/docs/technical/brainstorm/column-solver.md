# Column solver

## Description

Starting with Remapping, UW, then GF, we are encountering a case of column solver that is ill-fitted to the stencils script. E.g.:

- I and J have no dependancies,
- multiple scans of the column, with bounds that are calculated (Fields),
- break out of the solver for a column - but keep going on the other columns (other Ks).

Code generation should look something like

```python
for i, j in [I, J]:
    while keep_solving or iteration < N:
        for k in ...
            ...
            keep_solving = False
        if not keep_solving:
            break
        for k in ... / if not keep_solving
        for k in ... / if not keep_solving
        for k in ... / if not keep_solving

```

On top of this, we would need a system capable of:

- breaking into seperate stencils,
- dealing with different grids (interpolation).

Questions:

- On top of breaking out of the column, should we also be able to skip over a piece of code but _not_ all code.

## Solutions

### Dynamic intervals

The first feature is dynamic intervals. E.g.

```python
with computation(...), interval(scalar, field):
    ...
```

### FOR IJ -> WHILE SOLVE -> MANY Ks

The pattern means that IJ is independant and we need to insert a while between potentially many Ks. Other issue is that we need a concept that extends over multiple stencils to be able to organize code properly (e.g. orchestration).

#### Pure `DaCe`

```python
for i, j in dace.map[:I, :J]:
    while error[i, j]:
        kbcon[i, j] = start_level[i,  j]
        for k in dace.map[:K]:
            ...
            error[i, j] = 0
            break
        if error[i, j]:
            break
        ...
```

📈 Pros

- Support for all needed system
- Can fold _some_ concept into our own API
- Natively orchestratable

📉 Cons

- Slow in "stencil" mode
- Introducing absolute indexing by default vs relative in stencils
- Too generic, will be used for everything
- Can't insert stencils - everything will need to be pure DaCe
- Loose "cartesian" optimization because the maps become generic (maybe salvageable if we can somehow pass metadata...)
- DaCe parsing failures are difficult to parse

#### `gt4py.cartesian` Column solver

```python
@solver.stencil
def A():
    with computation(FORWARD):
        with interval(...):
            ...
            BREAK_FROM_SOLVER

@solver
def solver()
    with ColumnSolver(FLAG or ITERATION < N):
        A(kbcon, hcot)
        B(kbcon, hcot)
```

📈 Pros

- Keep within the "known" interface to write numerics (relative indexing...)
- Retain all the known boundaries and capacity to tool, complete control
- Retain capacitoy for "cartesian" bespoke optimization (we control the application, context, meaning...)
- Naively orchestratable (all work happens upstream)

📉 Cons

- This is orchestration-adjacent, the line becomes blurry
- Introducing an entire new concept, lots of work (how can we re-use a maximum of concepts?)

#### `gt4py.next`

They have solved some and/or all of it for `Icon4Py` - can we integrate?

## Examples

### PChem - Interpolator

Linear interpolation from a larger field to a smaller one, with variou checks on third fields and calculation post interpolation.

=== "Pseudo code"

    ```text
    For all latitudes on SMALL FIELD grid
        For all levels on SMALL FIELD grid
            Find the two value of BIG FIELD that surrounds the given level at lat
            Interpolate linearly BIG FIELD value
                Clamp if needed
        For all longitudes on SMALL FIELD grid
            Find the two value of BIG FIELD that surrounds the given level at long
            Interpolate linearly BIG FIELD value
                Clamp if needed
    ```

=== "Python "

    ```python
    for j in range(jm):
        for k in range(n_levs):
            self.temporaries.PROD.field[:, j, k] = interp.interp_no_extrap(
                OX_list=lats.field[:, j],
                IY=prod1[:, k],
                IX=pchem_lats[:],
            )
        for i in range(im):
            self.temporaries.PROD_INT.field[i, j, :] = interp.interp_no_extrap(
                OX_list=self.temporaries.PL.field[i, j, :],
                IY=self.temporaries.PROD.field[i, j, :],
                IX=pchem_levs.field[:],
            )
    
    def interp_no_extra():
        max_index = len(IX)
        OY = []

        for i, ox in enumerate(OX_list):
            # Find the interval index J such that IX[J] <= OX <= IX[J+1]
            J = min(max(np.count_nonzero(IX <= OX), 1), IX.size - 1) - 1

            # Linear interpolation
            if IX[J + 1] != IX[J]:
                OY = IY[J] + ((OX - IX[J]) / (IX[J + 1] - IX[J])) * (IY[J + 1] - IY[J])

            else:
                OY = IY[J]
           
            if OX_list[i] <= IX[0]:
                OY[i] = IY[0]

            if OX_list[i] >= IX[max_index - 1]:
                OY[i] = IY[max_index - 1]
        
        return OY
    ```

### GF Small solver

=== "Pseudo code"

    ```text
    Per column (independant over K)
        We are looking for KBCON (2D) - a K level
        Open-ended iterative solver (if do not error)
        From start_level to a MAX
            Calculate HCOT (3D)
        Move KBCON up until HCOT(kbcon) > HESO_CUP and <= KBMAX
        If KBCON is KBMAX
            We failed. We exit the solver, flagging an error.
        Calculate some DEPTH_BUOY (2D)
        If DEPH_BUOY < CAP
            Success. We found KBCON. Exit - no error.
        For the next try (2D)
            We calculate a new HCOT
            Start from one level up than last time (start_level+1)
    ```

=== "GT4Py + ColumnSolver"

    ```python
    @solver.stencil
    def A(kbon, hcot):
        with computation(FORWARD):
            with interval(0, 1):
                kbcon = start_level

            with interval(kbcon + 1, KBMAX + 3):
                ...
                hcot = hcot[K-1] + ...

            # Not great
            with interval(hcot[0, 0, kbcon] , HESO_cup[0, 0, kbcon]):
                kbcon = kbcon + 1
                if error == 0 and hcot < HESO_cup(0, 0, kbcon) and kbon > kbmax + 2:
                    error = 3
                    BreakFromColumn

    @solver.stencil
    def B(kbon, hcot):
        with computation(FORWARD):
            with interval(0, 1):
                depth_neg_buoy = ...
                if cap_max > depth_neg_buoy:
                    BreakFromColumn

            with interval(0, 1):
                k22 = k22 + 1
                x_add = (xlv*zqexec+cp*ztexec) +  x_add_buoy
                get_cloud_bc(...)
                start_level = start_level +`1


    @solver
    def solver():
        with ColumnSolver(COLUMN_IS_UNSOLVED or ITERATION < N) as mask:
            A(kbcon, hcot)
            B(kbcon, hcot)
            
    ```
=== "Fortran"

    ```fortran
    !--- DETERMINE THE LEVEL OF CONVECTIVE CLOUD BASE  - KBCON
    !
    loop0: DO i=its,itf
            !-default value
            kbcon         (i)=kbmax(i)+3
            depth_neg_buoy(i)=0.
            frh           (i)=0.
            if(ierr(i) /= 0) cycle


    loop1:  DO WHILE(ierr(i) == 0)

                kbcon(i)=start_level(i)
                do k=start_level(i)+1,KBMAX(i)+3
                    dz=z_cup(i,k)-z_cup(i,k-1)
                    hcot(i,k)= ( (1.-0.5*entr_rate(i,k-1)*dz)*hcot(i,k-1)     &
                                    + entr_rate(i,k-1)*dz *heo (i,k-1) ) / &
                                (1.+0.5*entr_rate(i,k-1)*dz)
                    if(k==start_level(i)+1) then
                    x_add    = (xlv*zqexec(i)+cp*ztexec(i)) + x_add_buoy(i)
                    hcot(i,k)= hcot(i,k) +  x_add
                    endif
                enddo

    loop2:      do while (hcot(i,kbcon(i)) < HESO_cup(i,kbcon(i)))
                    kbcon(i)=kbcon(i)+1
                    if(kbcon(i).gt.kbmax(i)+2) then
                        ierr(i)=3
                        ierrc(i)="could not find reasonable kbcon in cup_kbcon : above kbmax+2 "
                        exit loop2
                    endif
                    !print*,"kbcon=",kbcon(i);call flush(6)
                enddo loop2

                IF(ierr(i) /= 0) cycle loop0

                !---     cloud base pressure and max moist static energy pressure
                !---     i.e., the depth (in mb) of the layer of negative buoyancy
                depth_neg_buoy(i) = - (po_cup(i,kbcon(i))-po_cup(i,start_level(i)))

                IF(MOIST_TRIGGER == 1) THEN
                    frh(i)=0. ; dzh = 0
                    do k=k22(i),kbcon(i)
                    dz     = z_cup(i,k)-z_cup(i,max(k-1,kts))
                    frh(i) = frh(i) + dz*(qo(i,k)/qeso(i,k))
                    dzh    = dzh + dz
                    !print*,"frh=", k,dz,qo(i,k)/qeso(i,k)
                    enddo
                    frh(i) = frh(i)/(dzh+1.e-16)
                    frh_crit =frh_crit_O*xland(i) + frh_crit_L*(1.-xland(i))

                !fx     = 2.*(frh(i) - frh_crit) !- linear
                !fx     = 4.*(frh(i) - frh_crit)* abs(frh(i) - frh_crit) !-quadratic
                    fx     = ((2./0.78)*exp(-(frh(i) - frh_crit)**2)*(frh(i) - frh_crit)) !- exponential
                    fx     = max(-1.,min(1.,fx))

                    del_cap_max = fx* cap_inc(i)
                    cap_max(i)  = min(max(cap_max_in(i) + del_cap_max, 10.),150.)
                !print*,"frh=", frh(i),kbcon(i),del_cap_max, cap_max(i),  cap_max_in(i)
                ENDIF

                !- test if the air parcel has enough energy to reach the positive buoyant region
                if(cap_max(i) > depth_neg_buoy(i)) cycle loop0


    !--- use this for just one search (original k22)
    !            if(cap_max(i) < depth_neg_buoy(i)) then
    !                    ierr(i)=3
    !                    ierrc(i)="could not find reasonable kbcon in cup_cloud_limits"
    !            endif
    !            cycle loop0
    !---

                !- if am here -> kbcon not found for air parcels from k22 level
                k22(i)=k22(i)+1
                !--- increase capmax
                IF(USE_MEMORY == 20) cap_max(i)=cap_max(i)+cap_inc(i)

                !- get new hkbo
                x_add = (xlv*zqexec(i)+cp*ztexec(i)) +  x_add_buoy(i)
                call get_cloud_bc(name,kts,kte,ktf,xland(i),po(i,kts:kte),heo_cup (i,kts:kte),hkbo (i),k22(i),x_add,Tpert(i,kts:kte))
                !
                start_level(i)=start_level(i)+1
                !
                hcot(i,start_level(i))=hkbo (i)
            ENDDO loop1
            !--- last check for kbcon
            if(kbcon(i) == kts) then
                ierr(i)=33
                ierrc(i)="could not find reasonable kbcon in cup_kbcon = kts"
            endif
        ENDDO loop0
    ```
