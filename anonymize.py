'''
Created by Nicolas Quach, July 16 2019
Script to anonymize DICOM files. Scrubs metadata of private health information
and blacks out the top banner containing the patient's name/information.

Updated 03/22/19: Blacks out all information on the sides too

Need to adjust the blackout mask accordingly. The mask scales to input dimensions.
'''
import os
import numpy as np
import pydicom as dcm
import multiprocessing
import time
import csv
from shutil import move
from imageio import imsave
import argparse

def safe_makedir(path):
	if not os.path.exists(path):
		os.makedirs(path)

def output_imgdict2(imagefile):
    '''
    converts raw dicom to numpy arrays
    '''
    try:
        ds = imagefile
        nrow = int(ds.Rows)
        ncol = int(ds.Columns)
        ArrayDicom = np.zeros((nrow, ncol), dtype=ds.pixel_array.dtype)
        imgdict = {}
        if len(ds.pixel_array.shape) == 4: #format is (nframes, nrow, ncol, 3)
            nframes = ds.pixel_array.shape[0]
            R = ds.pixel_array[:,:,:,0]
            B = ds.pixel_array[:,:,:,1]
            G = ds.pixel_array[:,:,:,2]
            gray = (0.2989 * R + 0.5870 * G + 0.1140 * B)
            for i in range(nframes):
                imgdict[i] = gray[i, :, :]
            return imgdict
        elif len(ds.pixel_array.shape) == 3: #format (nframes, nrow, ncol) (ie in grayscale already)
            nframes = ds.pixel_array.shape[0]
            for i in range(nframes):
                imgdict[i] = np.invert(ds.pixel_array[i,:,:])
            return imgdict
    except:
        return None

def imresize(arr, shape):
    arr = np.asarray(arr)
    arr = arr.astype(np.uint8)
    return np.array(Image.fromarray(arr).resize(shape))


def anonymize(ds, anon_path, redcap, PHI_loc = 'top'):
	ds.InstanceCreationDate = 'NA'
	ds.InstanceCreationTime = 'NA'
	ds.StudyDate = 'NA'
	ds.SeriesDate = 'NA'
	ds.ContentDate = 'NA'
	ds.AcquisitionDateTime = 'NA'
	ds.StudyTime = 'NA'
	ds.SeriesTime = 'NA'
	ds.AccessionNumber = 'NA'
	ds.ReferringPhysicianName = 'NA'
	ds.PerformingPhysicianName = 'NA'
	ds.PatientName = 'NA'
	ds.PatientID = redcap
	ds.PatientBirthDate = 'NA'
	ds.RequestingPhysician = 'NA'
	ds.PerformedProcedureStepStartDate = 'NA'
	ds.PerformedProcedureStepStartTime = 'NA'
	ds.PerformedProcedureStepID = 'NA'
	ds.StudyID = 'NA'

	#Note that ds.pixel_array has shape (frames, rows, cols, channel), though channels is option
	#ds.pixel_array has type uint8. Typecast accordingly!

	mask = np.ones(ds.pixel_array.shape[1:3], dtype=np.uint8)

	###GENERATE 2D MASKS HERE### (im sorry there are lots of magic numbers)
	if PHI_loc == 'top':
		crop_pixels = int((60/600)*ds.pixel_array.shape[1]) 
		mask[:,:crop_pixels] = 0 #Crop the top
		UpperRight = np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(330*ds.pixel_array.shape[2]/800), dtype=np.uint8)
		UpperLeft = np.fliplr(np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(260*ds.pixel_array.shape[2]/800), dtype=np.uint8))
		LowerRight = np.flipud(np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(619*ds.pixel_array.shape[2]/800), dtype=np.uint8))
		mask = mask * UpperRight * UpperLeft * LowerRight

	elif PHI_loc == 'none':
		UpperRight = np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(347*ds.pixel_array.shape[2]/800), dtype=np.uint8)
		UpperLeft = np.fliplr(np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(300*ds.pixel_array.shape[2]/800), dtype=np.uint8))
		LowerRight = np.flipud(np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(700*ds.pixel_array.shape[2]/800), dtype=np.uint8))
		mask = mask * UpperRight * UpperLeft * LowerRight
	else:
		print(PHI_loc, 'is not a valid value for argument PHI_loc!')
		exit(1)

	final_mask = np.ones(ds.pixel_array.shape) #the final mask must be the same 
	
	##Expand the 2D mask into 3 or 4 dimensions, then apply to movie##
	if len(ds.pixel_array.shape) == 4:
		channel3mask = np.transpose(np.tile(mask, (3,1,1)), (1,2,0)) #transposition required since tile puts channel in axis=0
		final_mask = np.tile(channel3mask, (ds.pixel_array.shape[0],1,1,1))
		final_mask.astype(np.uint8)
		newarr = final_mask * ds.pixel_array 
	elif len(ds.pixel_array.shape) == 3:
		final_mask = np.tile(mask, (ds.pixel_array.shape[0],1,1))
		final_mask.astype(np.uint8)
		newarr = final_mask * ds.pixel_array
	else:
		print('NOT A TIME SERIES! Skipping...')
		return

	print('Saving...')
	ds.PixelData = newarr.tobytes()
	dcm.filewriter.write_file(anon_path, ds)


def anonymize_all(filename, PHI_loc):
	ds = dcm.dcmread(os.path.join(dcm_direc, filename))
	if ds.file_meta.TransferSyntaxUID.is_compressed is True:
		ds.decompress()

	MRN = ds.PatientID
	MRN = MRN.strip()
	redcap = name_dict[MRN]
	
	if filename[-3:] != 'dcm':
		anon_path = os.path.join(anon_direc, 'anon_' + filename + '.dcm')
	else:
		anon_path = os.path.join(anon_direc, 'anon_' + filename)

	print('Anonymizing ' + filename + ' ...')
	anonymize(ds, anon_path, redcap, PHI_loc)
	print(filename + ' complete!')



def start_program(PHI_loc, multiprocess, sort_echos, mrn_redcap_filename):
	start = time.time()

	#####################
	#Deprecated section since it's all argparse now#
	###SET PARAMETERS HERE#####
	###Options for masks include 'top', 'none'
	#PHI_loc = 'none' #set which mask to use
	#multiprocess = True #turns on multiprocessing
	#sort_echos = True #sorts echos by redcap ID in destination folder
	#mrn_redcap_filename = 'name_map.csv' #set this to the csv with MRN to REDCap mapping
	#####################

	print("Using mode: " + PHI_loc)
	if multiprocess == 'True':
		print('Multiprocessing mode ON')
	else:
		print('Multiprocessing mode OFF')

	if anonymize_bool:
		print("Anonymizing ON")
	else:
		print("Anonymizing OFF")

	if sort_echos:
		print("Sorting echos ON")
	else:
		print("Sorting echos OFF")

	#Sets current working directory
	root_direc = os.getcwd()
	dcm_direc = os.path.join(root_direc, 'raw_dicoms')
	anon_direc = os.path.join(root_direc, 'anonymized_dicoms')

	#Read in mapping of MRN to REDCap (or other unique anonymous identifier)
	name_dict = {}
	with open(os.path.join(root_direc, mrn_redcap_filename)) as fp:
		line = fp.readline()
		counter = 0
		while line:
			if counter == 0:
				counter += 1
				line = fp.readline()
				continue
			else:
				line = line.strip('\n')
				items = line.split(',')
				MRN = items[0]
				new_name = items[1]
				if MRN not in name_dict.keys():
					name_dict[MRN] = new_name
				line = fp.readline()
				counter += 1

	#Starts a multiprocessing pool and start a new process for each dicom file when a CPU becomes avaialable
	if anonymize_bool:
		p = multiprocessing.Pool()
		filenames = os.listdir(dcm_direc)

		for f in filenames:
			if f[-3:] == 'dcm':
				if multiprocess:
					p.apply_async(anonymize_all,[f, PHI_loc])
				else:
					print('NOT MULTIPROCESSING')
					anonymize_all(f, PHI_loc)
			else:
				continue
		p.close()
		p.join()

	#Print statement for time taken to compute
	print(str(time.time() - start) + ' seconds to run')

	#############################################
	#This part sorts anonymized echos by REDCAP ID
	if sort_echos == 'True':
		dicompath = anon_direc

		bad_file_list = []

		filenames = os.listdir(dicompath)
		for filename in filenames:
			print('Processing ' + filename + '...')
			if (os.path.isfile(os.path.join(dicompath, filename)) == False) or (filename[-3:] != 'dcm'):
				print('NOT A DICOM')
				continue
			else:
				path = os.path.join(dicompath, filename)
				try:
					ds = dcm.dcmread(os.path.join(dicompath, filename))
				except:
					print("DICOM corrupted! Skipping...")
					continue
				redcap = ds.PatientID
				framedict = output_imgdict2(ds)
				if framedict == None:
					bad_file_list.append(filename)
					print('BAD FILE')
					continue
				nrows = framedict[0].shape[0]
				ncols = framedict[0].shape[1]
				frame0 = framedict[0]
				frame0 = np.reshape(frame0, (nrows, ncols)) * 255
				frame_name = filename + '.jpeg'
				redcap_dir = os.path.join(dicompath, redcap)
				safe_makedir(redcap_dir)
				move(path, os.path.join(redcap_dir, filename))
				imsave(os.path.join(redcap_dir, frame_name), frame0)
		
		print(bad_file_list)
	else:
		print ('Skipping sorting files')

########################################################################################################


if __name__ == '__main__':

	parser = argparse.ArgumentParser(

        description="This is the Hiesinger Lab DICOM anonymizer script \
                      WARNING: Working directory must have a 'raw_dicoms' and 'anonymized_dicoms' for this to work.\
                      Usage is 'python anonymize.py <phi_location> <mrn_filename>'",

        epilog="Version 1.2; Created by Nick Quach (almost entirely) and Rohan Shad, MD"

    )

	parser.add_argument("phi_location", help="The location where ECHO files have hardcoded PHI. Either 'none' or 'top'.",type=str)
	parser.add_argument("-m", metavar='\b', help="Enable / Disable multicore processing. Default is set to TRUE.",type=str, required=False, default='True')
	parser.add_argument("-s", metavar='\b', help="Sorts anonymized ECHOs by REDCAP ID. Default is set to TRUE", type=str, required=False, default='True')
	parser.add_argument("mrn_filename", help="Name of the master key file with MRN and study IDs (include the .csv bit)", type=str)
   

	args = parser.parse_args()
	start_program(args.phi_location, args.m, args.s, args.mrn_filename)


