#!/bin/env python3
import subprocess, os, argparse

#
# Argparser
#
parser = argparse.ArgumentParser(description='tnp EGM fitter')
parser.add_argument('--createHists', action='store_true', help = 'Create histograms')
parser.add_argument('--firstRound', action='store_true', help = 'Do first round of fits (nominal, altBkg and altSig-mc')
parser.add_argument('--secondRound', action='store_true', help = 'Do second round of fits (altSig-data)')
parser.add_argument('--sumUp', action='store_true', help = 'Create the final SF plots')
args = parser.parse_args()


#
# System and cream02 commands
#
def system(command):
  print(command)
  return subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode()

def makeDir(filename):
  dirname = os.path.dirname(filename)
  try:    os.makedirs(dirname)
  except: pass

def cream02(command, logFile):
  dir = os.getcwd()
  qsubOptions = ['-v dir=%s,command="%s"' % (dir, 'source etc/scripts/setup.sh;%s' % command),
                 '-q localgrid@cream02',
                 '-e %s' % logFile,
                 '-o %s' % logFile,
                 '-l walltime=15:00:00']
  makeDir(logFile)
  try:
    system('qsub %s etc/scripts/runOnCream02.sh' % ' '.join(qsubOptions))
  except subprocess.CalledProcessError as e:
    print(e.output)
    exit(1)


#
# Settings
#
settings      = 'settings_leptonMva.py'
workingpoints = ['passingLeptonMvaTight', 'passingLeptonMvaMedium']
eras          = ['2016', '2017', '2018']

#
# Workflow
#
for era in eras:
  for workingpoint in workingpoints:
    baseCommand = 'python tnpEGM_fitter.py etc/config/%s --flag=%s --configOpts="era=%s"' % (settings, workingpoint, era)

    if args.createHists:
      system('%s --checkBins' % (baseCommand))
      system('%s --createBins' % (baseCommand))
      for sample in ['data' , 'mcNom', 'mcAlt', 'tagSel']:
        logFile = 'log/createHists/%s-%s-%s' % (workingpoint, sample, year)
        cream02('%s --createHists --sample=%s' % (baseCommand, sample), logFile)

    if args.firstRound:
      logFile = 'log/fits-nominal/%s-%s' % (workingpoint, year)
      cream02('%s --doFit' % (baseCommand), logFile)
      logFile = 'log/fits-altSig-mc/%s-%s' % (workingpoint, year)
      cream02('%s --doFit --mcSig --altSig' % (baseCommand), logFile)
      logFile = 'log/fits-altBkg/%s-%s' % (workingpoint, year)
      cream02('%s --doFit --altBkg' % (baseCommand), logFile)

    if args.secondRound:
      logFile = 'log/fits-altSig/%s-%s' % (workingpoint, year)
      cream02('%s --doFit --altSig' % (baseCommand), logFile)

    # Now fix fits
    # e.g.
    #os.system('python tnpEGM_fitter.py etc/config/%s --flag myWP %s --doFit --iBin ib' % (settings, workingpoint))
     
    # Then sum up
    if args.sumUp:
      system('%s --sumUp' % (baseCommand))
