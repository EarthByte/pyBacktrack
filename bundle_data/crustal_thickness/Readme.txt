Laske, G., Masters., G., Ma, Z. and Pasyanos, M., Update on CRUST1.0 - A 1-degree Global Model of Earth's Crust, Geophys. Res. Abstracts, 15, Abstract EGU2013-2658, 2013.

Crustal thickness xyz obtained from https://igppweb.ucsd.edu/~gabi/crust1.html#download

Grid file "crsthk.grd" (in metres) was generated from "crsthk.xyz" (in kms) using:

  gmt nearneighbor crsthk.xyz -R-179.5/179.5/-89.5/89.5 -I1 -S0.5d -N1 -Gcrsthk_kms.grd
  gmt grdmath 1000 crsthk_kms.grd MUL = crsthk.grd
