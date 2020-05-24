'''
Created by Rohan Shad, May 23 2020

Preflight testing to make sure ECHO files are appropriately de-identified prior to sending

'''

import os
import numpy as np
import pydicom as dcm
import csv
from shutil import move
import argparse
import random

def preflight_checks(rawflag,verbose):
	if rawflag:
		print('Checking anonymized files...')
	else:
		print('Checking raw files...')

	root_direc = os.getcwd()
	dcm_direc = os.path.join(root_direc, 'raw_dicoms')
	anon_direc = os.path.join(root_direc, 'anonymized_dicoms')
	
	if rawflag == False:
		file_dir = dcm_direc
	else:
		file_dir = anon_direc

	filenames = os.listdir(file_dir)
	file_list_final = []
	
	for f in filenames:
		if ".dcm" in f:
			file_list_final.append(f)
		
	if file_list_final == []:
		print('No DICOM files found')
	else:
		random_file = random.choice(file_list_final)
		ds = dcm.dcmread(os.path.join(file_dir, random_file))
		if ds.file_meta.TransferSyntaxUID.is_compressed is True:
				ds.decompress()
		if verbose:
			print(ds)
		else:
			print(ds.PatientID)

###################################################

if __name__ == '__main__':

	parser = argparse.ArgumentParser(

        description="This is the Hiesinger Lab DICOM preflight script \
                      WARNING: Working directory must have a 'raw_dicoms' and 'anonymized_dicoms' for this to work.\
                      Usage is 'python preflight.py [-r]'",

        epilog="Version 1.0; Rohan Shad, MD"
    )

	parser.add_argument("-r", "--raw_dicom_check", action='store_false', help = "raw_dicom preflight_checks (off by default)")
	parser.add_argument("-v", "--verbose", action='store_true', help = "Print full DICOM tag list (off by default)")

	args = vars(parser.parse_args())
	#print(args)

	preflight_checks(args['raw_dicom_check'],args['verbose'])
