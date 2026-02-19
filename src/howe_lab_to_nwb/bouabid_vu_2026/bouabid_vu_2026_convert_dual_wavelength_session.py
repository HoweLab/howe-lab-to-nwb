"""Primary script to run to convert an entire session for of data using the NWBConverter."""
import os
from pathlib import Path
from typing import Union, List

from pymatreader import read_mat
import numpy as np
import os

from howe_lab_to_nwb.bouabid_vu_2026 import single_wavelength_session_to_nwb
 
def dual_wavelength_session_to_nwb(
    raw_imaging_file_paths: List[Union[str, Path]],
    processed_data_file_path: Union[str,Path],
    fiber_photometry_fields: List[str],
    behavior_fields: List[str],
    index_fields: List[str],
    fiber_locations_file_path: Union[str, Path],
    excitation_wavelengths_in_nm: List[int],
    indicators: List[str],
    ttl_file_path: Union[str, Path],
    ttl_stream_names: List[str],
    nwbfile_path: Union[str, Path],
    sampling_frequency: float = -1,
    subject_metadata: dict = None,
    stub_test: bool = False,
):
    """
    Convert a session of data to NWB format.

    Parameters
    ----------
    raw_imaging_file_paths: List[Union[str, Path]]
        The list of paths to the .cxd files containing the raw imaging data.
    processed_data_file_path: Union[str,Path]
        The path to the processed channel-aligned imaging and behavior data
    fiber_photometry_fields: List[str]
        The list of the fields in the processed_data_file_path struct corresponding to the fiber photometry data, according to sensor
    behavior_fields: List[str]
        The list of the fields in the processed_data_file_path struct corresponding to the behavior data, according to sensor
    index_fields: List[str]
        The list of the fields in the processed_data_file_path struct corresponding to the included imaging indices, according to sensor
    fiber_locations_file_path : Union[str, Path]
        The path to the .xlsx file containing the fiber locations.
    excitation_wavelengths_in_nm : List[int]
        The excitation wavelengths in nm for each imaging modality.
    indicators : List[str]
        The indicators used for each imaging modality.
    ttl_file_path : Union[str, Path]
        The path to the .mat file containing the TTL signals.
    ttl_stream_names : List[str]
        The names of the TTL streams.
    nwbfile_path : Union[str, Path]
        The path to the NWB file to write.
    subject_metadata : dict, optional
        The metadata for the subject.
    stub_test : bool, optional
        Whether to run the conversion as a stub test.
    """
    # if motion_corrected_imaging_file_paths is None:
    #     motion_corrected_imaging_file_paths = [None] * len(raw_imaging_file_paths)

    # first_frame_indices, second_frame_indices = None, None
    # second_behavior_data = read_mat(behavior_file_paths[1])
    # if len(set(raw_imaging_file_paths)) != len(raw_imaging_file_paths):
    #     # we need the frame_indices for the imaging data
    #     if len(behavior_file_paths) != len(raw_imaging_file_paths):
    #         raise ValueError("The number of behavior file paths must match the number of imaging files.")
    #     first_behavior_data = read_mat(behavior_file_paths[0])
    #     if "orig_frame_numbers" not in first_behavior_data:
    #         raise ValueError(f"Expected 'orig_frame_numbers' is not in '{behavior_file_paths[0]}'.")
    #     first_frame_indices = list(first_behavior_data["orig_frame_numbers"] - 1)  # MATLAB indexing starts at 1
    #     second_frame_indices = list(second_behavior_data["orig_frame_numbers"] - 1)  # MATLAB indexing starts at 1

    processed_data = read_mat(processed_data_file_path)
    first_behavior_data = processed_data[behavior_fields[0]]
    first_frame_indices = list(np.arange(processed_data[index_fields[0]][0]-1,processed_data[index_fields[0]][1]))
    first_frame_starting_time = first_behavior_data["timestamp"][0]
    second_behavior_data = processed_data[behavior_fields[1]]
    second_frame_indices = list(np.arange(processed_data[index_fields[1]][0]-1,processed_data[index_fields[1]][1]))
    second_frame_starting_time = second_behavior_data["timestamp"][0]

    # Add data from the first excitation wavelength
    nwbfile = single_wavelength_session_to_nwb(
        raw_imaging_file_path=raw_imaging_file_paths[0],
        frame_indices=first_frame_indices,        
        aligned_starting_time=first_frame_starting_time,
        processed_data_file_path=processed_data_file_path,
        fiber_photometry_field=fiber_photometry_fields[0],
        behavior_field=behavior_fields[0],
        index_field=index_fields[0],
        fiber_locations_file_path=fiber_locations_file_path,
        excitation_wavelength_in_nm=excitation_wavelengths_in_nm[0],
        indicator=indicators[0],
        ttl_file_path=ttl_file_path,
        ttl_stream_name=ttl_stream_names[0],
        sampling_frequency=sampling_frequency,
        subject_metadata=subject_metadata,
        excitation_mode="dual-wavelength",
        stub_test=stub_test,
    )
    
    # Add data from the second excitation wavelength and write to NWB file
    # don't include behavior_field because we only need behavior from one channel
    single_wavelength_session_to_nwb(
        raw_imaging_file_path=raw_imaging_file_paths[1],
        frame_indices=second_frame_indices,        
        aligned_starting_time=second_frame_starting_time,
        processed_data_file_path=processed_data_file_path,
        fiber_photometry_field=fiber_photometry_fields[1],
        index_field=index_fields[1],
        fiber_locations_file_path=fiber_locations_file_path,
        excitation_wavelength_in_nm=excitation_wavelengths_in_nm[1],
        indicator=indicators[1],
        ttl_file_path=ttl_file_path,
        ttl_stream_name=ttl_stream_names[1],
        sampling_frequency=sampling_frequency,
        subject_metadata=subject_metadata,
        excitation_mode="dual-wavelength",
        nwbfile=nwbfile, # to add to the first one
        nwbfile_path=nwbfile_path, # write out
        stub_test=stub_test,
    )

if __name__ == "__main__":
    # Parameters for conversion
    subject_folder_path = Path("D:/UG27")
    session_folder_path = subject_folder_path / "240214"
    imaging_file_paths = [
        session_folder_path / "raw" / "data11.cxd",
        session_folder_path / "raw" / "data89.cxd",
    ]
    processed_data_file_path = session_folder_path / "UG27_240214.mat"
    fiber_photometry_fields = ["ACh","DA"]
    behavior_fields = ["behav_ACh","behav_DA"]
    index_fields = ["ACh_idx","DA_idx"]
    ttl_file_path = session_folder_path / "raw" / "UG27_bb1_570_470_norew_2024.02.14_09.34.53.mat"
    ttl_stream_names = ["ttlIn1", "ttlIn2"]
    fiber_locations_file_path = subject_folder_path / "fiber_table.xlsx"
    excitation_wavelengths_in_nm = [470, 570]
    indicators = ["ACh3.0", "rDA3m"]
    sampling_frequency = 18
    nwbfile_path = Path("D:/NWB/UG27_240214.nwb")    
    if not nwbfile_path.parent.exists():
        os.makedirs(nwbfile_path.parent, exist_ok=True)
    stub_test = False

    dual_wavelength_session_to_nwb(
        raw_imaging_file_paths=imaging_file_paths,
        processed_data_file_path=processed_data_file_path,
        fiber_photometry_fields=fiber_photometry_fields,
        ttl_file_path=ttl_file_path,
        ttl_stream_names=ttl_stream_names,
        fiber_locations_file_path=fiber_locations_file_path,
        excitation_wavelengths_in_nm=excitation_wavelengths_in_nm,
        indicators=indicators,
        behavior_fields=behavior_fields,
        index_fields=index_fields,
        nwbfile_path=nwbfile_path,
        sampling_frequency=sampling_frequency,
        stub_test=stub_test,
    )
