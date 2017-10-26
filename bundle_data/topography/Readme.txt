Amante, C. and B. W. Eakins, ETOPO1 1 Arc-Minute Global Relief Model: Procedures, Data Sources and Analysis. NOAA Technical Memorandum NESDIS NGDC-24, 19 pp, March 2009

https://www.ngdc.noaa.gov/mgg/global/global.html

Running GMT grdinfo on "ETOPO1_0.1.grd" reveals:

  Command: grdsample -V -I0.1 ETOPO1_Bed_g.g98 -GETOPO1_0.1.grd

...and finally it was converted from NetCDF 3 to NetCDF 4 using "grdconvert".