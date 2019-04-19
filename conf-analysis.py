#! /usr/bin/env python

################################################################################
# Extract SCF energies from all Gaussian output files in the current directory # 
################################################################################

import sys
import os
import math
import argparse 

# Parser commandline options #
parser = argparse.ArgumentParser(description='Name of conformer file')
parser.add_argument(
        '-f', metavar='<string>', dest='filename',
        default='conformers.confs.pdb', help='Conformer File Name (Use x.confs.pdb)')

args = parser.parse_args()

# Constants #
GAS_CONSTANT = 8.3144621
PLANCK_CONSTANT = 6.62606957e-34
BOLTZMANN_CONSTANT = 1.3806488e-23
SPEED_OF_LIGHT = 2.99792458e10
FREQ_CUTOFF = 100.000
imaginary = 0
temperature = 298.15

# Function #
def calc_entropy(frequency_wn, temperature):
        """
        Calculates the entropic contribution (cal/(mol*K)) of a harmonic oscillator for
        a list of frequencies of vibrational modes
        """
        entropy = 0
        frequency = [entry * SPEED_OF_LIGHT for entry in frequency_wn]
        for entry in frequency:
                factor = ((PLANCK_CONSTANT*entry)/(BOLTZMANN_CONSTANT*temperature))
                temp = factor*(1/(math.exp(factor)-1)) - math.log(1-math.exp(-factor))
                temp = temp*GAS_CONSTANT/4.184
                entropy = entropy + temp
        return entropy

# Variables #
frequencies = []
frequencies_unprojected = []
frequency_wn = []

output = open('energies.txt', 'w')

all_files = os.listdir(".")
g16_files = []
energies = {}
scf_energy = 0

# Create list with Gaussian 16 output files
for file in all_files: 
	if file.endswith(".log"): 
		g16_files.append(file)
                
for entry in g16_files:
        g16_output = open(entry, 'r')
        # Iterate over output
        for line in g16_output:
                # look for low frequencies
                if line.strip().startswith('Frequencies --'):
                        for i in range(2,5):
                                x = float(line.strip().split()[i])
                                frequencies.append(x)
                # look for unprojected low frequencies
                if line.strip().startswith('Low frequencies'):
                        frequencies_unprojected.extend(line.strip().split()[3:])
                # look if Gaussian finds an imaginary frequency
                if line.strip().startswith('******    1 imaginary'):
                        imaginary = 1
                # look for SCF energies, last one will be correct
                if line.strip().startswith('SCF Done:'):
                        scf_energy = float(line.strip().split()[4])
                # look for thermal corrections
                if line.strip().startswith('Zero-point correction='):
                        zero_point_corr = float(line.strip().split()[2])
                if line.strip().startswith('Thermal correction to Energy='):
                        energy_corr = float(line.strip().split()[4])
                if line.strip().startswith('Thermal correction to Enthalpy='):
                        enthalpy_corr = float(line.strip().split()[4])
                if line.strip().startswith('Thermal correction to Gibbs Free Energy='):
                        gibbs_corr = float(line.strip().split()[6])
        g16_output.close()
        # Calculate Truhlar's correction by raising low frequencies to FREQ_CUTOFF
        entropy = calc_entropy(frequency_wn, temperature)
        correction = (entropy - len(frequency_wn) * calc_entropy([FREQ_CUTOFF], temperature))
        # correction in kcal/mol
        correction = (correction * temperature) / 1000
        # correction in hartree
        correction2 = correction / 627.51
        # quasiharmonic free energy correction
        gibbs_corr_quasi = gibbs_corr + correction2
        # Calculate energies with thermal corrections
        energy = scf_energy + zero_point_corr
        enthalpy = scf_energy + enthalpy_corr
        gibbs_energy = scf_energy + gibbs_corr
        gibbs_energy_quasi = gibbs_energy + correction2
	energies[gibbs_energy_quasi] = entry

# sort according to energy 
temp = energies.keys()
temp.sort() 
# determine which conformers to keep
delta = []

# write to file 
for j in temp: 
	output.write("%-20s %-18.6f %.2f \n" % ((energies[j]), j, ((j-temp[0])*627.51)))
output.close()

#search through outputs
for k in temp:
        deltaqG = (k - temp[0])*627.51
        if deltaqG <= 3.0:
                delta.append(energies[k])
        else:
                pass

#make conformer file
conformer= open('%s' % (args.filename), 'w')
for l in delta:
        name = l[:-4]
        os.system('/software/openbabel/2.4.0/lssc0-linux/bin/babel -ilog %s -opdb %s_final.pdb' % (l, name))
        with open('%s_final.pdb' % (name), 'r') as conf:
                  for line in conf:
                          conformer.write(line)
conformer.close()
