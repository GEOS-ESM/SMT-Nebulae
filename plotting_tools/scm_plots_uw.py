
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

plt_profiles=True
timeseries=True
hovmoller = True

exp = "bomex"
PATH = "/Users/kfandric/data/scm/discover/"
#PATH = "/Users/kfandric/data/scm/uw"

f90 = xr.open_dataset(PATH+"/"+exp+"_uw_multi_fortran_hpc.nc4")
UW =  xr.open_dataset(PATH+"/"+exp+"_uw_multi_dsl_hpc.nc4")


# Get height and time coordinates
z = f90["lev"]   

time = f90["time"] 

def time_mean(ds, var, t_start=None, t_end=None):
    da = ds[var]
    if t_start is not None:
        da = da.sel(time=slice(t_start, t_end))
    return da.mean(dim="time").values

t_start = time[0]  
t_end   = time[-1]

profiles = {"Fortran": {
        "QV": time_mean(f90, "QV", t_start, t_end),
        "MU": time_mean(f90, "MU", t_start, t_end),
        "CLOUD": time_mean(f90, "CLOUD", t_start, t_end),
        "PL": time_mean(f90, "PL", t_start, t_end),
        "QL": time_mean(f90, "QL", t_start, t_end),
        "T": time_mean(f90, "T", t_start, t_end),
},"UW": {
        "QV": time_mean(UW, "QV", t_start, t_end),
        "MU": time_mean(UW, "MU", t_start, t_end),
        "CLOUD": time_mean(UW, "CLOUD", t_start, t_end),
        "PL": time_mean(UW, "PL", t_start, t_end),
        "QL": time_mean(UW, "QL", t_start, t_end),
        "T": time_mean(UW, "T", t_start, t_end),
}}

# Calculate grid-mean LWC
R_d = 287 # J / kg / K
C_p = 1004 
Lv = 2.5E6 # J / kg

PL_f90 = profiles["Fortran"]["PL"][:,0,0]
T_f90 = profiles["Fortran"]["T"][:,0,0]
QL_f90 = profiles["Fortran"]["QL"][:,0,0]
rho_air_f90 = PL_f90 / (R_d * T_f90)
LWC_f90 = QL_f90 * rho_air_f90

PL_UW = profiles["UW"]["PL"][:,0,0]
T_UW = profiles["UW"]["T"][:,0,0]
QL_UW = profiles["UW"]["QL"][:,0,0]
rho_air_UW = PL_UW / (R_d * T_UW)
LWC_UW = QL_UW * rho_air_UW

# Total specific humidity (liquid + vapor)
QT_f90 = QL_f90 + profiles["Fortran"]["QV"][:,0,0]
QT_UW = QL_UW + profiles["UW"]["QV"][:,0,0]

# Liquid water potential temperature
p_adj_f90 = (100000/PL_f90) ** (R_d/C_p)
theta_f90 = T_f90*p_adj_f90
theta_l_f90 = theta_f90 - ((Lv/C_p)*QL_f90)

p_adj_UW = (100000/PL_UW) ** (R_d/C_p)
theta_UW = T_UW*p_adj_UW
theta_l_UW = theta_UW - ((Lv/C_p)*QL_UW)

def profile(ax, x, z, label, color, ls="-", marker=None):
    ax.plot(x, z, label=label, color=color,
            linestyle=ls, marker=marker, markersize=5)

plt.rcParams.update({
    "font.size": 16,      
    "axes.titlesize": 16,   
    "axes.labelsize": 12,   
    "xtick.labelsize": 12,  
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "figure.titlesize": 16,  
    "lines.linewidth": 0.75,
    "lines.markersize": 2,
    "lines.markeredgewidth": 0.8
})

z = z[::-1]

if plt_profiles and exp == "bomex":
    fig, axs = plt.subplots(2, 3, figsize=(12, 12), sharey=True)
    axs = axs.flatten()

    ax = axs[0]
    profile(ax, theta_l_f90[::-1], z, "Fortran", "k", marker="o")
    profile(ax, theta_l_UW[::-1], z, "DSL: UW", "blue", marker="o")
    ax.set_title("a)", loc="left", fontweight="bold")
    ax.set_title(r"$\theta_l$", loc="center")
    ax.set_xlabel("[K]")
    ax.set_ylabel("[hPa]")
    ax.invert_yaxis()
    ax.legend()
    ax.grid(alpha=0.3)

    ax = axs[1]
    profile(ax, QT_f90[::-1], z, "Fortran","k", marker="o")
    profile(ax, QT_UW[::-1], z, "DSL: UW", "blue", marker="o")
    ax.set_title("b)", loc="left", fontweight="bold")
    ax.set_title(r"$q_t$", loc="center")
    ax.set_xlabel("[kg kg$^{-1}$]")
    ax.legend()
    ax.grid(alpha=0.3)


    ax = axs[2]
    profile(ax, profiles["Fortran"]["QL"][:,0,0][::-1], z, "Fortran", "k", marker="o")
    profile(ax, profiles["UW"]["QL"][:,0,0][::-1], z,"DSL:UW", "blue", marker="o")
    ax.set_title("c)", loc="left", fontweight="bold")
    ax.set_title(r"QL", loc="center")
    ax.set_xlabel("[m$^{-2}$s$^{-1}$]")
    ax.legend()
    ax.grid(alpha=0.3)


    ax = axs[3]
    profile(ax, profiles["Fortran"]["CLOUD"][:,0,0], z, "Fortran", "k", marker="o")
    profile(ax, profiles["UW"]["CLOUD"][:,0,0], z, "DSL: UW", "blue", marker="o")
    ax.set_title("d)", loc="left", fontweight="bold")
    ax.set_title(r"Cloud Fraction", loc="center")
    ax.set_xlabel("[fraction]")
    ax.set_ylabel("[hPa]")
    ax.legend()
    ax.grid(alpha=0.3)

    ax = axs[4]
    profile(ax, LWC_f90[::-1], z, "Fortran", "k", marker="o")
    profile(ax, LWC_UW[::-1], z, "DSL: UW", "blue", marker="o")
    ax.set_title("e)", loc="left", fontweight="bold")
    ax.set_title(r"Grid-mean LWC", loc="center")
    ax.set_xlabel("[kg kg$^{-1}$]")
    ax.legend()
    ax.grid(alpha=0.3)

    ax = axs[5]
    profile(ax, profiles["Fortran"]["MU"][:,0,0][::-1], z, "Fortran", "k", marker="o")
    profile(ax, profiles["UW"]["MU"][:,0,0][::-1], z, "DSL: UW", "blue", marker="o")
    ax.set_title("f)", loc="left", fontweight="bold")
    ax.set_title(r"Updraft Mass Flux", loc="center")
    ax.set_xlabel("[kg m$^{-2}$ s$^{-1}$]")
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig("/Users/kfandric/SMT-Nebulae/plotting_tools/scm_"+exp+"_profiles_uw.png", dpi=300)
    plt.show()


if plt_profiles and exp == "arm_97jun":
    fig, axs = plt.subplots(2, 2, figsize=(12, 12), sharey=True)
    axs = axs.flatten()

    ax = axs[0]
    profile(ax, profiles["Fortran"]["QV"][:,0,0][::-1], z, "Fortran", "k", marker="o")
    profile(ax, profiles["UW"]["QV"][:,0,0][::-1], z, "DSL: UW", "blue", marker="o")
    ax.set_title("a)", loc="left", fontweight="bold")
    ax.set_title(r"QV", loc="center")
    ax.set_xlabel("[kg kg$^{-1}$]")
    ax.set_ylabel("[m]")
    ax.legend()
    ax.grid(alpha=0.3)

    ax = axs[1]
    profile(ax, profiles["Fortran"]["T"][:,0,0][::-1], z, "Fortran", "k", marker="o")
    profile(ax, profiles["UW"]["T"][:,0,0][::-1], z, "DSL: UW", "blue", marker="o")
    ax.set_title("a)", loc="left", fontweight="bold")
    ax.set_title(r"T", loc="center")
    ax.set_xlabel("[K]")
    ax.legend()
    ax.grid(alpha=0.3)

    ax = axs[2]
    profile(ax, profiles["Fortran"]["CLOUD"][:,0,0][::-1], z, "Fortran", "k", marker="o")
    profile(ax, profiles["UW"]["CLOUD"][:,0,0][::-1], z, "DSL: UW", "blue", marker="o")
    ax.set_title("c)", loc="left", fontweight="bold")
    ax.set_title(r"Cloud Fraction", loc="center")
    ax.set_xlabel("[fraction]")
    ax.set_ylabel("[m]")
    ax.legend()
    ax.grid(alpha=0.3)


    ax = axs[3]
    profile(ax, profiles["Fortran"]["MU"][:,0,0][::-1], z, "Fortran", "k", marker="o")
    profile(ax, profiles["UW"]["MU"][:,0,0][::-1], z, "DSL: UW", "blue", marker="o")
    ax.set_title("d)", loc="left", fontweight="bold")
    ax.set_title(r"Updraft Mass Flux", loc="center")
    ax.set_xlabel("[kg m$^{-2}$ s$^{-1}$]")
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig("/Users/kfandric/SMT-Nebulae/plotting_tools/scm_"+exp+"_profiles_UW.png", dpi=300)
    plt.show()


# Load surface data
ds1 = xr.open_dataset(PATH+"/"+exp+"_uw_surf_fortran_hpc.nc4")
ds2 = xr.open_dataset(PATH+"/"+exp+"_uw_surf_dsl_hpc.nc4")
#PATH = "/Users/kfandric/data/scm/gfdl1m/"
# ds1 = xr.open_dataset(PATH+"/fortran_surface_linux.nc4")
# ds2 = xr.open_dataset(PATH+"/python_surface_linux_gpu.nc4")
# ds3 =  xr.open_dataset(PATH+"/python_surface_linux_cpu.nc4")



olr1 = -ds1["FLNT"]
olr2 = -ds2["FLNT"]
#olr3 = -ds3["FLNT"]

precip1 = ds1["PRECT"] * 86400
precip2 = ds2["PRECT"] * 86400
#precip3 = ds3["PRECT"] * 86400

tsair1 = ds1["TSAIR"] 
tsair2 = ds2["TSAIR"] 
#tsair3 = ds3["TSAIR"] 

cldlow1 = ds1["CLDLOW"] 
cldlow2 = ds2["CLDLOW"] 
#cldlow3 = ds3["CLDLOW"] 


if timeseries:
    fig, axs = plt.subplots(4, 1, figsize=(10,8), sharex=True)

    # --- OLR ---
    axs[0].plot(ds1["time"], olr1[:,0,0], label="Fortran",linewidth=1.5)
    axs[0].plot(ds2["time"], olr2[:,0,0], label="DSL: UW",linewidth=1.5)
    #axs[0].plot(ds3["time"], olr3[:,0,0], label="CPU DSL: UW",linewidth=1.5)
    axs[0].set_ylabel("[W m$^{-2}$]")
    axs[0].set_title("Outgoing Longwave Radiation")
    axs[0].legend()
    axs[0].grid(True)

    # --- Precip ---
    axs[1].plot(ds1["time"], precip1[:,0,0], label="Fortran",linewidth=1.5)
    axs[1].plot(ds2["time"], precip2[:,0,0], label="DSL: UW",linewidth=1.5)
    #axs[1].plot(ds3["time"], precip3[:,0,0], label="CPU DSL: UW",linewidth=1.5)
    axs[1].set_ylabel("[mm/day]")
    axs[1].set_xlabel("Time")
    axs[1].legend()
    axs[1].set_title("Total Precipitation")
    axs[1].grid(True)

    axs[2].plot(ds1["time"], tsair1[:,0,0], label="Fortran",linewidth=1.5)
    axs[2].plot(ds2["time"], tsair2[:,0,0], label="DSL: UW",linewidth=1.5)
    #axs[2].plot(ds3["time"], tsair3[:,0,0], label="CPU DSL: UW",linewidth=1.5)
    axs[2].set_ylabel("[K]")
    axs[2].set_xlabel("Time")
    axs[2].legend()
    axs[2].set_title("Surface Air Temperature")
    axs[2].grid(True)

    axs[3].plot(ds1["time"], cldlow1[:,0,0], label="Fortran",linewidth=1.5)
    axs[3].plot(ds2["time"], cldlow2[:,0,0], label="DSL: UW",linewidth=1.5)
    #axs[3].plot(ds3["time"], cldlow3[:,0,0], label="CPU DSL: UW",linewidth=1.5)
    axs[3].set_ylabel("[fraction]")
    axs[3].set_xlabel("Time")
    axs[3].legend()
    axs[3].set_title("Low-level Cloud Fraction")
    axs[3].grid(True)

    plt.tight_layout()
    plt.savefig("/Users/kfandric/SMT-Nebulae/plotting_tools/scm_"+exp+"_timeseries_uw.png", dpi=300)
    plt.show()


if hovmoller:

    #variables = ["QV", "QL", "CLOUD", "MU", "T"]
    variables = ["QV", "CLOUD", "MU", "T"]

    time = f90["time"].values
    z = f90["lev"].values

    # Flip vertical axis
    z_plot = z[::-1]

    nvar = len(variables)

    fig, axs = plt.subplots(nvar, 3, figsize=(16, 4*nvar), sharex=True, sharey=True)

    for i, var in enumerate(variables):

        # Extract data
        f90_data = f90[var][:, :, 0, 0].values
        UW_data = UW[var][:, :, 0, 0].values

        # Flip vertical dimension
        f90_data = f90_data[:, ::-1]
        UW_data = UW_data[:, ::-1]

        diff = UW_data - f90_data

        diffmax = np.nanmax(np.abs(diff))

        norm = TwoSlopeNorm(vmin=-diffmax, vcenter=0.0, vmax=diffmax)


        # --- Fortran ---
        im0 = axs[i,0].pcolormesh(
            time,
            z_plot,
            f90_data.T,
            shading="auto",
        )

        if i == 0:
            axs[i,0].set_title("Fortran")

        axs[i,0].set_ylabel(f"{var}\nHeight (m)")
        plt.colorbar(im0, ax=axs[i,0])

        # --- DSL ---
        im1 = axs[i,1].pcolormesh(
            time,
            z_plot,
            UW_data.T,
            shading="auto",
        )

        if i == 0:
            axs[i,1].set_title("DSL: UW")

        plt.colorbar(im1, ax=axs[i,1])

        # --- Difference ---
        im2 = axs[i,2].pcolormesh(
            time,
            z_plot,
            diff.T,
            shading="auto",
            cmap="RdBu_r",
            norm=norm
        )

        if i == 0:
            axs[i,2].set_title("Difference (DSL - Fortran)")

        plt.colorbar(im2, ax=axs[i,2])

    # Label bottom row
    for ax in axs[-1, :]:
        ax.set_xlabel("Time")


    plt.tight_layout()
    plt.savefig("/Users/kfandric/SMT-Nebulae/plotting_tools/scm_"+exp+"_hovmoller_uw.png", dpi=300)
    plt.show()
