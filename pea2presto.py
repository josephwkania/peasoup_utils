#!/usr/bin/env python3
import os, argparse, time, sys, subprocess
import  xml.etree.ElementTree as ET
import numpy as np

class peasoup2presto(object):
    def __init__(self, **options):
        self.options = options

    def checkForFiles(options):
        if not os.path.exists(options['xml']):#see if file is there
            print(f"File \'{options['xml']}\' does not exist, exiting")
            sys.exit()
        if not os.path.exists(options['results']):#see if file is there
            print(f"Directory \'{options['psrfile']}\' does not exist, will try to create.")
            os.makedirs(options['results'])
        if options['mask']:
            if not os.path.exists(options['mask']):#see if file is there
                print(f"File \'{options['mask']}\' does not exist, exiting")
                sys.exit() 


    def peasoup2presto(self):
        start = time.time #time the run
        
        peasoup2presto.checkForFiles(self.options)

        tree = ET.parse(self.options['xml'])
        root = tree.getroot()
        numCands = len(root.find('candidates'))
        candidateTable = np.empty([numCands,3], dtype=float)
        for i, candidate in enumerate(root.find('candidates')):
            periodOpt = float(candidate.find('opt_period').text)#use the optimal period if avaliable
            if periodOpt > 0.0:
                 candidateTable[i][0] = periodOpt
            else:
                candidateTable[i][0] = float(candidate.find('period').text)
            candidateTable[i][1] = float(candidate.find('dm').text)
            snr = float(candidate.find('snr').text)
            folded_snr = float(candidate.find('folded_snr').text)
            candidateTable[i][2] = max(snr, folded_snr)
        
        for i in range(min(numCands, self.options['number'])):
            if candidateTable[i][2]<=self.options['snr']:
                break
            print(f"sending canidate #{i:02}, with period={candidateTable[i][0]:.7f}, dm={candidateTable[i][1]:.3f}, snr={candidateTable[i][2]:.3f} to presto")
            if self.options['mask']:
                prst = f"/opt/pulsar/src/PRESTOv2.7/bin/prepfold -p {candidateTable[i][0]} -dm {candidateTable[i][1]} {self.options['psrfile']} -o {self.options['results']} -noxwin -mask {self.options['mask']}"
            else:
                prst = f"/opt/pulsar/src/PRESTOv2.7/bin/prepfold -p {candidateTable[i][0]} -dm {candidateTable[i][1]} {self.options['psrfile']} -o {self.options['results']} -noxwin"
            out = subprocess.run(['sbatch', '--job-name', 'pea2prst', '--wrap', prst], stdout=subprocess.PIPE)
            print(out.stdout)
        

if __name__ == "__main__":
    parser=argparse.ArgumentParser(
        description="Use Presto to optimize and view peasoup canidates",
        prog='peasoup2presto',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )

    required=parser.add_argument_group('required arguments:')
    required.add_argument('-x','--xml',type=str,
                          help="peasoup .xml file to analyze",
                          required=True)
    required.add_argument('-p','--psrfile',type=str,
                          help="filterbank to fold",
                          required=True)

    semi_opt=parser.add_argument_group('arguments set to defaults:')
    #semi_opt.add_argument('-t','--temp',type=str,
    #                      help='path where intermediate are saved',
    #                      default="./temp")
    semi_opt.add_argument('-r','--results',type=str,
                          help='path where results are saved',
                          default="./results")
    semi_opt.add_argument('-n','--number',type=int,
                          help='number of canidates to send to presto, starts with highest snr canidates',
                          default=50)
    semi_opt.add_argument('-s','--snr',type=int,
                          help='min snr of canidates to send to presto.',
                          default=6)

    optional=parser.add_argument_group('other optional arguments')
    optional.add_argument('-m', '--mask', type=str,
                          help='rfifind mask to use to make prepfolds')

    

    args = vars(parser.parse_args())
    peasoup2presto(**args).peasoup2presto()
