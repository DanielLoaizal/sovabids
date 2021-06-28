import mne
import numpy as np

class carga_datos(object):

    def tabular_data(self, ch_names, ch_types, sfreq, bad_ch=[], description=[]):
        self.info = mne.create_info(ch_names, sfreq=fs, ch_types=ch_type)
        self.info['description'] = description
        print(self.info)
        if len(bad_ch):
            self.info['bads'] = bad_ch
        return self.info



ch_names = ['Fpz', 'Fp1', 'Fp2', 'Fp3', 'Fp4', 'Fp5', 'Fp6']
bad_ch = ch_names[0:3]
ch_type = 'eeg'
data = np.random.randint(0,10, size=(16, 10000))
fs = 250
# print(bad_ch)
carga = carga_datos()
info = carga.tabular_data(ch_names, ch_types=ch_type, sfreq=fs, bad_ch=bad_ch, )
print(info['bads'])
