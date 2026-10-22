# Bio-ORACLE teaching grid

`bio_oracle_bc_surface_temperature.csv` is a checked-in extract of Bio-ORACLE
v3 surface ocean temperature (mean, degrees Celsius) for 48.025–60.025°N and
139.975–122.025°W. It contains 42,679 ocean cells at 0.05° resolution. The
rectangle includes adjacent waters; it is not a British Columbia boundary.

Sources:

- Baseline 2010–2020: `thetao_baseline_2000_2019_depthsurf`, time 2010-01-01.
- SSP2-4.5 2050–2060: `thetao_ssp245_2020_2100_depthsurf`, time 2050-01-01.
- Variable: `thetao_mean`; source: <https://www.bio-oracle.org/> via
  <https://erddap.bio-oracle.org/erddap/>.

To regenerate, request the two cropped CSV0 subsets from ERDDAP and run
`python3 frontend/scripts/prepare_bio_oracle.py baseline.csv future.csv
frontend/data/bio_oracle_bc_surface_temperature.csv` from the repository root.
The script retains only cells with finite values in both periods and rounds
temperatures to 0.001°C.

Please cite Assis et al. (2024), *Bio-ORACLE v3.0*, Global Ecology and
Biogeography, DOI: 10.1111/geb.13813, in any use of this data.
