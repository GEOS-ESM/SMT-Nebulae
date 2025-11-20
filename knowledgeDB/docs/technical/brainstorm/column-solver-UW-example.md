# ⚠️ Column solver to replace `go to`

In the context of porting physics parameterizations, we have encountered multiple examples of Fortran `go to`, in which a condition is met and code jumps to a particular line of code, skipping all of the computations in between for that column. 
 
The goal is to expand the DSL to be able to port these features. We have begun experimenting with a potential solution here: [link to Column Solver examples].

## Context

While porting physics parametrizations, we found several examples of Fortran `go to`. At present, they have ported using various workarounds that range in complexity. The goal is to undo this workaround that complexifies calling code.

##### Example 1
In the example below, from the UW shallow convection scheme [link to uwshcu.F90], a `go to` is used to exit a loop if a certain condition is met:

```fortran
    do k = 0, k0
        if( pifc0(k) .lt. plcl ) then
            klcl = k
            go to 25
        endif
    end do
    klcl = k0
        
25  continue

    klcl = max(1,klcl)
```

This can be written in the DSL using a simple workaround:

```python
with computation(FORWARD), interval(...):
    k = 0
    klcl_flag = 0.0
    while lev < k0 + 1 and klcl_flag == 0.0:
        if pifc0.at(K=k) < plcl:
            klcl = k
            klcl_flag = 1.0
        k += 1

    if klcl_flag == 0.0:
        klcl = 0

    klcl = max(0, klcl)
```

Other cases we have seen of Fortran `go to` are not as simple and require more complex workarounds. For these complex cases, we are seeking a new DSL feature to help simplify porting.

##### Example 2
In the example below, when `go to 333` is triggered, the code jumps to `333` and skips over hundreds of lines of computations at a particular column. 


```fortran
do i = 1, idim
    do iter = 1, iter_cin
    
        math...

        plcl = qsinvert(qtsrc,thlsrc,pifc0(0))

        do k = 0, k0
            if( pifc0(k) .lt. plcl ) then
                klcl = k
                go to 25
            endif
        end do
        klcl = k0
        
25      continue
        
        klcl = max(1,klcl)

        if( plcl .lt. 60000. ) then               
            id_exit = .true.
            go to 333
        endif

        math...

    enddo
    
    math...

333     continue

math...

enddo
```

This feature cannot be easily replicated with a simple workaround, like the example above. Instead, the current solution is to apply a masking technique, so that when `go to 333` is triggered, the stencil computations are finished for that column.

In the code below, `condensation` is a `BoolFieldIJ` mask that is set to False by default. When `go to 333` is triggered, `condensation` is set to True for that column. Then, we must check `if not condensation` for all subsequent computations. While this workaround gets the job done, it can be tedious and unattractive.

```python
with computation(FORWARD), interval(...):
    if not condensation:
        plcl = qsinvert(qtsrc, thlsrc, pifc0.at(K=0), ese, esx)
        lev = 0
        klcl_flag = 0.0
        while lev < k0 + 1 and klcl_flag == 0.0:
            kidx = lev
            if pifc0.at(K=kidx) < plcl:
                klcl = lev
                klcl_flag = 1.0
            lev += 1

        if klcl_flag == 0.0:
            klcl = 0

        klcl = max(0, klcl)

        if plcl < 60000.0:
            condensation = True
```

## Proposed solution

The proposed solution is a ColumnSolver that would follow this general structure:

```python
@solver.stencil
def A():
    with computation(FORWARD):
        with interval(...):
            ...
            BREAK_FROM_SOLVER

@solver
def solver()
    with ColumnSolver(not condensation):
        A(...)
```

📈 Pros

- Keep within the "known" interface to write numerics (relative indexing...)
- Retain all the known boundaries and capacity to tool, complete control
- Retain capacitoy for "cartesian" bespoke optimization (we control the application, context, meaning...)
- Naively orchestratable (all work happens upstream)

📉 Cons

- This is orchestration-adjacent, the line becomes blurry
- Introducing an entire new concept, lots of work (how can we re-use a maximum of concepts?)

### Example
```python
    @solver.stencil
    def A(...):
        with computation(FORWARD):
            with interval(...):
                plcl = qsinvert(qtsrc, thlsrc, pifc0.at(K=0), ese, esx)
                lev = 0
                klcl_flag = 0.0
                while lev < k0 + 1 and klcl_flag == 0.0:
                    kidx = lev
                    if pifc0.at(K=kidx) < plcl:
                        klcl = lev
                        klcl_flag = 1.0
                    lev += 1

                if klcl_flag == 0.0:
                    klcl = 0

                klcl = max(0, klcl)

                if plcl < 60000.0:
                    condensation = True
                    BreakFromColumn


    @solver
    def solver():
        with ColumnSolver(not condensation) as mask:
            A(...)
            
```