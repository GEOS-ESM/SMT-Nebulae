# Tutorials

## What is NDSL?

The NASA/NOAA Domain Specific Language (NDSL) is a Python based middleware which allows users to accelerate
their code and seamlessly switch between
CPU and GPU execution. To achieve this, NDSL leverages the functionality of
[GT4Py](https://gridtools.github.io/gt4py/latest/index.html) and optimization
capabilities of [DaCe](https://spcldace.readthedocs.io/en/latest/index.html) to creating a smooth,
unified user experience which allows for easy development of grid-based models.

NDSL has extensive documentation, and this should serve as a first point of reference for questions about
the system; however, it is important to note that GT4Py and DaCe also have their own
sets of documentation, and these may be useful - particularly for more nuanced applications.

NDSL - like all DSL's - is powerful because it is restrictive. Every degree of freedom added
exponentially increases optimization difficulty, and ultimately lowers performance ceilings.
While this software has numerous features designed to make the development process smoother, there will
inevitably be situations where desired patterns fail to align seamlessly with core concepts of this language.
In those moments, it is important to remember that these patterns were "banned" because their implementation
would dramatically reduce (or, in some cases, completely eliminate) the create a nimble, efficient
executable product.

The requirement to (occasionally) rethink old methods may occasionally be a significant request; however,
with it comes significant benefit. Below are a few examples of the performance gains achieved with NDSL:

PERFORMANCE GAINS HERE

**NDSL User Manual**

A user manual has been compiled for NDSL. This guide has been designed to introduce important concepts and
establish a solid foundation required to use NDSL. For that reason, it is highly recommended that you look
through this guide before working with NDSL. 

## What is GEOS

The Goddard Earth Observing System (GEOS) is the flagship Earth system model developed by NASA
Goddard Space Flight Center. Traditionally developed and run in Fortran, this model brings together
numerous components - atmopshere, ocean, radiation, land surface, chemistry, etc. - to 
create a complete picture of the Earth's dynamic systems. Development is led by the
[GMAO](https://gmao.gsfc.nasa.gov), with support from numerous public and private partners.
More information is available [here](https://gmao.gsfc.nasa.gov/geos-systems/).

## FAQ

For questions which are not answered by the tutorials, please check the list of
[frequently asked questions (FAQ)](faq.md). Additional questions can be submitted here FORM LINK HERE.
