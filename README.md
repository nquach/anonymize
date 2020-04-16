# DICOM Anonymizer
This script allows automated anonymizing of echocardiogram DICOM files. Scrubs all private health information stored in metadata as well as blacks out the top and sides to remove private information listed in the banner. 

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
Place DICOMs to be anonymized in the `/raw_dicoms` folder. The name of the files MUST NOT have private information in it! The script will name the anonymized files based off of the original file name. Anonymized DICOMS will appear in the `/anonymized_dicoms` folder. The anonymized files will have all metadata containing private health information removed. The patient ID will be changed from the MRN to an anonymized patient identifier specified in `name_map_demo.csv`. `name_map_demo.csv` must be formatted to have two columns, one with MRNs and another with the new anonymized patient specific identifier. Once everything is set up, simply type in 
```bash
$ python anonymize.py 
```
Example output:
```bash
Anonymizing 6i.dcm ...
Saving...
6i.dcm complete!
3.4569029808044434 seconds to run
```
CHECK TO SEE IF ALL PATIENT INFORMATION HAS BEEN BLACKED OUT. If not, open `anonymize.py` and change the variables for the 2D mask to appropriate values.

Test DICOMS that go with the `name_map.csv` file can be downloaded here for a test run: https://drive.google.com/drive/folders/1XgdIY1ZRzWjuWjXZbwSB_DIo5Hi5uKBD?usp=sharing

Make sure to delete `blank.dcm` placeholder files before running the script on real DICOMS! 





