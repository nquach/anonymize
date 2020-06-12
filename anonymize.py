'''
Created by Nicolas Quach, July 16 2019
Updated 05/28/20: v1.4 

Script to anonymize DICOM files. Scrubs metadata of private health information
and blacks out the top banner containing the patient's name/information.

Need to adjust the blackout mask accordingly. The mask scales to input dimensions.

By default, all masks except for 'none' black out the areas not in the bounding box
Currently support masks preset (specified by arg --phi_loc flag):
'top' = preset for Phillips/GE with banner at the top
'no_top' = preset for Phillips/GE with no banner at the top
'none' = doesnt apply a mask (no bounding box either)
'boundingbox' = just applies bounding box
'spectrum_high' = preset for Octave with a normal scanning sector
'spectrum_offaxis' = preset for Octave with tilted scanning sector. 

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
import pdb

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
	#ds.StudyDate = 'NA'
	#ds.SeriesDate = 'NA'
	ds.ContentDate = 'NA'
	ds.AcquisitionDateTime = 'NA'
	#ds.StudyTime = 'NA'
	#ds.SeriesTime = 'NA'
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
	ds.PatientAddress = 'NA'
	ds.ReviewerName = 'NA'
	ds.EthnicGroup = 'NA'
	ds.PatientTelephoneNumbers = 'NA'
	ds.OtherPatientIDs = 'NA'
	#Note that ds.pixel_array has shape (frames, rows, cols, channel), though channels is option
	#ds.pixel_array has type uint8. Typecast accordingly!
	mask = np.ones(ds.pixel_array.shape[1:3], dtype=np.uint8)

	#Create bounding box if pixel coordinates are available
	try:
		data = ds[0x0018,0x6011]
		data = data[0]
		Y0 = data[0x0018,0x601A].value
		Y1 = data[0x0018,0x601E].value
		X0 = data[0x0018,0x6018].value
		X1 = data[0x0018,0x601C].value
		#print(X0, X1, Y0, Y1)
	except:
		print("Pixel coordinates are not available!")
		pass

	#create bounding box. black out pixels outside of box
	mask[:Y0, :] = 0
	mask[:, :X0] = 0
	mask[Y1:, :] = 0
	mask[:, X1:] = 0

	###GENERATE 2D MASKS HERE### 
	#(im sorry there are lots of magic numbers, derived from measurements of the scanning sector)
	if PHI_loc == 'top': #default for Phillips if there is a banner at the top
		crop_pixels = int((60/600)*ds.pixel_array.shape[1]) 
		mask[:,:crop_pixels] = 0 #Crop the top
		UpperRight = np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(330*ds.pixel_array.shape[2]/800), dtype=np.uint8)
		UpperLeft = np.fliplr(np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(260*ds.pixel_array.shape[2]/800), dtype=np.uint8))
		LowerRight = np.flipud(np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(619*ds.pixel_array.shape[2]/800), dtype=np.uint8))
		mask = mask * UpperRight * UpperLeft * LowerRight

	elif PHI_loc == 'no_top': #default for Phillips if there is no banner at the top
		UpperRight = np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(347*ds.pixel_array.shape[2]/800), dtype=np.uint8)
		UpperLeft = np.fliplr(np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(300*ds.pixel_array.shape[2]/800), dtype=np.uint8))
		LowerRight = np.flipud(np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(700*ds.pixel_array.shape[2]/800), dtype=np.uint8))
		mask = mask * UpperRight * UpperLeft * LowerRight

	elif PHI_loc == 'none': #literally applies NO MASK
		print('Saving...')
		dcm.filewriter.write_file(anon_path, ds)
		return

	elif PHI_loc == 'boundingbox': #blacks out all pixels outside of the bounding box define by pixel coordinates in metadata
		pass

	elif PHI_loc == 'spectrum_offaxis': #use if the echo is off axis for Octave echoes
		UpperRight = np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(455*ds.pixel_array.shape[2]/636), dtype=np.uint8)
		UpperLeft = np.fliplr(np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(455*ds.pixel_array.shape[2]/636), dtype=np.uint8))
		LowerRight = np.flipud(np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(936*ds.pixel_array.shape[2]/1016), dtype=np.uint8))
		mask = mask * UpperRight * UpperLeft * LowerRight

	elif PHI_loc == 'spectrum_high': #default for Octave echoes
		UpperRight = np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(318*ds.pixel_array.shape[2]/636), dtype=np.uint8)
		UpperLeft = np.fliplr(np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(318*ds.pixel_array.shape[2]/636), dtype=np.uint8))
		LowerRight = np.flipud(np.tri(ds.pixel_array.shape[1], ds.pixel_array.shape[2], int(580*ds.pixel_array.shape[2]/636), dtype=np.uint8))
		mask = mask * UpperRight * UpperLeft * LowerRight
	else:
		print(PHI_loc, 'is not a valid value for argument PHI_loc!')
		exit(1)

	final_mask = np.ones(ds.pixel_array.shape) #the final mask must be the same 
	
	##Makes NFRAME copies of final_mask (2D) and stacks them together to produce a 3D volume
	#that can be applied to the volume of pixel data by pixel-wise multiplication.##

	#Two potential cases, pixel_array has 4 dimensions (frames, X, Y, RGB channel) or 3 dim (X, Y, channel)
	#in the 4 dim case, you need to first stack the 2D final_mask 
	if len(ds.pixel_array.shape) == 4: 
		#np.tile does the copying and stacking of masks into the channel dim to produce 3D masks
		#transposition to convert tile output (channel, X, Y)  into (X, Y, channel)
		channel3mask = np.transpose(np.tile(mask, (3,1,1)), (1,2,0)) 

		#now use np.tile to copy and stack the 3D masks into 4D array to apply to 4D pixel data
		#tile converts (X, Y, channels) —> (frames, X, Y, channels), which is the presumed ordering for 4D pixel data
		final_mask = np.tile(channel3mask, (ds.pixel_array.shape[0],1,1,1))
		final_mask.astype(np.uint8) #conversion to uint8 to avoid warning message
		newarr = final_mask * ds.pixel_array #apply final 4D mask to 4D pixel data
	#greyscale case is easier, no need to stack into the channel dim since it doesnt exist
	elif len(ds.pixel_array.shape) == 3:
		#np.tile converts (X, Y) —> (frames, X, Y)
		final_mask = np.tile(mask, (ds.pixel_array.shape[0],1,1))
		final_mask.astype(np.uint8) #convert to uint8 to avoid warning message
		newarr = final_mask * ds.pixel_array #apply 3D mask to 3D pixel data
	else:
		print('NOT A TIME SERIES! Skipping...')
		return
	

	print('Saving...')
	ds.PixelData = newarr.tobytes()
	
	dcm.filewriter.write_file(anon_path, ds)


def anonymize_all(filename, PHI_loc, name_dict):
	root_direc = os.getcwd()
	dcm_direc = os.path.join(root_direc, 'raw_dicoms')
	anon_direc = os.path.join(root_direc, 'anonymized_dicoms')
	ds = dcm.dcmread(os.path.join(dcm_direc, filename))


	if ds.file_meta.TransferSyntaxUID.is_compressed is True:
		ds.decompress()

	MRN = ds.PatientID
	MRN = MRN.strip()
	if MRN not in name_dict:
		print('MRN ' + MRN + " is not a valid value in mapping")
		return
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
	if multiprocess:
		print('Multiprocessing mode ON')
	else:
		print('Multiprocessing mode OFF')

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
	p = multiprocessing.Pool()
	filenames = os.listdir(dcm_direc)

	for f in filenames:
		if f[-3:] == 'dcm':
			if multiprocess:
				p.apply_async(anonymize_all,[f, PHI_loc, name_dict])
			else:
				print('NOT MULTIPROCESSING')
				anonymize_all(f, PHI_loc, name_dict)
		else:
			continue
	p.close()
	p.join()

	#Print statement for time taken to compute
	print(str(time.time() - start) + ' seconds to run')

	#############################################
	#This part sorts anonymized echos by REDCAP ID
	if sort_echos:
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
                      Usage is 'python anonymize.py --phi_loc=<phi_location> --mrn=<mrn_filename> [-m -s]'",

        epilog="Version 1.4; Created by Nick Quach (almost entirely) and Rohan Shad, MD"

    )

	parser.add_argument("-l", "--phi_loc", required=True, help="The location where ECHO files have hardcoded PHI. Either 'none' or 'top'.")
	parser.add_argument("-m", "--multiprocess", action='store_true', help="Enable / Disable multicore processing.")
	parser.add_argument("-s", "--sort", action='store_true', help="Sorts anonymized ECHOs by REDCAP ID and saves first img of study. Default is set to TRUE")
	parser.add_argument("-f", "--mrn", required=True, help="Name of the master key file with MRN and study IDs (include the .csv bit)")
   

	args = vars(parser.parse_args())
	print(args)

	start_program(args['phi_loc'], args['multiprocess'], args['sort'], args['mrn'])


