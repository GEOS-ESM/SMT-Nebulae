# HPC metrics

In collaboration with the NCCS, we are listing below a range of metrics that should be evaluated for each benchmark.

Time to solution

- Despite not aiming for production-ready code by the end of the project, we will still keep an eye on the "job-level" turn around and document improvement and potential non-numerics slowdown due to the technology swap.

Energy

- Light software sampling to document amplitude of TPU’s chip: imprecise but can be easily ran with little overhead.
- Hardware monitoring on selected runs for precise measure: precise but requires close cooperation with NCCS sys admin and IT.

Node-to-node

- Compare CPU node with GPU nodes
- Minimize generation difference for valid comparison

Node usage

- Chip usage: measure in % of theoretical throughput rather than FLOP/s
- Chip idle time: important for hybrid work

Minimal hardware requirements

- For developments
- For scientific runs
