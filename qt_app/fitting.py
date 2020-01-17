import flimdata


class fitter:

    def __init__(self, flimdObect: flimdata = None, fitSetting: List = None):

        self.data = flimdObect

        self.settings = fitSetting

        self.guessed_parameters = []
        self.fitted_parameters = []
