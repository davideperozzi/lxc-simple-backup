#!/usr/bin/python

import sys
import re
import argparse
import subprocess
import time

LXD_CMD = '/usr/bin/lxc'
SNAP_RETAIN = '172800'
SNAP_PREFIX = 'backup_'

def parse_args():
  parser = argparse.ArgumentParser(description='Simple backup automation script')
  parser.add_argument('name', help='The name of the container')
  parser.add_argument('--snap-prefix', default=SNAP_PREFIX, help='The prefix to use for the snapshots (Default: "' + SNAP_PREFIX + '")')
  parser.add_argument('--snap-retain', default=SNAP_RETAIN, help='Max time (in ms) to preserve the snapshots (Default: "' + SNAP_RETAIN + '")')
  parser.add_argument('--dry-run', default='0', help='Set this to "1" if no action should be executed') 

  return parser.parse_args()

def cleanup_snapshots(name, prefix, retain, dryRun):
  result = subprocess.run([LXD_CMD, 'info', name], stdout=subprocess.PIPE)
  lines = result.stdout.decode('UTF-8').splitlines()
  
  for line in lines:
    line = line.strip()
    snapName = None
    snapTime = None
    outputName = re.search('^' + prefix + '[0-9]{1,}', line)
    outputTime = re.search('taken at (.*?) UTC', line)
    
    if outputName is not None:
      snapName = outputName.group(0)    

    if outputTime is not None:
      snapTime = outputTime.group(0)
      snapTime = snapTime.replace('taken at ', '')
      snapTime = snapTime.replace(' UTC', '')
      snapTime = time.strptime(snapTime, '%Y/%m/%d %H:%M')
      snapTime = time.mktime(snapTime)

    if snapTime is not None and snapName is not None:
      currentTime = time.time()
      timeRetain = float(retain)
      
      if snapTime < currentTime - timeRetain: 
        if dryRun == '0':
           subprocess.run([LXD_CMD, 'delete', name + '/' + snapName], stdout=subprocess.PIPE)
        
        print(('Would r' if dryRun == '1' else 'R') + 'emove: ' + name + '/' + snapName)

def create_snapshot(name, prefix, dryRun):
  currentTime = time.time()
  snapName = prefix + ('%.0f' % currentTime)

  if dryRun == '0':
    subprocess.run([LXD_CMD, 'snapshot', name, snapName], stdout=subprocess.PIPE)
  
  print(('Would c' if dryRun == '1' else 'C') + 'reate: ' + name + '/' + snapName)

def main():
  args = parse_args()
  cleanup_snapshots(args.name, args.snap_prefix, args.snap_retain, args.dry_run)
  create_snapshot(args.name, args.snap_prefix, args.dry_run)

if __name__ == "__main__":
    main()
