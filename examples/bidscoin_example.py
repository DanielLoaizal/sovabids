from bidscoin.plugins.sova2coin import is_eeg,is_sourcefile,get_eegfield,get_attribute,bidsmapper_plugin
from pathlib import Path
from bidscoin.bidscoiner import bidscoiner
from bidscoin.bidsmapper import bidsmapper
import os
import shutil
from numpy import source
from sovabids.utils import get_files

this_dir = os.path.dirname(__file__)
data_dir = os.path.join(this_dir,'..','_data')
data_dir = os.path.abspath(data_dir)
example_dir = os.path.abspath(os.path.join(this_dir,'..','examples'))

source_path = os.path.abspath(os.path.join(data_dir,'lemon_bidscoin_input'))
bids_root= os.path.abspath(os.path.join(data_dir,'lemon_bidscoin_output'))
rules_path = os.path.join(example_dir,'bidscoin_example_rules.yml')
bidsmap_path = os.path.join(example_dir,'bidscoin_example_bidsmap.yml')


files = get_files(source_path)
any_vhdr = Path([x for x in files if '.vhdr' in x][0])
any_not_vhdr = Path([x for x in files if '.vhdr' not in x][0])

assert is_sourcefile(any_vhdr)=='EEG'
assert is_sourcefile(any_not_vhdr)==''
assert get_eegfield('sidecar.SamplingFrequency',any_vhdr) == 2500.0
assert get_attribute('EEG',any_vhdr,'sidecar.SamplingFrequency') == 2500.0

bidsmap = """# --------------------------------------------------------------------------------
# This is a bidsmap YAML file with the key-value mappings for the different BIDS
# datatypes (anat, func, dwi, etc). The datatype attributes are the keys that map
# onto the BIDS labels. The bidsmap data-structure should be 5 levels deep:
#
# dict       : dict     : list     : dict        : dict
# dataformat : datatype : run-item : bidsmapping : mapping-data
#
# NB:
# 1) Edit the bidsmap file to your needs before feeding it to bidscoiner.py
# 2) (Institute) users may create their own bidsmap_[template].yaml or
#    bidsmap_[sample].yaml file
#
# For more information, see: https://bidscoin.readthedocs.io
# --------------------------------------------------------------------------------


Options:
# --------------------------------------------------------------------------------
# General options and plugins
# --------------------------------------------------------------------------------
  bidscoin:
    version: 3.7.0-dev            # BIDScoin version (should correspond with the version in ../bidscoin/version.txt)
    bidsignore: extra_data/       # Semicolon-separated list of entries that are added to the .bidsignore file (for more info, see BIDS specifications), e.g. extra_data/;pet/;myfile.txt;yourfile.csv
    subprefix: sub-               # The subject prefix of the source data
    sesprefix: ses-               # The session prefix of the source data
  plugins:                        # List of plugins with plugin-specific key-value pairs (that can be used by the plugin)
    dcm2bidsmap:                  # The default plugin that is used by the bidsmapper to map DICOM and PAR/REC source data
    dcm2niix2bids:                # See dcm2niix -h and https://www.nitrc.org/plugins/mwiki/index.php/dcm2nii:MainPage#General_Usage for more info
      path: module add dcm2niix;  # Command to set the path to dcm2niix (note the semi-colon), e.g. module add dcm2niix/1.0.20180622; or PATH=/opt/dcm2niix/bin:$PATH; or /opt/dcm2niix/bin/ or '"C:\Program Files\dcm2niix\"' (note the quotes to deal with the whitespace)
      args: -b y -z y -i n        # Argument string that is passed to dcm2niix. Tip: SPM users may want to use '-z n' (which produces unzipped nifti's, see dcm2niix -h for more information)
    sova2coin:            #module add sovabids #
      rules_file : {}
      non-bids:
        path_pattern : /%ignore%/ses-%entities.session%/%entities.task%/sub-%entities.subject%.vhdr #USE POSIX

EEG:
# --------------------------------------------------------------------------------
# Physio key-value heuristics (phys2bids -info data) that are mapped to the BIDS labels)
# --------------------------------------------------------------------------------
  subject: <<entities.subject>> #<<PathPattern>>     # <<SourceFilePath>> extracts the subject label from the source directory during bidscoiner runtime
  session: <<entities.session>> #sub-%subject%/ses-%session%/%task%/%ignore%     # <<SourceFilePath>> extracts the session label from the source directory during bidscoiner runtime

  eeg:        # ----------------------- All behavioural runs --------------------
  - provenance:                   # The fullpath name of the source file from which the attributes are read. Serves also as a look-up key to find a run in the bidsmap
    filesystem:                   # This is what phys2bids is using now (well, part of it)
      path:                       # File folder, e.g. ".*Parkinson.*" or ".*(phantom|bottle).*"
      name:         "(.*)"        # File name, e.g. ".*fmap.*" or ".*(fmap|field.?map|B0.?map).*"
      size:                       # File size, e.g. "2[4-6]\d MB" for matching files between 240-269 MB
      nrfiles:                    # Number of files in the folder that match the above criteria, e.g. "5/d/d" for matching a number between 500-599
    attributes:                   # The matching (regexp) criteria for the phys2bids -info data go in here
      sidecar.SamplingFrequency:
      sidecar.PowerLineFrequency:
      sidecar.RecordingDuration:
      entities.subject:
      entities.task:
      entities.session:
    bids:
      task: <<entities.task>> # Note Dynamic values are not previewed in the bids editor but they do work, this should be fixed anyway
      acq: 
      recording:
      run: <<1>>                  # This will be updated during bidscoiner runtime (as it depends on the already existing files)
      suffix: eeg
    meta:                         # This is an optional entry for meta-data dictionary that will be appended to the json sidecar files produced by mne-bids
""".format(rules_path)

with open(bidsmap_path,mode='w') as f:
    f.write(bidsmap)

#CLEAN BIDS PATH
try:
    shutil.rmtree(bids_root)
except:
    pass

bidsmapper(rawfolder=source_path,bidsfolder=bids_root,subprefix='sub-',sesprefix='ses-',bidsmapfile='bidsmap.yaml',templatefile= bidsmap_path,)

bidscoiner(rawfolder    = source_path,
            bidsfolder   = bids_root,just_wrap=True)