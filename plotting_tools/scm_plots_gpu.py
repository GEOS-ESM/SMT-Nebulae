import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

# ===============================
# GLOBAL FONT SIZES
# ===============================
plt.rcParams.update({
    "font.size": 14,
    "axes.titlesize": 16,
    "axes.labelsize": 15,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 13
})

plt_profiles = True
timeseries = True
hovmoller = True

exp = "arm_97jun"
levs = "72"
param = "moist"

GPU_PATH = "/Users/kfandric/data/scm/discover/" + exp + "_dsl_" + levs
CPU_PATH = "/Users/kfandric/data/scm/discover/"

# ===============================
# LOAD DATA
# ===============================
runs = {
    "Fortran": xr.open_dataset(
        f"{CPU_PATH}/{exp}_{param}_multi_fortran_cpu_{levs}.nc4"
    ),
    "CPU": xr.open_dataset(
        f"{CPU_PATH}/{exp}_{param}_multi_dsl_cpu_{levs}.nc4"
    ),
    "GPU": xr.open_dataset(
        f"{GPU_PATH}/{exp}_{param}_multi_dsl_gpu_{levs}.nc4"
    ),
}

surf_runs = {
    "Fortran": xr.open_dataset(
        f"{CPU_PATH}/{exp}_{param}_surf_fortran_cpu_{levs}.nc4"
    ),
    "CPU": xr.open_dataset(
        f"{CPU_PATH}/{exp}_{param}_surf_dsl_cpu_{levs}.nc4"
    ),
    "GPU": xr.open_dataset(
        f"{GPU_PATH}/{exp}_{param}_surf_dsl_gpu_{levs}.nc4"
    ),
}

# ===============================
# COORDINATES
# ===============================
f90 = runs["Fortran"]

z = f90["lev"][::-1]
time = f90["time"]

# Simple numeric hour axis
time_hours_hov = np.arange(len(time))

# ===============================
# HELPERS
# ===============================
def time_mean(ds, var, t_start=None, t_end=None):

    da = ds[var]

    if t_start is not None:
        da = da.sel(time=slice(t_start, t_end))

    return da.mean(dim="time").values


def profile(ax, x, z, label, color,
            ls="-", marker=None):

    ax.plot(
        x,
        z,
        label=label,
        color=color,
        linestyle=ls,
        marker=marker,
        markersize=5,
        linewidth=2
    )

# ===============================
# TIME MEAN PROFILES
# ===============================
# variables = ["QV", "MU", "CLOUD", "QL", "PL", "T"]

# t_start = time[0]
# t_end = time[-1]

# profiles = {}

# for name, ds in runs.items():

#     profiles[name] = {}

#     for var in variables:

#         profiles[name][var] = time_mean(
#             ds,
#             var,
#             t_start,
#             t_end
#         )

# # ===============================
# # DERIVED VARIABLES
# # ===============================
# R_d = 287
# C_p = 1004
# Lv = 2.5E6

# derived = {}

# for name in runs.keys():

#     PL = profiles[name]["PL"][:, 0, 0]
#     T  = profiles[name]["T"][:, 0, 0]
#     QL = profiles[name]["QL"][:, 0, 0]
#     QV = profiles[name]["QV"][:, 0, 0]

#     rho = PL / (R_d * T)

#     LWC = QL * rho
#     QT  = QL + QV

#     p_adj = (100000 / PL) ** (R_d / C_p)

#     theta = T * p_adj
#     theta_l = theta - ((Lv / C_p) * QL)

#     derived[name] = {
#         "LWC": LWC,
#         "QT": QT,
#         "theta_l": theta_l
#     }

# colors = {
#     "Fortran": "k",
#     "CPU": "red",
#     "GPU": "blue"
# }

# # ===============================
# # PROFILE PLOTS
# # ===============================
# if plt_profiles and exp == "bomex":

#     fig, axs = plt.subplots(
#         2,
#         3,
#         figsize=(14, 12),
#         sharey=True
#     )

#     axs = axs.flatten()

#     # θl
#     ax = axs[0]

#     for name in runs:

#         profile(
#             ax,
#             derived[name]["theta_l"][::-1],
#             z,
#             name,
#             colors[name],
#             marker="o"
#         )

#     ax.set_title(r"$\theta_l$")
#     ax.invert_yaxis()
#     ax.legend()
#     ax.grid(alpha=0.3)

#     # qt
#     ax = axs[1]

#     for name in runs:

#         profile(
#             ax,
#             derived[name]["QT"][::-1],
#             z,
#             name,
#             colors[name],
#             marker="o"
#         )

#     ax.set_title(r"$q_t$")
#     ax.grid(alpha=0.3)

#     # QL
#     ax = axs[2]

#     for name in runs:

#         profile(
#             ax,
#             profiles[name]["QL"][:, 0, 0][::-1],
#             z,
#             name,
#             colors[name],
#             marker="o"
#         )

#     ax.set_title("QL")
#     ax.grid(alpha=0.3)

#     # CLOUD
#     ax = axs[3]

#     for name in runs:

#         profile(
#             ax,
#             profiles[name]["CLOUD"][:, 0, 0][::-1],
#             z,
#             name,
#             colors[name],
#             marker="o"
#         )

#     ax.set_title("Cloud Fraction")
#     ax.grid(alpha=0.3)

#     # LWC
#     ax = axs[4]

#     for name in runs:

#         profile(
#             ax,
#             derived[name]["LWC"][::-1],
#             z,
#             name,
#             colors[name],
#             marker="o"
#         )

#     ax.set_title("Grid-mean LWC")
#     ax.grid(alpha=0.3)

#     # MU
#     ax = axs[5]

#     for name in runs:

#         profile(
#             ax,
#             profiles[name]["MU"][:, 0, 0][::-1],
#             z,
#             name,
#             colors[name],
#             marker="o"
#         )

#     ax.set_title("Updraft Mass Flux")
#     ax.grid(alpha=0.3)

#     for ax in axs:

#         ax.set_ylabel("Height (m)")

#         ax.tick_params(
#             axis='both',
#             labelsize=12
#         )

#     plt.tight_layout()

#     plt.savefig(
#         f"/Users/kfandric/SMT-Nebulae/plotting_tools/scm_{param}_{exp}_profiles_gpu_{levs}.png",
#         dpi=300
#     )

#     plt.show()


# ===============================
# TIMESERIES
# ===============================
if timeseries:
    fig, axs = plt.subplots(4, 1, figsize=(10,8), sharex=True)

    for name, ds in surf_runs.items():
        axs[0].plot(ds["time"], -ds["FLNT"][:,0,0], label=name)
        axs[1].plot(ds["time"], ds["PRECT"][:,0,0]*86400, label=name)
        axs[2].plot(ds["time"], ds["TSAIR"][:,0,0], label=name)
        axs[3].plot(ds["time"], ds["CLDLOW"][:,0,0], label=name)

    axs[0].set_title("OLR"); axs[0].legend(); axs[0].grid()
    axs[1].set_title("Precip"); axs[1].legend(); axs[1].grid()
    axs[2].set_title("TSAIR"); axs[2].legend(); axs[2].grid()
    axs[3].set_title("CLDLOW"); axs[3].legend(); axs[3].grid()

    plt.tight_layout()
    plt.savefig(f"/Users/kfandric/SMT-Nebulae/plotting_tools/scm_{param}_{exp}_timeseries_gpu_"+levs+".png", dpi=300)
    plt.show()

# ===============================
# HOVMOLLER
# ===============================
if hovmoller and exp != "armtwp_ice":

    variables = ["QV", "CLOUD", "MU", "T"]

    z_plot = f90["lev"].values[::-1]

    nvar = len(variables)

    fig, axs = plt.subplots(
        nvar,
        5,
        figsize=(24, 5 * nvar),
        sharex=True,
        sharey=True
    )

    # Label every other timestep
    tick_positions = np.arange(0, len(time_hours_hov)/2, 1)
    tick_labels = np.arange(1, len(time_hours_hov)/2 + 1, 1)

    for i, var in enumerate(variables):

        f90_data = runs["Fortran"][var][:, :, 0, 0].values[:, ::-1]

        cpu_data = runs["CPU"][var][:, :, 0, 0].values[:, ::-1]

        gpu_data = runs["GPU"][var][:, :, 0, 0].values[:, ::-1]

        diff_cpu = cpu_data - f90_data
        diff_gpu = gpu_data - f90_data

        diffmax = max(
            np.nanmax(np.abs(diff_cpu)),
            np.nanmax(np.abs(diff_gpu))
        )

        norm = TwoSlopeNorm(
            vmin=-diffmax,
            vcenter=0,
            vmax=diffmax
        )

        datasets = [
            f90_data,
            cpu_data,
            gpu_data,
            diff_cpu,
            diff_gpu
        ]

        titles = [
            "Fortran",
            "CPU",
            "GPU",
            "CPU-F90",
            "GPU-F90"
        ]

        cmaps = [
            None,
            None,
            None,
            "RdBu_r",
            "RdBu_r"
        ]

        for j in range(5):

            im = axs[i, j].pcolormesh(
                time_hours_hov,
                z_plot,
                datasets[j].T,
                shading="auto",
                cmap=cmaps[j],
                norm=norm if j >= 3 else None
            )

            if i == 0:

                axs[i, j].set_title(
                    titles[j],
                    fontsize=16
                )

            if j == 0:

                axs[i, j].set_ylabel(
                    f"{var}\nHeight (m)",
                    fontsize=14
                )

            axs[i, j].set_xticks(tick_positions)
            axs[i, j].set_xticklabels(np.int32(tick_labels))

            axs[i, j].tick_params(
                axis='x',
                labelsize=11
            )

            axs[i, j].tick_params(
                axis='y',
                labelsize=11
            )

            cbar = plt.colorbar(
                im,
                ax=axs[i, j]
            )

            cbar.ax.tick_params(
                labelsize=10
            )

    for ax in axs[-1, :]:

        ax.set_xlabel(
            "Time (h)",
            fontsize=14
        )

    plt.tight_layout()

    plt.savefig(
        f"/Users/kfandric/SMT-Nebulae/plotting_tools/scm_{param}_{exp}_hovmoller_gpu_{levs}.png",
        dpi=300
    )

    plt.show()

# =========================================================
# HOVMOLLER PLOTS
# =========================================================
if hovmoller and exp == "armtwp_ice":

    variables = ["QV", "CLOUD", "QL", "T"]

    # Reverse pressure levels
    z_plot = f90["lev"].values[::-1]

    # Time coordinate
    time = f90["time"].values

    nvar = len(variables)

    fig, axs = plt.subplots(
        nvar,
        5,
        figsize=(20, 4 * nvar),
        sharex=True,
        sharey=True
    )

    for i, var in enumerate(variables):

        # Reverse vertical dimension
        f90_data = runs["Fortran"][var][:, :, 0, 0].values[:, ::-1]
        cpu_data = runs["CPU"][var][:, :, 0, 0].values[:, ::-1]
        gpu_data = runs["GPU"][var][:, :, 0, 0].values[:, ::-1]

        # Differences
        diff_cpu = cpu_data - f90_data
        diff_gpu = gpu_data - f90_data

        diffmax = max(
            np.nanmax(np.abs(diff_cpu)),
            np.nanmax(np.abs(diff_gpu))
        )

        norm = TwoSlopeNorm(
            vmin=-diffmax,
            vcenter=0,
            vmax=diffmax
        )

        datasets = [
            f90_data,
            cpu_data,
            gpu_data,
            diff_cpu,
            diff_gpu
        ]

        titles = [
            "Fortran",
            "CPU",
            "GPU",
            "CPU-F90",
            "GPU-F90"
        ]

        cmaps = [
            None,
            None,
            None,
            "RdBu_r",
            "RdBu_r"
        ]

        for j in range(5):

            im = axs[i, j].pcolormesh(
                time,
                z_plot,
                datasets[j].T,
                shading="auto",
                cmap=cmaps[j],
                norm=norm if j >= 3 else None
            )

            # Force 1000 hPa at bottom
            axs[i, j].set_ylim(z_plot.max(), z_plot.min())

            if i == 0:
                axs[i, j].set_title(titles[j])

            if j == 0:
                axs[i, j].set_ylabel(f"{var}\nPressure (hPa)")

            plt.colorbar(im, ax=axs[i, j])

    for ax in axs[-1, :]:
        ax.set_xlabel("Time")

    plt.tight_layout()

    plt.savefig(
        f"/Users/kfandric/SMT-Nebulae/plotting_tools/scm_{param}_{exp}_hovmoller_gpu_{levs}.png",
        dpi=300
    )

    plt.show()