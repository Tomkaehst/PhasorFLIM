from flimdata import flimdata

class IRF(flimdata):

    def __init__(self, file_path: str, channel: int):

        self.file_path = file_path
        self.channel = channel
        self.spatial_binning = 4
        self.temporal_binning = 0

        super().__init__(
            file_path = self.file_path,
            channel = self.channel,
            spatial_binning = self.spatial_binning,
            temporal_binning = self.temporal_binning
        )

        self.irf = self.overall_decays

        del self.flimarray


    def cut_irf(self, left_cutoff: int, right_cutoff: int, background: int):
        self.irf = self.overall_decays[left_cutoff, right_cutoff]

