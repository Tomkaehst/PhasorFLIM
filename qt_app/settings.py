# AG BP FLIM Fitter --- Class: settings()
'''
Class: settings()
---

Author: Tom Kache, University Hospital Jena
April 2020
'''

class settings():
    def __init__(self, application_state):
        self.application_state = application_state


    def save_settings_to_disk(self):
        pass


    def load_settings(self):
        pass

    def get_current_settings(self):
        states_to_save = [
            self.application_state.ptupath,
            self.application_state.irf_object.file_path
            
        ]

    def apply_settings(self):
        pass