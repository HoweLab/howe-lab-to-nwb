from pathlib import Path
from typing import Union
from warnings import warn

import pandas as pd
from nwbinspector import inspect_nwbfile, format_messages, save_report
from tqdm import tqdm

from howe_lab_to_nwb.bouabid_vu_2026.bouabid_vu_2026_convert_dual_wavelength_session import dual_wavelength_session_to_nwb


def convert_all_dual_wavelength_sessions(
    data_table_path: Union[str, Path],
    folder_path: Union[str, Path],
    nwbfile_folder_path: Union[str, Path],
    subject_ids: list,
    stub_test: bool = False,
    overwrite: bool = False,
):
    """
    Convert all dual-wavelength excitation sessions from the Vu 2024 dataset to NWB format.

    Parameters
    ----------
    data_table_path : str or Path
        The path to the XLSX file containing info for all the sessions.
    folder_path : str or Path
        The root folder path to search for the filenames in the data table.
    nwbfile_folder_path : str or Path
        The folder path to save the NWB files.
    subject_ids : list
        The list of subjects to convert.
    stub_test : bool, optional
        Whether to run the conversion as a stub test.
        When set to True, write only a subset of the data for each session.
        When set to False, write the entire data for each session.
    overwrite : bool, optional
        Whether to overwrite existing NWB files, default is False.

    """
    from howe_lab_to_nwb.bouabid_vu_2026.utils._data_utils import (
        _get_subject_metadata_from_dataframe,
        _get_ttl_stream_name_from_file_path,
        _get_indicator_from_aav_string,
    )

    data_table_dict = pd.read_excel(data_table_path, sheet_name=["Sessions", "Mice"])
    data_table = data_table_dict["Sessions"]

    filtered_data_table = data_table[data_table["Mouse"].astype(str).isin(subject_ids)]
    if filtered_data_table.empty:
        raise ValueError(f"No sessions found for the provided subject IDs: {subject_ids}.")

    subjects_table = data_table_dict["Mice"].astype(str)

    folder_path = Path(folder_path)

    columns_to_group = ["Mouse", "Experiment Directory"]
    total_file_paths = filtered_data_table.groupby(columns_to_group).count().shape[0]
    progress_bar = tqdm(
        filtered_data_table.groupby(columns_to_group),
        desc=f"Converting {total_file_paths} sessions to NWB ...",
        position=0,
        total=total_file_paths,
        dynamic_ncols=True,
    )

    for (subject_id, exp_dir), table in progress_bar:
        subject_metadata = _get_subject_metadata_from_dataframe(subject_id=subject_id, data_table=subjects_table)
        
        subject_id = str(subject_id).replace("-", "")
        subject_folder_path = folder_path / subject_id
        session_folder_path = subject_folder_path / exp_dir        
        
        raw_imaging_file_paths=[session_folder_path /  "raw" / table["Raw Imaging File: green"].values[0], session_folder_path /  "raw" / table["Raw Imaging File: red"].values[0]]
        processed_data_file_path = session_folder_path / table["Processed Data File"].values[0]
        fiber_photometry_fields = [table["Processed Photometry Field: green"].values[0],table["Processed Photometry Field: red"].values[0]]
        behavior_fields = [table["Processed Behavior Field: green"].values[0],table["Processed Behavior Field: red"].values[0]]
        index_fields = [table["Processed Index Field: green"].values[0],table["Processed Index Field: red"].values[0]]
        fiber_locations_file_path = subject_folder_path / "fiber_table.xlsx"
        excitation_wavelengths_in_nm = [table["LED Excitation Wavelength (nm): green"].values[0],table["LED Excitation Wavelength (nm): red"].values[0]]
        indicators = [_get_indicator_from_aav_string(table["Relevant Injected Sensor: green"].values[0]),_get_indicator_from_aav_string(table["Relevant Injected Sensor: red"].values[0])]
        ttl_file_path = session_folder_path / "raw" / table["Raw Behavior File"].values[0]
        ttl_stream_names = ["ttlIn1","ttlIn2"]
        nwbfile_path = nwbfile_folder_path / f"{subject_id}_{exp_dir}.nwb"
        if stub_test:
            nwbfile_path = nwbfile_folder_path / f"stub-{subject_id}_{exp_dir}.nwb"
        if nwbfile_path.exists() and not overwrite:
            progress_bar.update(1)
            continue

        progress_bar.set_description(f"Converting subject '{subject_id}' session '{exp_dir}' session to NWB ...")

        dual_wavelength_session_to_nwb(
            raw_imaging_file_paths=raw_imaging_file_paths,
            processed_data_file_path=processed_data_file_path,
            fiber_photometry_fields=fiber_photometry_fields,
            behavior_fields=behavior_fields,
            index_fields=index_fields,
            fiber_locations_file_path=fiber_locations_file_path,
            excitation_wavelengths_in_nm=excitation_wavelengths_in_nm,
            indicators=indicators,
            ttl_file_path=ttl_file_path,
            ttl_stream_names=ttl_stream_names,
            nwbfile_path=nwbfile_path,
            sampling_frequency=18,
            subject_metadata=subject_metadata,            
        )

        results = list(inspect_nwbfile(nwbfile_path=nwbfile_path))
        report_path = nwbfile_folder_path / f"{subject_id}-{exp_dir}_nwbinspector_result.txt"
        if not report_path.exists():
            save_report(
                report_file_path=report_path,
                formatted_messages=format_messages(
                    results,
                    levels=["importance", "file_path"],
                ),
            )

        progress_bar.update(1)


if __name__ == "__main__":
    # Parameters for conversion

    # The path to the XLSX file containing info for all the sessions
    data_table_excel_file_path = Path("D:/data_table.xlsx")

    # The list of subjects to convert
    subject_ids = ["UG27"]

    # The root folder path to search for the filenames in the data table
    folder_path = Path("D:")

    # The folder path to save the NWB files
    nwbfile_folder_path = Path("D:/NWB")
    if not nwbfile_folder_path.exists():
        nwbfile_folder_path.mkdir(exist_ok=True)

    # Whether to overwrite existing NWB files, default is False
    overwrite = True

    # Whether to run the conversion as a stub test
    # When set to True, write only a subset of the data for each session
    # When set to False, write the entire data for each session
    stub_test = False

    convert_all_dual_wavelength_sessions(
        data_table_path=data_table_excel_file_path,
        folder_path=folder_path,
        nwbfile_folder_path=nwbfile_folder_path,
        subject_ids=subject_ids,
        stub_test=stub_test,
        overwrite=overwrite,
    )
