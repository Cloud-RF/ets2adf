## ETS to ADF conversion utility
This antenna utility converts ETS CSV files into TIA/EIA-804-B standard ADF files.

[ADF antenna standard](https://cloudrf.com/files/ADF_antenna_standard_wg16_99_050.pdf)

To use, take a ETS CSV file and call the script with one argument of the filename:

    python3 ets2adf.py {raw.csv}

The script outputs ADF files to the adf directory. Upload these at CloudRF to use them in the service.
![ADF polar plot from CloudRF.com](https://cloudrf.com/files/antenna_plot.jpg)

### Assumptions
- 15 degree separation between values
- Vertical polarisation
- Vertical plane needs rotating 90 degrees so it's 'north up'
- Vertical plane is symmetrical as it expects only half
