import itertools
from dataclasses import dataclass, field
from typing import Any, Iterable, List, Optional

import click
import numpy as np
import plotly.graph_objects as go

from tcn.benchmark.geos_log_parser import parse_geos_log
from tcn.benchmark.raw_data import BenchmarkRawData
from tcn.hws.graph import energy_envelop_calculation


@dataclass
class BenchmarkReport:
    setup: str = ""
    per_backend_per_metric_comparison: List[Any] = field(default_factory=list)
    per_backend_gridcomp_breakdown_fig: str = ""  # html figures

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        s = self.setup + "\n"
        for bmc in self.per_backend_per_metric_comparison:
            for key, value in bmc.items():
                s += f"{key}:\n  {value}\n"
        return s


def _index_in_profiling(parent, profilings) -> int:
    for i, (shortname, _, _) in enumerate(profilings):
        if parent == shortname:
            return i
    return -1


def sankey_plot_of_gridcomp(raw_data: BenchmarkRawData, filename: str, title: str):
    sources = []
    targets = []
    values = []
    for i, (_shortname, value, parent) in enumerate(
        raw_data.fv_gridcomp_detailed_profiling
    ):
        if parent == "":
            continue
        sources.append(
            _index_in_profiling(parent, raw_data.fv_gridcomp_detailed_profiling)
        )
        targets.append(i)
        values.append(value)

    fig = go.Figure(
        data=[
            go.Sankey(
                # Define nodes
                node=dict(
                    pad=15,
                    thickness=15,
                    line=dict(color="black", width=0.5),
                    label=[
                        f"{shortname}:{measure}s"
                        for shortname, measure, _ in raw_data.fv_gridcomp_detailed_profiling
                    ],
                ),
                # Add links
                link=dict(source=sources, target=targets, value=values, label=values),
            )
        ]
    )
    fig.update_layout(title_text=title, font_size=10)
    fig.write_image(f"{filename}.png")


REPORT_TIME_KEY = "Time (in seconds)"
REPORT_COST_KEY = "Cost (in kW)"
REPORT_ENERGY_KEY = "Energy (in seconds.k$)"


def _comparison_in_X(value_A, value_B, label: str, unit: str = "s") -> str:
    if value_A > value_B:
        speed_up = value_A / value_B
        return (
            f"{label}: 1.00x ({value_A:.2f}{unit}) - "
            f"{speed_up:.2f}x ({value_B:.2f}{unit})\n"
        )
    else:
        speed_up = value_B / value_A
        return (
            f"{label}: {speed_up:.2f}x ({value_A:.2f}{unit}) -  "
            f"1.00x ({value_B:.2f}{unit})\n"
        )


def report(raw_data: List[BenchmarkRawData]) -> Optional[BenchmarkReport]:
    if raw_data == []:
        return None

    report = BenchmarkReport()

    # Setup check
    grid_resolution = raw_data[0].grid_resolution
    for bench_data in raw_data[1:]:
        if grid_resolution != bench_data.grid_resolution:
            raise RuntimeError(
                "Benchmark don't share the same grid: "
                f"{grid_resolution} != {bench_data.grid_resolution}"
            )

    report.setup = (
        "Experiment: \n"
        f"  Resolution: C{grid_resolution[0]}-L{grid_resolution[2]}\n"
        "   Layouts:\n"
    )

    for bench_data in raw_data:
        report.setup += (
            f"    - {bench_data.backend}:"
            f"{bench_data.node_setup[0]}x{bench_data.node_setup[1]}"
            f", {bench_data.node_setup[2]} ranks\n"
        )

    # Compute speed ups
    raw_backends_2by2 = itertools.combinations(raw_data, 2)
    for benchA, benchB in raw_backends_2by2:  # Time
        time_report = f"{benchA.backend} vs {benchB.backend}\n\n"
        time_report += _comparison_in_X(
            benchA.global_run_time, benchB.global_run_time, "Global RUN"
        )

        first_fv_timestep_A = benchA.fv_dyncore_timings[0]
        first_fv_timestep_B = benchB.fv_dyncore_timings[0]

        benchA_fvcomp_run = 0.0
        for key, value, _ in benchA.fv_gridcomp_detailed_profiling:
            if key == "RUN":
                benchA_fvcomp_run += value - first_fv_timestep_A
            elif key == "RUN2":
                benchA_fvcomp_run += value
        benchB_fvcomp_run = 0.0
        for key, value, _ in benchB.fv_gridcomp_detailed_profiling:
            if key == "RUN":
                benchB_fvcomp_run = value - first_fv_timestep_B
            elif key == "RUN2":
                benchB_fvcomp_run += value
        time_report += _comparison_in_X(
            benchA_fvcomp_run,
            benchB_fvcomp_run,
            "FV Grid Comp (1st timestep removed)",
        )

        benchA_dycore_median = np.median(benchA.fv_dyncore_timings)
        benchB_dycore_median = np.median(benchB.fv_dyncore_timings)
        time_report += _comparison_in_X(
            benchA_dycore_median,
            benchB_dycore_median,
            "Dycore (median)",
        )
        if benchA.inner_dycore_timings != [] and benchB.inner_dycore_timings != []:
            time_report += _comparison_in_X(
                np.median(benchA.inner_dycore_timings),
                np.median(benchB.inner_dycore_timings),
                "GT dycore (median)",
            )

        report.per_backend_per_metric_comparison.append({REPORT_TIME_KEY: time_report})

        # Energy
        if benchA.hws_data != {}:
            energy_report = f"{benchA.backend} vs {benchB.backend}\n\n"

            eReport = energy_envelop_calculation(
                benchA.hws_data["cpu_psu"],
                benchA.hws_data["gpu_psu"],
            )
            if benchA.backend == "fortran":
                benchA_global_kW_envelop = eReport.CPU_envelop_kWh
            else:
                benchA_global_kW_envelop = (
                    eReport.GPU_envelop_kWh + eReport.CPU_envelop_kWh
                )

            eReport = energy_envelop_calculation(
                benchB.hws_data["cpu_psu"],
                benchB.hws_data["gpu_psu"],
            )
            if benchB.backend == "fortran":
                benchB_global_kW_envelop = eReport.CPU_envelop_kWh
            else:
                benchB_global_kW_envelop = (
                    eReport.GPU_envelop_kWh + eReport.CPU_envelop_kWh
                )

            energy_report += _comparison_in_X(
                benchA_global_kW_envelop,
                benchB_global_kW_envelop,
                "Overall energy envelop",
                unit="kW",
            )
            report.per_backend_per_metric_comparison.append(
                {REPORT_ENERGY_KEY: energy_report}
            )

    return report


@click.command()
@click.argument("geos_logs", nargs=-1)
def cli(geos_logs: Iterable[str]):
    benchmark_raw_data: List[BenchmarkRawData] = []
    for log in geos_logs:
        benchmark_raw_data.append(parse_geos_log(log))
    r = report(benchmark_raw_data)
    print(r)
    for raw_data in benchmark_raw_data:
        if raw_data.fv_gridcomp_detailed_profiling != []:
            sankey_plot_of_gridcomp(
                raw_data,
                f"FVGridComp_breakdown_{raw_data.backend_sanitized}",
                f"FV Grid Comp for {raw_data.backend}",
            )
    for raw_data in benchmark_raw_data:
        x = np.arange(len(raw_data.fv_dyncore_timings))
        fig = go.Figure(data=go.Scatter(x=x[1:], y=raw_data.fv_dyncore_timings[1:]))
        fig.write_image(f"dyncore_verif_{raw_data.backend}.png")


if __name__ == "__main__":
    cli()
