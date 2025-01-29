import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib import cm

observed_data = xr.open_dataset("/Users/ckropiew/misc/NDSL_prog_20150421_1800z.nc4")
reference_data = xr.open_dataset("/Users/ckropiew/misc/F_prog_20150421_1800z.nc4")
difference = xr.open_dataset("/Users/ckropiew/misc/diff.nc4")

lat = difference["lat"]
lon = difference["lon"]

temperature_diff = difference["T"]
u_diff = difference["U"]
v_diff = difference["V"]
omega_diff = difference["OMEGA"]

rh_diff = difference["RH"]

qi_diff = difference["QI"]
ql_diff = difference["QL"]
qv_diff = difference["QV"]

levels = difference["lev"].values

# Calc RMSE of differences
rmse_t_per_level = np.sqrt((temperature_diff**2).mean(dim=("lat", "lon", "time")))
rmse_u_per_level = np.sqrt((u_diff**2).mean(dim=("lat", "lon", "time")))
rmse_v_per_level = np.sqrt((v_diff**2).mean(dim=("lat", "lon", "time")))
rmse_omega_per_level = np.sqrt((omega_diff**2).mean(dim=("lat", "lon", "time")))
rmse_rh_per_level = np.sqrt((rh_diff**2).mean(dim=("lat", "lon", "time")))
rmse_qi_per_level = np.sqrt((qi_diff**2).mean(dim=("lat", "lon", "time")))
rmse_ql_per_level = np.sqrt((ql_diff**2).mean(dim=("lat", "lon", "time")))
rmse_qv_per_level = np.sqrt((qv_diff**2).mean(dim=("lat", "lon", "time")))

# Convert to numpy arrays for plotting
rmse_t_per_level_values = rmse_t_per_level.values
rmse_u_per_level_values = rmse_u_per_level.values
rmse_v_per_level_values = rmse_v_per_level.values
rmse_omega_per_level_values = rmse_omega_per_level.values
rmse_rh_per_level_values = rmse_rh_per_level.values
rmse_qi_per_level_values = rmse_qi_per_level.values
rmse_ql_per_level_values = rmse_ql_per_level.values
rmse_qv_per_level_values = rmse_qv_per_level.values

makeplot = False
if makeplot == True:
    # Plot RMSE for Diagnostic Variables
    plt.figure(figsize=(8, 10), dpi=300)

    # Plot for Temperature
    plt.subplot(4, 1, 1)
    plt.plot(rmse_t_per_level_values, levels, marker="o", linestyle="-", color="b")
    plt.gca().invert_yaxis()
    plt.xlabel("RMSE (K)")
    plt.ylabel("Pressure Level (hPa)")
    plt.title("Temperature (T)")
    plt.grid(True)

    # Plot for U
    plt.subplot(4, 1, 2)
    plt.plot(rmse_u_per_level_values, levels, marker="o", linestyle="-", color="r")
    plt.gca().invert_yaxis()
    plt.xlabel("RMSE (m/s)")
    plt.ylabel("Pressure Level (hPa)")
    plt.title("Zonal Wind (U)")
    plt.grid(True)

    # Plot for V
    plt.subplot(4, 1, 3)
    plt.plot(rmse_v_per_level_values, levels, marker="o", linestyle="-", color="g")
    plt.gca().invert_yaxis()
    plt.xlabel("RMSE (m/s)")
    plt.ylabel("Pressure Level (hPa)")
    plt.title("Meridional Wind (V)")
    plt.grid(True)

    # Plot for OMEGA
    plt.subplot(4, 1, 4)
    plt.plot(
        rmse_omega_per_level_values, levels, marker="o", linestyle="-", color="purple"
    )
    plt.gca().invert_yaxis()
    plt.xlabel("RMSE (m/s)")
    plt.ylabel("Pressure Level (hPa)")
    plt.title("Vertical Motion (Omega)")
    plt.grid(True)

    plt.tight_layout()
    plt.savefig("RMSE_diffs_TUVW.png")
    # plt.show()

makeplot = False
if makeplot == True:
    # Plot RMSE for Mixing Ratios
    plt.figure(figsize=(8, 10), dpi=300)

    # Plot for RH
    plt.subplot(4, 1, 1)
    plt.plot(rmse_rh_per_level_values, levels, marker="o", linestyle="-", color="b")
    plt.gca().invert_yaxis()
    plt.xlabel("RMSE (%)")
    plt.ylabel("Pressure Level (hPa)")
    plt.title("Relative Humidity (RH)")
    plt.grid(True)

    # Plot for QI
    plt.subplot(4, 1, 2)
    plt.plot(rmse_qi_per_level_values, levels, marker="o", linestyle="-", color="r")
    plt.gca().invert_yaxis()
    plt.xlabel("RMSE (kg/kg)")
    plt.ylabel("Pressure Level (hPa)")
    plt.title("Ice Mixing Ratio (kg/kg)")
    plt.grid(True)

    # Plot for QL
    plt.subplot(4, 1, 3)
    plt.plot(rmse_ql_per_level_values, levels, marker="o", linestyle="-", color="g")
    plt.gca().invert_yaxis()
    plt.xlabel("RMSE (kg/kg)")
    plt.ylabel("Pressure Level (hPa)")
    plt.title("Liquid Mixing Ratio (kg/kg)")
    plt.grid(True)

    # Plot for QV
    plt.subplot(4, 1, 4)
    plt.plot(
        rmse_qv_per_level_values, levels, marker="o", linestyle="-", color="purple"
    )
    plt.gca().invert_yaxis()
    plt.xlabel("RMSE (kg/kg))")
    plt.ylabel("Pressure Level (hPa)")
    plt.title("Vapor Mixing Ratio (kg/kg)")
    plt.grid(True)

    plt.tight_layout()
    plt.savefig("RMSE_diffs_h2o.png")
    # plt.show()


###### Creating Florian's story

## WORST PERFORMANCE AREA

lons, lats = np.meshgrid(lon, lat)
cmap_levels = [-20, -15, -10, -5, -2, -1, 0, 1, 2, 5, 10, 15, 20]

# Plot the region of interest

# observed
plt.figure(figsize=(10, 7), dpi=300)
ax = plt.axes(projection=ccrs.PlateCarree())
# ax.stock_img()

ax.coastlines()
ax.add_feature(cfeature.BORDERS, linestyle="-", alpha=1)

ax.set_extent([-50, -15, -35, -20])

contour = ax.contourf(
    lons,
    lats,
    observed_data["U"][0, 0, :, :],
    levels=cmap_levels,
    cmap="seismic",
    extend="both",
)
cbar = plt.colorbar(
    contour,
    ax=ax,
    orientation="horizontal",
    shrink=0.7,
    pad=0.01,
    label="Wind Difference (m/s)",
)

plt.title("NDSL U Field", size=25)
plt.tight_layout()
plt.savefig("U_NDSL_brazil.png")

# reference
plt.figure(figsize=(10, 7), dpi=300)
ax = plt.axes(projection=ccrs.PlateCarree())
# ax.stock_img()

ax.coastlines()
ax.add_feature(cfeature.BORDERS, linestyle="-", alpha=1)

ax.set_extent([-50, -15, -35, -20])

contour = ax.contourf(
    lons,
    lats,
    reference_data["U"][0, 0, :, :],
    levels=cmap_levels,
    cmap="seismic",
    extend="both",
)
cbar = plt.colorbar(
    contour,
    ax=ax,
    orientation="horizontal",
    shrink=0.7,
    pad=0.01,
    label="Wind Difference (m/s)",
)

plt.title("Fortran U Field", size=25)
plt.tight_layout()
plt.savefig("U_Fortran_brazil.png")

# difference
plt.figure(figsize=(10, 7), dpi=300)
ax = plt.axes(projection=ccrs.PlateCarree())
# ax.stock_img()

ax.coastlines()
ax.add_feature(cfeature.BORDERS, linestyle="-", alpha=1)

ax.set_extent([-50, -15, -35, -20])

contour = ax.contourf(
    lons,
    lats,
    difference["U"][0, 0, :, :],
    levels=cmap_levels,
    cmap="seismic",
    extend="both",
)
cbar = plt.colorbar(
    contour,
    ax=ax,
    orientation="horizontal",
    shrink=0.7,
    pad=0.01,
    label="Wind Difference (m/s)",
)

plt.title("Difference (Fortran - NDSL) U Field", size=25)
plt.tight_layout()
plt.savefig("U_difference_brazil.png")


## BETTER PERFORMANCE AREA chosen semi-randomly (numbers chosen without looking at data)

# observed
plt.figure(figsize=(10, 7), dpi=300)
ax = plt.axes(projection=ccrs.PlateCarree())
# ax.stock_img()

ax.coastlines()
ax.add_feature(cfeature.BORDERS, linestyle="-", alpha=1)

ax.set_extent([-180, -145, 45, 30])

contour = ax.contourf(
    lons,
    lats,
    observed_data["U"][0, 0, :, :],
    levels=cmap_levels,
    cmap="seismic",
    extend="both",
)
cbar = plt.colorbar(
    contour,
    ax=ax,
    orientation="horizontal",
    shrink=0.7,
    pad=0.01,
    label="Wind Difference (m/s)",
)

plt.title("NDSL U Field", size=25)
plt.tight_layout()
plt.savefig("U_NDSL_northpacific.png")

# reference
plt.figure(figsize=(10, 7), dpi=300)
ax = plt.axes(projection=ccrs.PlateCarree())
# ax.stock_img()

ax.coastlines()
ax.add_feature(cfeature.BORDERS, linestyle="-", alpha=1)

ax.set_extent([-180, -145, 45, 30])

contour = ax.contourf(
    lons,
    lats,
    reference_data["U"][0, 0, :, :],
    levels=cmap_levels,
    cmap="seismic",
    extend="both",
)
cbar = plt.colorbar(
    contour,
    ax=ax,
    orientation="horizontal",
    shrink=0.7,
    pad=0.01,
    label="Wind Difference (m/s)",
)

plt.title("Fortran U Field", size=25)
plt.tight_layout()
plt.savefig("U_Fortran_northpacific.png")

# difference
plt.figure(figsize=(10, 7), dpi=300)
ax = plt.axes(projection=ccrs.PlateCarree())
# ax.stock_img()

ax.coastlines()
ax.add_feature(cfeature.BORDERS, linestyle="-", alpha=1)

ax.set_extent([-180, -145, 45, 30])

contour = ax.contourf(
    lons,
    lats,
    difference["U"][0, 0, :, :],
    levels=cmap_levels,
    cmap="seismic",
    extend="both",
)
cbar = plt.colorbar(
    contour,
    ax=ax,
    orientation="horizontal",
    shrink=0.7,
    pad=0.01,
    label="Wind Difference (m/s)",
)

plt.title("Difference (Fortran - NDSL) U Field", size=25)
plt.tight_layout()
plt.savefig("U_diff_northpacific.png")


# difference whole map
plt.figure(figsize=(10, 7), dpi=300)
ax = plt.axes(projection=ccrs.PlateCarree())
# ax.stock_img()

ax.coastlines()
ax.add_feature(cfeature.BORDERS, linestyle="-", alpha=1)

# ax.set_extent([-180, -145, 45, 30])

contour = ax.contourf(
    lons,
    lats,
    difference["U"][0, 0, :, :],
    levels=cmap_levels,
    cmap="seismic",
    extend="both",
)
cbar = plt.colorbar(
    contour,
    ax=ax,
    orientation="horizontal",
    shrink=0.7,
    pad=0.01,
    label="Wind Difference (m/s)",
)

plt.title("Difference (Fortran - NDSL) U Field", size=25)
plt.tight_layout()
plt.savefig("U_diff_world.png")
