# DICOM Anonymizer
This script allows automated anonymizing of echocardiogram DICOM files. Scrubs all private health information stored in metadata as well as blacks out the top and sides to remove private information listed in the banner. This repo contains no real private health information, and test files are simply for demo.

*WARNING: DO NOT RUN SCRIPT ON NON-SECURE SERVER OR NON-ENCRYPTED LOCAL DESKTOP*

Use script with caution and ALWAYS MANUALLY ENSURE THAT ALL PHI HAS BEEN ZERO'ED OUT.

## Getting Started
### Downloading Python
Download the Anaconda package manager for Python. Skip if you already have Anaconda installed.

Make a temporary folder:
```bash
$ mkdir tmp
```

Enter the folder:
```bash
$ cd tmp
```

Download Anaconda:
```bash
$ curl -O https://repo.anaconda.com/archive/Anaconda3-2019.03-Linux-x86_64.sh
```

Check data integrity with a cryptographic hash:
```bash
$ sha256sum Anaconda3-2019.03-Linux-x86_64.sh
```

Output should look like this:
```bash
45c851b7497cc14d5ca060064394569f724b67d9b5f98a926ed49b834a6bb73a  Anaconda3-2019.03-Linux-x86_64.sh
```

Run the script:
```bash
$ bash Anaconda3-2019.03-Linux-x86_64.sh
```

You'll get this output:
```bash
Output

Welcome to Anaconda3 2019.03

In order to continue the installation process, please review the license
agreement.
Please, press ENTER to continue
>>> 
```

Press `ENTER` and read through the license, then type `yes` to agree and install. 
At this point, you’ll be prompted to choose the location of the installation. You can press `ENTER` to accept the default location, or specify a different location to modify it.

```bash
Anaconda3 will now be installed into this location:
/home/nquach/anaconda3

  - Press ENTER to confirm the location
  - Press CTRL-C to abort the installation
  - Or specify a different location below

[/home/nquach/anaconda3] >>> 
```
Installation will take some time. Let it complete and then you'll see this output:
```bash
...
installation finished.
Do you wish the installer to prepend the Anaconda3 install location
to PATH in your /home/nquach/.bashrc ? [yes|no]
[no] >>> 
```
Type `yes` to allow use of the `conda` command.

### Setting up a virtual environment
Virtual environments allows you to download different dependencies for different projects. Here we will create one called `anonymize`:
```bash
$ conda create --name anonymize python=3
```

Type `y` to download all the packages.

Activate the environment by typing:
```bash
$ source activate anonymize
```
Once activate you should see your command prompt change to:
```bash
(anonymize) nquach@sherlock.stanford.edu:
```

### Download dependencies for scripts
Enter into the ~/anonymize folder. To download all the dependencies needed, simply type:
```bash
$ pip install -r requirements.txt
```
## Anonymizing DICOMS
Place DICOMs to be anonymized in the `/raw_dicoms` folder. The name of the files MUST NOT have private information in it! The script will name the anonymized files based off of the original file name. Anonymized DICOMS will appear in the `/anonymized_dicoms` folder. The anonymized files will have all metadata containing private health information removed. The patient ID will be changed from the MRN to an anonymized patient identifier specified in a csv file. The csv file must be formatted to have two columns, one with MRNs and another with the new anonymized patient specific identifier. You will specify the filename of this csv file in the `--mrn` flag argument. You will also need to specify the `--phi_loc` flag, which specifies which mask preset. Currently supports the following presets:
- 'top' = preset for Phillips/GE with banner at the top
- 'no_top' = preset for Phillips/GE with no banner at the top
- 'none' = doesnt apply a mask (no bounding box either)
- 'boundingbox' = just applies bounding box
- 'spectrum_high' = preset for Octave with a normal scanning sector
- 'spectrum_offaxis' = preset for Octave with tilted scanning sector. 
Optional flags are `-m` which enables multiprocessing (default is True), and `-s` which sorts dicoms by REDCap ID and prints the first image of the ECHO. Once everything is set up, simply type in 
```bash
$ python anonymize.py --mrn=name_map.csv --phi_loc=top 
```
Example output:
```bash
Anonymizing DICOM_example.dcm ...
Saving...
6a.dcm complete!
3.4569029808044434 seconds to run
```
CHECK TO SEE IF ALL PATIENT INFORMATION HAS BEEN BLACKED OUT (ZERO'ED). If not, open `anonymize.py` and change the variables for the 2D mask to appropriate values. Use the `preflight.py` script to verify that the PatientID metadata has been erased








