# Introduction to NDSL

The NDSL is a Python based middleware which allows users to accelerate their code while
simultaneously gaining access to CPU or GPU execution.

NDSL relies heavily on the performance capabilities delivered by
[GT4Py](https://gridtools.github.io/gt4py/latest/index.html), but wraps many of the GT4Py features
with more user friendly interfaces and introduces its own set of features and optimization
techniques. For this reason, it is recommended that anyone trying to learn NDSL focus on this user
manual as a first point of contact, and only refer to the GT4Py documentation when absolutely
necessary.

NDSL - like all DSL's - is powerful because it is restrictive. Every degree of freedom added
exponentially increases optimisation difficulty, and ultimately decreases performance.
NDSL has numerous features designed to make the development process smoother, but there will
inevitably be situations where old code needs to be altered and conceptual foundations need
to be reformed to align with the NDSL framework.

With this effort; however, comes significant benefit. Below are a few examples of the performance
gains achieved with NDSL:

PERFORMANCE GAINS HERE

## By the end of this guide, you will:
- [Learn about the unique storage objects used by NDSL](./data.md)
- [Possess a foundational understanding of the core concepts of GT4Py](./stencil_function_basics.md)
- [Move on to more advanced techniques](advanced_stencil_features.md)
- [Discuss some common patters and their implementation](./common_patterns.md)
- [Illustrate the importance of using classes and other object oriented coding practices](./why_use_classes.md)