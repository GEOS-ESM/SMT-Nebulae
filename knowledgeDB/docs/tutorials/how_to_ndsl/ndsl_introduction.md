# Introduction to NDSL

The NASA/NOAA Domain Specific Language (NDSL) is a Python based middleware which allows users to accelerate
their code and seamlessly switch between
CPU and GPU execution. To achieve this, NDSL leverages the functionality of
[GT4Py](https://gridtools.github.io/gt4py/latest/index.html) and optimization
capabilities of [DaCe](https://spcldace.readthedocs.io/en/latest/index.html) to creating a smooth,
unified user expeirence which allows for easy development of grid-based models.

NDSL has extensive documentation, and this should serve as a first point of reference for questions about
the system; however, it is important to note that GT4Py and DaCe also have their own
sets of documentation, and these may be useful - particularly for more nuanced applications.

NDSL - like all DSL's - is powerful because it is restrictive. Every degree of freedom added
exponentially increases optimisation difficulty, and ultimately lowers performance ceilings.
While this software has numerous features designed to make the development process smoother, there will
inevitably be situations where desired patterns fail to aligh seamlessly with core concepts of this language.
In those moments, it is important to remember that these patterns were "banned" because their implementation
would dramatically reduce (or, in some cases, completely eliminate) the create a nimble, effecient
executable product.

The requirement to (occationally) rethink old methods may - and is - a significant request; however, with it
comes significant benefit. Below are a few examples of the performance gains achieved with NDSL:

PERFORMANCE GAINS HERE

This user manual introduces relevant concepts and provides knowledge needed to use NDSL. By the end of this
guide, you will:

- [Learn about the unique storage objects used by NDSL](./data.md)
- [Possess a foundational understanding of the core concepts of GT4Py](./writing_ndsl_code.md)
- [Move on to more advanced techniques](advanced_stencil_features.md)
- [Discuss some common patters and their implementation](./common_patterns.md)
- [Illustrate the importance of using classes and other object oriented coding practices](./why_use_classes.md)

This guide is not a FAQ or a replacement for proper documentation. These resources are available [LINK(s) HERE]