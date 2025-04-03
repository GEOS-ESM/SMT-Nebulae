# Fields Bundle

To allow semantic manipulation of a group of fields, we propose to implement a base class `FieldBundle` which will provide API to name, group, filter and deliver semantically grouped fields on top of a contiguous 4D memory representation. We considered using Python's dictionnary but it won't fit the stencil-execution pattern, so we kept the underlying 4D and propose to build metadata and indexation on top.

## Context

Throughouts ESMs fields are semantically bundled together and transported on cartesian grid as 4D vectors. For example, Tracers have "water species", "aerosols", etc. In Fortran, the general mode of execution is:
    - Define a 4D field with IJK + 4th dimension
    - Use index to the last dimension as semantically relevant information (0 is "vapor", `1 is "ice")

This allows a few manipulation we have to replicate:
    - Blind iteration over all fields as 3D fields (loop over N fields with N size of 4th dimension)
    - Direct access to a particular field semantically relevant
    - Filtering on a subset of 3D fields (loop over N+x to N-y with x/y as relevant offsets)

Pros:
    - Single memory block to be moved around
    - Clear 4th dimension usage
    - Cache friendliness if the group/subgroups remain contiguous

Cons:
    - Code readability: indices or offset are difficult to read and pre-suppose to remember knowing correspondance

Another aspect of those code is the re-organization of 3D fields within a 4D sequence either for scientific use (sort the interesting tracers so they are next to each other and offseted loop can be used) or performance (reduce cache miss). Those operations are difficult to track in a codebase and easily forgotten in a methodology that often see the lower algorithmics (parameterization for example) and it's use in the larger model (driver) as seperated tasks.

Our proposition should aim at covering all use case, retain pros, improved on cons and allow advanced to tooling to detect memory manipulation (and/or forbid them).

## Decision

We propose to implement a base class `FieldBundle` with two main components:

- a 4D device-senstive memory space
- a complex 4th dimensional `indexer`, carrying metadata (names, groups)

The `indexer` operates on the memory and should have the following features:
  
- Access by name to a single 3D field (e.g. `bundle["vapor"]` or `bundle.vapor`)
- Filtering by groups to access a subset of the bundle (e.g. `bundle.groupby("water species")`)
- Sub-filtering a groups to access a subset of a given group (e.g. `bundle.groupby("water species").exclude(["rain", "ice"])`)
- Blind access to a 4D gt4py-capable field (e.g. `bundle` of type `FloatField` + Data Dimension)

The results will have to be `orchestratable` natively and allow for a quick and transparent access to 3D field as a `Quantity`.

Once the first iteration of this code is available, we shall endeavor how we can refactor `pyFV3`'s `State` concept which has overlapping features.

### Tooling / Features

- Ability to dump all fields in a `xarray.Dataset` with options for grouping, single field save, etc.

## Consequences

This will define a base class to be derived from. It will be implemented with pyFV3 (dynamics) and pySHiELD (physics) as workhorse. That strategy might narrow the field of design and miss importabnt APIs but it seems the pragmatic angle to ensure we do not over-engineer.

## Alternatives considered

N/A

## References

N/A
