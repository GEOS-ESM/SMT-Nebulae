import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib import cm
import re


plot_rmse_diagnostics = False
plot_box_diagnostics = False
plot_hist_diagnostics = True
plot_rmse_mixing_ratios = False
plot_details = True
directory = "/Users/kfandric/data"
# backend = "dacegpu"
# backend_label = "NDSL GPU (dace:gpu)"
backend = "fortran_perturbed"
backend_label = "NDSL CPU (dace:cpu)"
benchmark_call = False


if __name__ == "__main__":
    python_data = xr.open_dataset(
        f"{directory}/{backend}/TBC_C24_L72.geosgcm_prog.20000503_0600z.nc4"
    )
    fortran_data = xr.open_dataset(
        f"{directory}/fortran/TBC_C24_L72.geosgcm_prog.20000503_0600z.nc4"
    )
    difference = python_data - fortran_data

    lat = difference["lat"]
    lon = difference["lon"]

    temperature_diff = difference["T"][:, :, 0:-1]
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

    # Plot RMSE for Diagnostic Variables
    if plot_rmse_diagnostics:
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
            rmse_omega_per_level_values,
            levels,
            marker="o",
            linestyle="-",
            color="purple",
        )
        plt.gca().invert_yaxis()
        plt.xlabel("RMSE (m/s)")
        plt.ylabel("Pressure Level (hPa)")
        plt.title("Vertical Motion (Omega)")
        plt.grid(True)

        plt.tight_layout()
        plt.savefig("RMSE_diffs_TUVW.png")
        # plt.show()

    # Plot RMSE for Mixing Ratios
    if plot_rmse_mixing_ratios:
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

    temperature_diff_flatten = temperature_diff.sel(lev=1000).values.flatten()
    rh_diff_flatten = rh_diff.sel(lev=1000).values.flatten()
    u_diff_flatten = u_diff.sel(lev=1000).values.flatten()
    v_diff_flatten = v_diff.sel(lev=1000).values.flatten()

    # Box plot of the differences in diagnostics variables:
    if plot_box_diagnostics:
        # Make boxplots of diffs at 1000hpa level
        plt.figure(figsize=(8, 10), dpi=300)

        # Temperature Difference Box Plot at 1000 hPa
        plt.subplot(4, 1, 1)
        plt.boxplot(
            temperature_diff_flatten[~np.isnan(temperature_diff_flatten)],
            vert=False,
            patch_artist=True,
            boxprops=dict(facecolor="b", color="b"),
        )
        plt.xlabel("T Difference (K)")
        plt.title("Temperature (1000 hPa)")

        # Relative Humidity Difference Box Plot at 1000 hPa
        plt.subplot(4, 1, 2)
        plt.boxplot(
            rh_diff_flatten[~np.isnan(rh_diff_flatten)],
            vert=False,
            patch_artist=True,
            boxprops=dict(facecolor="g", color="g"),
        )
        plt.xlabel("RH Difference (%)")
        plt.title("Relative Humidity (1000 hPa)")

        # Zonal Wind (U) Difference Box Plot at 1000 hPa
        plt.subplot(4, 1, 3)
        plt.boxplot(
            u_diff_flatten[~np.isnan(u_diff_flatten)],
            vert=False,
            patch_artist=True,
            boxprops=dict(facecolor="r", color="r"),
        )
        plt.xlabel("U Difference (m/s)")
        plt.title("Zonal Wind (U) (1000 hPa)")

        # Meridional Wind (V) Difference Box Plot at 1000 hPa
        plt.subplot(4, 1, 4)
        plt.boxplot(
            v_diff_flatten[~np.isnan(v_diff_flatten)],
            vert=False,
            patch_artist=True,
            boxprops=dict(facecolor="purple", color="purple"),
        )
        plt.xlabel("V Difference (m/s)")
        plt.title("Meridional Wind (V) (1000 hPa)")

        # Adjust layout for better readability
        plt.tight_layout()
        plt.savefig("boxplots_sfc.png")

    # Histogram of the differences in diagnostics variables:
    if plot_hist_diagnostics:
        # Create a figure with subplots to display the histograms with a smaller x-axis range
        fig = plt.figure(figsize=(10, 12))
        fig.suptitle(
            f"Distribution of differences between Fortran and Fortran Perturbed",
            size=18,
        )

        # Temperature Difference Histogram with smaller x-axis range
        plt.subplot(4, 1, 1)
        plt.hist(temperature_diff_flatten, bins=1000, color="b", alpha=0.7)
        plt.xlim(
            [
                np.nanmean(temperature_diff_flatten)
                - (10 * np.nanstd(temperature_diff_flatten)),
                np.nanmean(temperature_diff_flatten)
                + (10 * np.nanstd(temperature_diff_flatten)),
            ]
        )  # Narrowing the x-axis range
        plt.xlabel("Temperature Difference (K)")
        plt.ylabel("Frequency")
        plt.title("Temperature")

        # Relative Humidity Difference Histogram with smaller x-axis range
        plt.subplot(4, 1, 2)
        plt.hist(rh_diff_flatten, bins=1000, color="g", alpha=0.7)
        plt.xlim(
            [
                np.nanmean(rh_diff_flatten) - (10 * np.nanstd(rh_diff_flatten)),
                np.nanmean(rh_diff_flatten) + (10 * np.nanstd(rh_diff_flatten)),
            ]
        )  # Narrowing the x-axis range
        plt.xlabel("Relative Humidity Difference (%)")
        plt.ylabel("Frequency")
        plt.title("Relative Humidity")

        # Zonal Wind (U) Difference Histogram with smaller x-axis range
        plt.subplot(4, 1, 3)
        plt.hist(u_diff_flatten, bins=1000, color="r", alpha=0.7)
        plt.xlim(
            [
                np.nanmean(u_diff_flatten) - (10 * np.nanstd(u_diff_flatten)),
                np.nanmean(u_diff_flatten) + (10 * np.nanstd(u_diff_flatten)),
            ]
        )  # Narrowing the x-axis range
        plt.xlabel("Zonal Wind U (m/s)")
        plt.ylabel("Frequency")
        plt.title("Zonal Wind (U)")

        # Meridional Wind (V) Difference Histogram with smaller x-axis range
        plt.subplot(4, 1, 4)
        plt.hist(v_diff_flatten, bins=1000, color="purple", alpha=0.7)
        plt.xlim(
            [
                np.nanmean(v_diff_flatten) - (10 * np.nanstd(v_diff_flatten)),
                np.nanmean(v_diff_flatten) + (10 * np.nanstd(v_diff_flatten)),
            ]
        )  # Narrowing the x-axis range
        plt.xlabel("Meridional Wind V (m/s)")
        plt.ylabel("Frequency")
        plt.title("Meridional Wind (V)")

        # Adjust layout for readability
        plt.tight_layout()
        plt.savefig(f"hist__{backend}_v_Fortran__sfc.png")

    # Plot details
    if plot_details:
        # WORST PERFORMANCE AREA

        lons, lats = np.meshgrid(lon, lat)
        # cmap_levels = [-20, -15, -10, -5, -2, -1, 0, 1, 2, 5, 10, 15, 20]
        cmap_levels = [260, 265, 270, 275, 280, 285, 290, 295, 300, 305, 310, 315, 320]

        # # Plot the region of interest

        # # observed
        # plt.figure(figsize=(10, 7), dpi=300)
        # ax = plt.axes(projection=ccrs.PlateCarree())
        # # ax.stock_img()

        # ax.coastlines()
        # ax.add_feature(cfeature.BORDERS, linestyle="-", alpha=1)

        # ax.set_extent([-50, -15, -35, -20])

        # contour = ax.contourf(
        #     lons,
        #     lats,
        #     python_data["U"][0, 0, :, :],
        #     levels=cmap_levels,
        #     cmap="seismic",
        #     extend="both",
        # )
        # cbar = plt.colorbar(
        #     contour,
        #     ax=ax,
        #     orientation="horizontal",
        #     shrink=0.7,
        #     pad=0.01,
        #     label="Wind Difference (m/s)",
        # )

        # plt.title("NDSL U Field", size=25)
        # plt.tight_layout()
        # plt.savefig("U_NDSL_brazil.png")

        # # reference
        # plt.figure(figsize=(10, 7), dpi=300)
        # ax = plt.axes(projection=ccrs.PlateCarree())
        # # ax.stock_img()

        # ax.coastlines()
        # ax.add_feature(cfeature.BORDERS, linestyle="-", alpha=1)

        # ax.set_extent([-50, -15, -35, -20])

        # contour = ax.contourf(
        #     lons,
        #     lats,
        #     fortran_data["U"][0, 0, :, :],
        #     levels=cmap_levels,
        #     cmap="seismic",
        #     extend="both",
        # )
        # cbar = plt.colorbar(
        #     contour,
        #     ax=ax,
        #     orientation="horizontal",
        #     shrink=0.7,
        #     pad=0.01,
        #     label="Wind Difference (m/s)",
        # )

        # plt.title("Fortran U Field", size=25)
        # plt.tight_layout()
        # plt.savefig("U_Fortran_brazil.png")

        # # difference
        # plt.figure(figsize=(10, 7), dpi=300)
        # ax = plt.axes(projection=ccrs.PlateCarree())
        # # ax.stock_img()

        # ax.coastlines()
        # ax.add_feature(cfeature.BORDERS, linestyle="-", alpha=1)

        # ax.set_extent([-50, -15, -35, -20])

        # contour = ax.contourf(
        #     lons,
        #     lats,
        #     difference["U"][0, 0, :, :],
        #     levels=cmap_levels,
        #     cmap="seismic",
        #     extend="both",
        # )
        # cbar = plt.colorbar(
        #     contour,
        #     ax=ax,
        #     orientation="horizontal",
        #     shrink=0.7,
        #     pad=0.01,
        #     label="Wind Difference (m/s)",
        # )

        # plt.title("Difference (Fortran - NDSL) U Field", size=25)
        # plt.tight_layout()
        # plt.savefig("U_difference_brazil.png")

        # ## BETTER PERFORMANCE AREA chosen semi-randomly (numbers chosen without looking at data)

        # # observed
        # plt.figure(figsize=(10, 7), dpi=300)
        # ax = plt.axes(projection=ccrs.PlateCarree())
        # # ax.stock_img()

        # ax.coastlines()
        # ax.add_feature(cfeature.BORDERS, linestyle="-", alpha=1)

        # ax.set_extent([-180, -145, 45, 30])

        # contour = ax.contourf(
        #     lons,
        #     lats,
        #     python_data["U"][0, 0, :, :],
        #     levels=cmap_levels,
        #     cmap="seismic",
        #     extend="both",
        # )
        # cbar = plt.colorbar(
        #     contour,
        #     ax=ax,
        #     orientation="horizontal",
        #     shrink=0.7,
        #     pad=0.01,
        #     label="Wind Difference (m/s)",
        # )

        # plt.title("NDSL U Field", size=25)
        # plt.tight_layout()
        # plt.savefig("U_NDSL_northpacific.png")

        # # reference
        # plt.figure(figsize=(10, 7), dpi=300)
        # ax = plt.axes(projection=ccrs.PlateCarree())
        # # ax.stock_img()

        # ax.coastlines()
        # ax.add_feature(cfeature.BORDERS, linestyle="-", alpha=1)

        # ax.set_extent([-180, -145, 45, 30])

        # contour = ax.contourf(
        #     lons,
        #     lats,
        #     fortran_data["U"][0, 0, :, :],
        #     levels=cmap_levels,
        #     cmap="seismic",
        #     extend="both",
        # )
        # cbar = plt.colorbar(
        #     contour,
        #     ax=ax,
        #     orientation="horizontal",
        #     shrink=0.7,
        #     pad=0.01,
        #     label="Wind Difference (m/s)",
        # )

        # plt.title("Fortran U Field", size=25)
        # plt.tight_layout()
        # plt.savefig("U_Fortran_northpacific.png")

        # # difference
        # plt.figure(figsize=(10, 7), dpi=300)
        # ax = plt.axes(projection=ccrs.PlateCarree())
        # # ax.stock_img()

        # ax.coastlines()
        # ax.add_feature(cfeature.BORDERS, linestyle="-", alpha=1)

        # ax.set_extent([-180, -145, 45, 30])

        # contour = ax.contourf(
        #     lons,
        #     lats,
        #     difference["U"][0, 0, :, :],
        #     levels=cmap_levels,
        #     cmap="seismic",
        #     extend="both",
        # )
        # cbar = plt.colorbar(
        #     contour,
        #     ax=ax,
        #     orientation="horizontal",
        #     shrink=0.7,
        #     pad=0.01,
        #     label="Wind Difference (m/s)",
        # )

        # plt.title("Difference (Fortran - NDSL) U Field", size=25)
        # plt.tight_layout()
        # plt.savefig("U_diff_northpacific.png")

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
            difference["T"][0, 0, :, :],
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
            label="Temperature (K)",
        )

        plt.title(
            f"Temperature Field Differences (Fortran - Fortran Perturbed)", size=18
        )
        plt.tight_layout()
        plt.savefig("T_diff_world.png")

        contour = ax.contourf(
            lons,
            lats,
            fortran_data["T"][0, 0, :, :],
            levels=cmap_levels,
            cmap="seismic",
            extend="both",
        )

        plt.title("Temperature Field from reference Fortran", size=18)
        plt.tight_layout()
        plt.savefig("T_fortran_world.png")

        contour = ax.contourf(
            lons,
            lats,
            python_data["T"][0, 0, :, :],
            levels=cmap_levels,
            cmap="seismic",
            extend="both",
        )
        plt.title(f"Temperature Field from Fortran perturbed", size=18)
        plt.tight_layout()
        plt.savefig("T_fortran_perturbed_world.png")

    # # Plot benchmark numbers
    # if benchmark_call:
    #     numeric_const_pattern = (
    #         "[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?"  # noqa
    #     )
    #     rx = re.compile(numeric_const_pattern, re.VERBOSE)

    #     observed_timings = []
    #     observed_median_timings = 0
    #     with open(f"{directory}/{backend}/BENCH.{backend}.timings.out") as f:
    #         for line in f.readlines():
    #             observed_timings.append((float(rx.findall(line)[2])))

    #     reference_timings = []
    #     reference_median = 0
    #     with open(f"{directory}/fortran/BENCH.fortran.timings.out") as f:
    #         for line in f.readlines():
    #             reference_timings.append((float(rx.findall(line)[2])))

    #     reference_median = np.percentile(
    #         reference_timings, 95, method="median_unbiased"
    #     )
    #     python_data = np.percentile(observed_timings, 95, method="median_unbiased")

    #     print(f"Fortran {reference_median}")
    #     print(f"{backend_label} {python_data}")

    #     if reference_median < python_data:
    #         speed_up = -1.0 * (python_data / reference_median)
    #     else:
    #         speed_up = reference_median / python_data
    #     print("Speed up:", speed_up)
