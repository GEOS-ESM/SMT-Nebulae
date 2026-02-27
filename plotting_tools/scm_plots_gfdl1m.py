
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

profiles=True
timeseries=True

PATH = "/Users/kfandric/data/scm/gfdl1m/"

f90 = xr.open_dataset(PATH+"armtwpice_fortran.nc4")
gfdl1m = xr.open_dataset(PATH+"armtwpice_dace.nc4")

# Get height and time coordinates
z = f90["lev"].values        
time = f90["time"] 

def time_mean(ds, var, t_start=None, t_end=None):
    da = ds[var]
    if t_start is not None:
        da = da.sel(time=slice(t_start, t_end))
    return da.mean(dim="time").values

t_start = time[-288]  
t_end   = time[-1]

profiles = {"Fortran": {
        "QV": time_mean(f90, "QV", t_start, t_end),
        "QV": time_mean(f90, "QV", t_start, t_end),
        "MU": time_mean(f90, "MU", t_start, t_end),
        "CLOUD": time_mean(f90, "CLOUD", t_start, t_end),
        "PL": time_mean(f90, "PL", t_start, t_end),
        "QL": time_mean(f90, "QL", t_start, t_end),
        "T": time_mean(f90, "T", t_start, t_end),
},"gfdl1m": {
        "QV": time_mean(gfdl1m, "QV", t_start, t_end),
        "QV": time_mean(gfdl1m, "QV", t_start, t_end),
        "MU": time_mean(gfdl1m, "MU", t_start, t_end),
        "CLOUD": time_mean(gfdl1m, "CLOUD", t_start, t_end),
        "PL": time_mean(gfdl1m, "PL", t_start, t_end),
        "QL": time_mean(gfdl1m, "QL", t_start, t_end),
        "T": time_mean(gfdl1m, "T", t_start, t_end),
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

PL_gfdl1m = profiles["gfdl1m"]["PL"][:,0,0]
T_gfdl1m = profiles["gfdl1m"]["T"][:,0,0]
QL_gfdl1m = profiles["gfdl1m"]["QL"][:,0,0]
rho_air_gfdl1m = PL_gfdl1m / (R_d * T_gfdl1m)
LWC_gfdl1m = QL_gfdl1m * rho_air_gfdl1m

# Total specific humidity (liquid + vapor)
QT_f90 = QL_f90 + profiles["Fortran"]["QV"][:,0,0]
QT_gfdl1m = QL_gfdl1m + profiles["gfdl1m"]["QV"][:,0,0]

# Liquid water potential temperature
p_adj_f90 = (100000/PL_f90) ** (R_d/C_p)
theta_f90 = T_f90*p_adj_f90
theta_l_f90 = theta_f90 - ((Lv/C_p)*QL_f90)

p_adj_gfdl1m = (100000/PL_gfdl1m) ** (R_d/C_p)
theta_gfdl1m = T_gfdl1m*p_adj_gfdl1m
theta_l_gfdl1m = theta_gfdl1m - ((Lv/C_p)*QL_gfdl1m)

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

if profiles:
    fig, axs = plt.subplots(2, 3, figsize=(12, 12), sharey=True)
    axs = axs.flatten()

    ax = axs[0]
    profile(ax, theta_l_f90, z, "Fortran", "k", marker="o")
    profile(ax, theta_l_gfdl1m, z, "DSL: GFDL1M", "blue", marker="o")
    ax.set_title("a)", loc="left", fontweight="bold")
    ax.set_title(r"$\theta_l$", loc="center")
    ax.set_xlabel("[K]")
    ax.set_ylabel("[m]")
    ax.legend()
    ax.grid(alpha=0.3)

    ax = axs[1]
    profile(ax, QT_f90, z, "Fortran","k", marker="o")
    profile(ax, QT_gfdl1m, z, "DSL: GFDL1M", "blue", marker="o")
    ax.set_title("b)", loc="left", fontweight="bold")
    ax.set_title(r"$q_t$", loc="center")
    ax.set_xlabel("[kg kg$^{-1}$]")
    ax.legend()
    ax.grid(alpha=0.3)


    ax = axs[2]
    profile(ax, profiles["Fortran"]["QV"][:,0,0], z, "Fortran", "k", marker="o")
    profile(ax, profiles["gfdl1m"]["QV"][:,0,0], z,"DSL:GFDL1M", "blue", marker="o")
    ax.set_title("c)", loc="left", fontweight="bold")
    ax.set_title(r"QV", loc="center")
    ax.set_xlabel("[kg/kg]")
    ax.legend()
    ax.grid(alpha=0.3)


    ax = axs[3]
    profile(ax, profiles["Fortran"]["CLOUD"][:,0,0], z, "Fortran", "k", marker="o")
    profile(ax, profiles["gfdl1m"]["CLOUD"][:,0,0], z, "DSL: GFDL1M", "blue", marker="o")
    ax.set_title("d)", loc="left", fontweight="bold")
    ax.set_title(r"Cloud Fraction", loc="center")
    ax.set_xlabel("[fraction]")
    ax.set_ylabel("[m]")
    ax.legend()
    ax.grid(alpha=0.3)

    ax = axs[4]
    profile(ax, LWC_f90, z, "Fortran", "k", marker="o")
    profile(ax, LWC_gfdl1m, z, "DSL: GFDL1M", "blue", marker="o")
    ax.set_title("e)", loc="left", fontweight="bold")
    ax.set_title(r"Grid-mean LWC", loc="center")
    ax.set_xlabel("[kg kg$^{-1}$]")
    ax.legend()
    ax.grid(alpha=0.3)

    ax = axs[5]
    profile(ax, profiles["Fortran"]["MU"][:,0,0], z, "Fortran", "k", marker="o")
    profile(ax, profiles["gfdl1m"]["MU"][:,0,0], z, "DSL: GFDL1M", "blue", marker="o")
    ax.set_title("f)", loc="left", fontweight="bold")
    ax.set_title(r"Updraft Mass Flux", loc="center")
    ax.set_xlabel("[kg m$^{-2}$ s$^{-1}$]")
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig("scm_armtwpice_profiles_gfdl1m.png", dpi=300)
    plt.show()


# Load surface data
ds1 = xr.open_dataset(PATH+"armtwpice_fortran_surface.nc4")
ds2 = xr.open_dataset(PATH+"armtwpice_dace_surface.nc4")


olr1 = -ds1["FLNT"]
olr2 = -ds2["FLNT"]

precip1 = ds1["PRECT"] * 86400
precip2 = ds2["PRECT"] * 86400

tsair1 = ds1["TSAIR"] 
tsair2 = ds2["TSAIR"] 

cldlow1 = ds1["CLDLOW"] 
cldlow2 = ds2["CLDLOW"] 


if timeseries:
    fig, axs = plt.subplots(4, 1, figsize=(12,8), sharex=True)

    # --- OLR ---
    axs[0].plot(ds1["time"], olr1[:,0,0], label="Fortran",linewidth=1.5)
    axs[0].plot(ds2["time"], olr2[:,0,0], label="DSL: GFDL1M",linewidth=1.5)
    axs[0].set_ylabel("OLR (W m$^{-2}$)")
    axs[0].set_title("Outgoing Longwave Radiation")
    axs[0].legend()
    axs[0].grid(True)

    # --- Precip ---
    axs[1].plot(ds1["time"], precip1[:,0,0], label="Fortan",linewidth=1.5)
    axs[1].plot(ds2["time"], precip2[:,0,0], label="DSL: GFDL1M",linewidth=1.5)
    axs[1].set_ylabel("Precipitation (mm/day)")
    axs[1].set_xlabel("Time")
    axs[1].legend()
    axs[1].set_title("Total Precipitation")
    axs[1].grid(True)

    axs[2].plot(ds1["time"], tsair1[:,0,0], label="Fortan",linewidth=1.5)
    axs[2].plot(ds2["time"], tsair2[:,0,0], label="DSL: GFDL1M",linewidth=1.5)
    axs[2].set_ylabel("Surface Air Temperature (K)")
    axs[2].set_xlabel("Time")
    axs[2].legend()
    axs[2].set_title("Surface Air Temperature")
    axs[2].grid(True)

    axs[3].plot(ds1["time"], cldlow1[:,0,0], label="Fortan",linewidth=1.5)
    axs[3].plot(ds2["time"], cldlow2[:,0,0], label="DSL: GFDL1M",linewidth=1.5)
    axs[3].set_ylabel("CLDLOW")
    axs[3].set_xlabel("Time")
    axs[3].legend()
    axs[3].set_title("CLDLOW")
    axs[3].grid(True)

    plt.tight_layout()
    plt.savefig("scm_armtwpice_timeseries_gfdl1m.png", dpi=300)
    plt.show()