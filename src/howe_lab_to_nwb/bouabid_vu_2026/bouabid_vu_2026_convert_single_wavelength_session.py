"""Primary script to run to convert an entire session for of data using the NWBConverter."""
import os
from pathlib import Path
from typing import Union, Optional, List, Literal

from dateutil import tz
from natsort import natsorted
from neuroconv.tools.nwb_helpers import configure_and_write_nwbfile
from neuroconv.utils import load_dict_from_file, dict_deep_update
from pynwb import NWBFile
from pymatreader import read_mat
import numpy as np

from howe_lab_to_nwb.bouabid_vu_2026 import BouabidVu2026NWBConverter
from howe_lab_to_nwb.bouabid_vu_2026.extractors.bioformats_utils import extract_ome_metadata, parse_ome_metadata
from howe_lab_to_nwb.bouabid_vu_2026.utils import get_fiber_locations, update_ophys_metadata, update_fiber_photometry_metadata
 
def single_wavelength_session_to_nwb(
    raw_imaging_file_path: Union[str, Path],
    processed_data_file_path: Union[str,Path],
    fiber_photometry_field: str,    
    index_field: str,
    fiber_locations_file_path: Union[str, Path],
    excitation_wavelength_in_nm: int,
    indicator: str,
    ttl_file_path: Union[str, Path],
    ttl_stream_name: str,
    behavior_field: Optional[str] = None,
    frame_indices: Optional[List[int]] = None,
    nwbfile_path: Optional[Union[str, Path]] = None,
    nwbfile: Optional[NWBFile] = None,
    sampling_frequency: float = -1,
    subject_metadata: Optional[dict] = None,
    aligned_starting_time: Optional[float] = None,
    excitation_mode: Literal["single-wavelength", "dual-wavelength"] = "single-wavelength",
    stub_test: bool = False,
) -> NWBFile:
    """
    Convert a session of data to NWB format.

    Parameters
    ----------
    
    raw_imaging_file_path : Union[str, Path]
        The path to the .cxd file containing the raw imaging data.
    processed_data_file_path: Union[str,Path]
        The path to the processed channel-aligned imaging and behavior data
    fiber_photometry_field: str
        The field in the processed_data_file_path struct corresponding to the fiber photometry data, according to sensor
    behavior_field: str
        The field in the processed_data_file_path struct corresponding to the behavior data, according to sensor
    index_field: str
        The field in the processed_data_file_path struct corresponding to the included imaging indices, according to sensor
    fiber_locations_file_path : Union[str, Path]
        The path to the .xlsx file containing the fiber locations.
    excitation_wavelength_in_nm : int
        The excitation wavelength in nm.
    indicator : str
        The name of the indicator used for the fiber photometry recording.
    ttl_file_path : Union[str, Path]
        The path to the .mat file containing the TTL signals.
    ttl_stream_name : str
        The name of the TTL stream (e.g. 'ttlIn1').    
    nwbfile_path : Union[str, Path], optional
        The path to the NWB file to write. If None, the NWBFile object will be returned.
    nwbfile : NWBFile, optional
        An in-memory NWBFile object to add the data to. If None, a new NWBFile object will be created.   
    nwbfile_path : Union[str, Path]
        The path to the NWB file to be created.
    sampling_frequency : float, optional
        The sampling frequency of the data. If None, the sampling frequency will be read from the .cxd file.
        If missing from the file, the sampling frequency must be provided.    
    subject_metadata : dict, optional
        The metadata for the subject.
    excitation_mode: Literal["single-wavelength", "dual-wavelength"], optional
        The mode of excitation used for the imaging data. By default "single-wavelength".
        Used to correctly update the description of the imaging data.
    stub_test : bool, optional
        Whether to run a stub test, by default False.
    """

    source_data = dict()
    conversion_options = dict()

    # Add raw imaging data
    frame_indices = read_mat(processed_data_file_path,variable_names=index_field)
    frame_indices = list(np.arange(frame_indices[index_field][0]-1,frame_indices[index_field][1]))

    
    imaging_source_data = dict(file_path=str(raw_imaging_file_path), frame_indices=frame_indices)
    if sampling_frequency is not None:
        imaging_source_data.update(sampling_frequency=sampling_frequency)
    source_data.update(dict(Imaging=imaging_source_data))
    conversion_options.update(
        dict(Imaging=dict(stub_test=stub_test, photon_series_type="OnePhotonSeries", photon_series_index=0))
    )

    # Add raw fiber photometry
    source_data.update(
        dict(
            FiberPhotometry=dict(
                file_path=str(processed_data_file_path),
                data_field=fiber_photometry_field,
                ttl_file_path=str(ttl_file_path),
                ttl_stream_name=ttl_stream_name,
            )
        )
    )
    conversion_options.update(dict(FiberPhotometry=dict(stub_test=stub_test)))


    # Add fiber locations
    fiber_locations_metadata = get_fiber_locations(fiber_locations_file_path)
    conversion_options.update(
        dict(FiberPhotometry=dict(stub_test=stub_test, fiber_locations_metadata=fiber_locations_metadata))
    )

    # Add ROI segmentation
    accepted_list = [fiber_ind for fiber_ind, fiber in enumerate(fiber_locations_metadata) if fiber["included"]]
    roi_source_data = dict(
        file_path=str(processed_data_file_path),
        data_field=fiber_photometry_field,
        sampling_frequency=sampling_frequency,
        accepted_list=accepted_list,
    )
    source_data.update(dict(Segmentation=roi_source_data))
    conversion_options.update(dict(Segmentation=dict(stub_test=stub_test)))

    # Add behavior
    if behavior_field is not None:
        source_data.update(dict(Behavior=dict(
            file_path=str(processed_data_file_path),
            data_field=behavior_field)))
        conversion_options.update(dict(Behavior=dict(stub_test=stub_test)))

    # based on data organization
    subject_id = processed_data_file_path.parent.parent.name
    session_id = processed_data_file_path.parent.name



    converter = BouabidVu2026NWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    session_start_time = metadata["NWBFile"]["session_start_time"]
    tzinfo = tz.gettz("US/Eastern")
    metadata["NWBFile"].update(
        session_start_time=session_start_time.replace(tzinfo=tzinfo),
        session_id=session_id,
    )

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "metadata" / "bouabid_vu_2026_general_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    if subject_metadata is not None:
        metadata = dict_deep_update(metadata, subject_metadata)
        date_of_birth = metadata["Subject"]["date_of_birth"]
        metadata["Subject"].update(date_of_birth=date_of_birth.replace(tzinfo=tzinfo))

    ophys_metadata = load_dict_from_file(Path(__file__).parent / "metadata" / "bouabid_vu_2026_ophys_metadata.yaml")
    metadata = dict_deep_update(metadata, ophys_metadata)

    # Load the default metadata for fiber photometry
    fiber_photometry_metadata = load_dict_from_file(
        Path(__file__).parent / "metadata" / "bouabid_vu_2026_fiber_photometry_metadata.yaml"
    )
    # Update metadata with the excitation wavelength and indicator
    excitation_wavelength_to_photon_series_name = {
        470: "Green",
        405: "GreenIsosbestic",
        415: "GreenIsosbestic",
        570: "Red",
    }

    name_suffix = excitation_wavelength_to_photon_series_name[excitation_wavelength_in_nm]
    fiber_photometry_response_series_name = f"FiberPhotometryResponseSeries{name_suffix}"
    updated_fiber_photometry_metadata = update_fiber_photometry_metadata(
        metadata=fiber_photometry_metadata,
        fiber_photometry_response_series_name=fiber_photometry_response_series_name,
        excitation_wavelength_in_nm=excitation_wavelength_in_nm,
        indicator=indicator,
    )
    metadata = dict_deep_update(metadata, updated_fiber_photometry_metadata)

    # Update metadata with the excitation wavelength and indicator
    metadata = update_ophys_metadata(
        metadata=metadata,
        one_photon_series_name=f"OnePhotonSeries{name_suffix}",
        excitation_wavelength_in_nm=excitation_wavelength_in_nm,
        excitation_mode=excitation_mode,
        indicator=indicator,
    )

    if nwbfile is None:
        nwbfile = converter.create_nwbfile(metadata=metadata, conversion_options=conversion_options)
    else:
        converter.add_to_nwbfile(
            nwbfile=nwbfile,
            metadata=metadata,
            conversion_options=conversion_options,
            aligned_starting_time=aligned_starting_time,
        )

    if nwbfile_path is None:
        return nwbfile

    configure_and_write_nwbfile(nwbfile=nwbfile, output_filepath=nwbfile_path)


if __name__ == "__main__":

    # Parameters for conversion
    raw_imaging_file_path = Path("D:/UG27/240214/raw/data11.cxd")
    processed_data_file_path = Path("D:/UG27/240214/UG27_240214.mat")
    fiber_photometry_field = "ACh"    
    ttl_file_path = Path("D:/UG27/240214/raw/UG27_bb1_570_470_norew_2024.02.14_09.34.53.mat")
    ttl_stream_name = "ttlIn1"
    fiber_locations_file_path = Path("D:/UG27/fiber_table.xlsx")
    behavior_field = "behav_ACh"
    index_field = "ACh_idx";

    # The sampling frequency of the raw imaging data must be provided when it cannot be extracted from the .cxd file
    sampling_frequency = 18

    excitation_wavelength_in_nm = 470
    indicator = "ACh3.0"

    nwbfile_path = Path("D:/NWB/UG27_240214.nwb")
    if not nwbfile_path.parent.exists():
        os.makedirs(nwbfile_path.parent, exist_ok=True)
    stub_test = False

    single_wavelength_session_to_nwb(
        raw_imaging_file_path=raw_imaging_file_path,
        processed_data_file_path=processed_data_file_path,
        fiber_photometry_field=fiber_photometry_field,        
        ttl_file_path=ttl_file_path,
        ttl_stream_name=ttl_stream_name,
        fiber_locations_file_path=fiber_locations_file_path,
        excitation_wavelength_in_nm=excitation_wavelength_in_nm,
        indicator=indicator,        
        behavior_field=behavior_field,
        index_field=index_field,
        nwbfile_path=nwbfile_path,
        sampling_frequency=sampling_frequency,
        stub_test=stub_test,
    )
