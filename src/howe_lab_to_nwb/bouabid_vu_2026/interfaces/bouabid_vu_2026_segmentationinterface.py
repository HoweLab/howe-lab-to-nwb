from pathlib import Path
from typing import Union

from neuroconv.datainterfaces.ophys.basesegmentationextractorinterface import BaseSegmentationExtractorInterface

from howe_lab_to_nwb.bouabid_vu_2026.extractors.bouabid_vu_2026_segmentationextractor import BouabidVu2026SegmentationExtractor


class BouabidVu2026SegmentationInterface(BaseSegmentationExtractorInterface):
    """The interface for reading the ROI masks and locations from custom .mat files from the Howe Lab."""

    display_name = "BouabidVu2026 Segmentation"
    associated_suffixes = (".mat",)
    info = "Interface for BouabidVu2026 segmentation data."

    Extractor = BouabidVu2026SegmentationExtractor

    def __init__(
        self, file_path: Union[str, Path], data_field: str, sampling_frequency: float, accepted_list: list = None, verbose: bool = True
    ):
        """
        DataInterface for reading ROI masks and locations from custom .mat files from the Howe Lab.

        Parameters
        ----------
        file_path : str or Path
            Path to the .mat file that contains the ROI masks and locations.
        data_field : str
            Field within the processed data .mat containing the fiber photometry data.
        sampling_frequency : float
            The sampling frequency of the data.
        accepted_list : list, optional
            A list of the accepted ROIs.
        verbose : bool, default: True
            controls verbosity.
        """
        super().__init__(file_path=file_path, data_field=data_field, sampling_frequency=sampling_frequency, accepted_list=accepted_list)
        self.verbose = verbose

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()
        device_name = "HamamatsuMicroscope"
        metadata["Ophys"]["Device"][0].update(name=device_name)
        return metadata
