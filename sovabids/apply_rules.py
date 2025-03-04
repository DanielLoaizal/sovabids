import os
import mne_bids
import json
import yaml
import argparse
from sovabids.utils import deep_merge_N,get_supported_extensions,get_files,macro, run_command,split_by_n,parse_string_from_template,mne_open
from mne_bids import BIDSPath, read_raw_bids, print_dir_tree, make_report,write_raw_bids
from copy import deepcopy


def get_info_from_path(path,rules_):
    rules = deepcopy(rules_)
    patterns_extracted = {}
    if 'splitter' in rules.get('non-bids',{}):
        splitter = rules['non-bids']['splitter']
    else:
        splitter = '%'

    if "path_pattern" in rules.get('non-bids',{}):
        patterns_extracted = parse_string_from_template(path,rules['non-bids']['path_pattern'],splitter)
    if 'ignore' in patterns_extracted:
        del patterns_extracted['ignore']
    # this what needed because using rules.update(patterns_extracted) replaced it all
    rules = deep_merge_N([rules,patterns_extracted])
    return rules

def load_rules(rules_):
    if not isinstance(rules_,dict):
        with open(rules_,encoding="utf-8") as f:
            return yaml.load(f,yaml.FullLoader)
    return rules_
def apply_rules(source_path,bids_root,rules_):

    rules_ = load_rules(rules_)
    # Generate all files
    try:
        extensions = rules_['non-bids']['eeg_extension']
    except:
        extensions = get_supported_extensions()

    if isinstance(extensions,str):
        extensions = [extensions]

    # append dot to extensions if missing
    extensions = [x if x[0]=='.' else '.'+x for x in extensions]

    filepaths = get_files(source_path)
    filepaths = [x for x in filepaths if os.path.splitext(x)[1] in extensions]

    #%% BIDS CONVERSION

    for f in filepaths:
        rules = deepcopy(rules_) #otherwise the deepmerge wont update the values for a new file

        # Upon reading RAW MNE makes the assumptions
        raw = mne_open(f)

        # First get info from path

        rules = get_info_from_path(f,rules)

        # Apply Rules
        assert 'entities' in rules
        entities = rules['entities'] # this key has the same fields as BIDSPath constructor argument

        if 'sidecar' in rules:
            sidecar = rules['sidecar']
            if "PowerLineFrequency" in sidecar:
                raw.info['line_freq'] = sidecar["PowerLineFrequency"]  # specify power line frequency as required by BIDS
            # Should we try to infer the line frequency automatically from the psd?

        if 'channels' in rules:
            channels = rules['channels']
            if "type" in channels:
                raw.set_channel_types(channels["type"])

        if 'non-bids' in rules:
            non_bids = rules['non-bids']
            if "code_execution" in non_bids:
                if isinstance(non_bids["code_execution"],str):
                    non_bids["code_execution"] = [non_bids["code_execution"]]
                if isinstance(non_bids["code_execution"],list):
                    for command in non_bids["code_execution"]:
                        exec(macro)
                        #raw = run_command(raw,command) #another way...
                        # maybe log errors here?


        bids_path = BIDSPath(**entities,root=bids_root)
        write_raw_bids(raw, bids_path=bids_path,overwrite=True)

        # Rules that need to be applied to the result of mne-bids
        # Or maybe we should add the functionality directly to mne-bids

        if 'sidecar' in rules:
            sidecar_path = bids_path.copy().update(suffix='eeg', extension='.json')
            with open(sidecar_path.fpath) as f:
                dummy_dict = json.load(f)
                sidecar = rules['sidecar']
                dummy_dict.update(sidecar)
                # maybe include an overwrite rule
                mne_bids.utils._write_json(sidecar_path.fpath,dummy_dict,overwrite=True)

    # Grab the info from the last file to make the dataset description
    if 'dataset_description' in rules:
        dataset_description = rules['dataset_description']
        if 'Name' in dataset_description:
            # Renaming for mne_bids.make_dataset_description support
            dataset_description['name'] = dataset_description.pop('Name')
        if 'Authors' in dataset_description:
            dataset_description['authors'] = dataset_description.pop('Authors')

        mne_bids.make_dataset_description(bids_root,**dataset_description,overwrite=True)
        # Problem: Authors with strange characters are written incorrectly.

def main():
    """Console script usage"""
    # see https://github.com/Donders-Institute/bidscoin/blob/master/bidscoin/bidsmapper.py for example of how to make this
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser = subparsers.add_parser('apply_rules')
    parser.add_argument('source_path')  # add the name argument
    parser.add_argument('bids_root')  # add the name argument
    parser.add_argument('rules')  # add the name argument
    args = parser.parse_args()
    apply_rules(args.source_path,args.bids_root,args.rules)

if __name__ == "__main__":
    main()