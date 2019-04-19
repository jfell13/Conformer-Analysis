#! /usr/bin/env python

#################################################
# Create abd submit Gaussian16 files from       #
# conformer pdbs                                #
#################################################

import sys
import os
import argparse 

#Generate xyz
for i in os.listdir('.'):
        if i[-4:] == '.pdb':
                os.system('/software/openbabel/2.4.0/lssc0-linux/bin/babel -ipdb %s -oxyz %s.xyz' % (i, i[:-4]))

xyz_files = os.listdir(".")
temp_list = xyz_files[:]
for file in temp_list:
        if not file.endswith(".xyz"):
                xyz_files.remove(file)

# parse commandline options 
parser = argparse.ArgumentParser(description='Create Gaussian16 optimization file from pdb')
parser.add_argument(
	'-t', type=str, dest='theory', 
	default = 'B3LYP', 
	help = 'Theory to use (default: B3LYP)'
	)
parser.add_argument(
	'-b', type=str, dest='basis', 
	default = '6-311G(d,p)', 
	help = 'Basis Set (default: 6-311G(d,p))'
	)
parser.add_argument(
        '-d', type=str, dest='disp',
        default = '',
        help = 'Additional dispersion correction (Options: GD2, GD3, or GD3BJ; default: none)'
        )
parser.add_argument(
        '-s', type=str, dest='solv',
        default = '',
        help = 'Additional IEFPCM solvation (Options:  ethanol, chcl3, ch2cl2, or water; default: none)'
        )
parser.add_argument(
        '-c', type=int, dest='charge',
        default = '0',
        help = 'Molecular charge (default: 0)'
        )

args = parser.parse_args()

#Dispersion Arguments
if args.disp == 'GD2':
        args.disp = 'EmpiricalDispersion=GD2 '
if args.disp == 'GD3':
        args.disp = 'EmpiricalDispersion=GD3 '
if args.disp == 'GD3BJ':
        args.disp = 'EmpiricalDispersion=GD3 '
        
#Solvation Arguments
if args.solv == 'ethanol':
        args.solv = 'SCRF=(Solvent=Ethanol) '
if args.solv == 'chcl3':
        args.solv = 'SCRF=(Solvent=Chloroform) '
if args.solv == 'ch2cl2':
        args.solv = 'SCRF=(Solvent=Dichloromethane) '
if args.solv == 'water':
        args.solv = 'SCRF=(Solvent=Water) '
        
# create list of all chk files in the current directory 
xyz_files = os.listdir(".")
temp_list = xyz_files[:]
for file in temp_list: 
	if not file.endswith(".xyz"): 
		xyz_files.remove(file)
		
# create a Gaussian16 opt file for every xyz file 
# remove spaces and parenthesis when necessary 
for file in xyz_files:
	g16_filename = file.replace(' ', '') 
	g16_filename = g16_filename.replace('(', '') 
	g16_filename = g16_filename.replace(')', '')
	print g16_filename 
	g16_input = open(g16_filename[:-3]+"com", "w")
        xyz_coordinates = open(file).readlines()
        # write header 	
	g16_input.write("%chk="+g16_filename[:-4]+".chk\n")
	g16_input.write("#" + args.theory)
        g16_input.write("/" + args.basis)
        g16_input.write(" ")
        g16_input.write(str(args.disp))
        g16_input.write(" ")
        g16_input.write(str(args.solv))
        g16_input.write(" Freq=NoRaman\n")
	g16_input.write("\n")
	g16_input.write(g16_filename[:-4] + "\n")
	g16_input.write("\n")
	g16_input.write(str(args.charge) + "  1\n")
        # insert coordinates
        for line in xyz_coordinates[2:]:
                g16_input.write(line)
	g16_input.write("\n")
	g16_input.close() 
        
# Create submission files for Barbera#
for i in os.listdir('.'):
        if i[-4:] == '.com':
                name = i[:-4]
                with open('%s.sh' % (name), 'w') as sub_f:
                        sub_f.write('#!/bin/bash\n')
                        sub_f.write('#SBATCH --job-name=%s\n' % (i[:8]))
                        sub_f.write('#SBATCH --output=%s.log\n' % (name))
                        sub_f.write('#SBATCH --error=%s.err\n' % (name))
                        sub_f.write('#SBATCH --mem-per-cpu=20G\n')
                        sub_f.write('#SBATCH --nodes=1\n')
                        sub_f.write('#SBATCH --time=1-0\n')
                        sub_f.write('#SBATCH --partition=production\n\n')
                        sub_f.write('module load gaussian\n')
                        sub_f.write('source $g16root/g16/bsd/g16.profile\n')
                        sub_f.write('g16 %s\n' % (i))
                        sub_f.close()

#Submission of files:
for j in os.listdir('.'):
        if j[-3:] == '.sh':
                os.system('sbatch %s' % (j))
