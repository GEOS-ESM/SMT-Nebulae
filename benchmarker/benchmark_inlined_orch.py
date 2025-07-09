import dace
from ndsl.dsl.dace.orchestration import orchestrate, dace_inhibitor
from cuda_timer import TimedCUDAProfiler


class BenchmarkMe:
    def __init__(self, dace_config, d_sw):
        orchestrate(obj=self, config=dace_config)
        self._d_sw = d_sw
        self.timings = {}
        self._timer = TimedCUDAProfiler("topline", self.timings)

    @dace_inhibitor
    def _start_timer(self):
        self._timer.__enter__()

    @dace_inhibitor
    def _end_timer(self):
        self._timer.__exit__([], [], [])

    def __call__(
        self,
        inputs: dace.compiletime,
        iteration: dace.compiletime,
        dt,
    ):
        for _ in dace.nounroll(range(iteration)):
            self._start_timer()
            self._d_sw(
                inputs["delpc"],
                inputs["delp"],
                inputs["pt"],
                inputs["u"],
                inputs["v"],
                inputs["w"],
                inputs["uc"],
                inputs["vc"],
                inputs["ua"],
                inputs["va"],
                inputs["divgd"],
                inputs["mfx"],
                inputs["mfy"],
                inputs["cx"],
                inputs["cy"],
                inputs["crx"],
                inputs["cry"],
                inputs["xfx"],
                inputs["yfx"],
                inputs["q_con"],
                inputs["zh"],
                inputs["heat_source"],
                inputs["diss_est"],
                dt,
            )
            self._end_timer()
