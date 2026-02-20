# Notes concerning the vu2024 conversion

## Dataset notes

Based on the [manuscript](https://doi.org/10.64898/2026.01.20.700614) provided by the lab, this dataset contains fiber
photometry recordings from multi-fiber arrays implanted in the striatum in mice running on a wheel or ball treadmill. In some sessions, mice receive unpredicted rewards, or undergo Pavlovian training or extinction to visual (blue LED) or auditory (12 kHz tone) stimuli, optogenetic midbrain stimulation, or none of the above. Licking was monitored by a capacitive touch circuit connected to the spout.

### From protocol.io

The dataset was collected using the protocols detailed in the [manuscript](https://doi.org/10.64898/2026.01.20.700614)
#### Fiber array imaging

Fiber bundle imaging for head-fixed experiments was performed with a custom microscope.

Imaging data was acquired using HCImage Live (Hamamatsu) and saved as a .CXD (movie) file. For these recordings, dual-wavelength (470 and 570) excitation and emission, two LEDs were triggered by alternating 5V digital TTL pulses which for a sampling rate of 18Hz (20ms exposure) for each channel. To synchronize each LED with the appropriate camera
(e.g. 470nm LED excitation to green emission camera), the LED trigger pulses were sent in parallel(and decreased to 3.3V
via a pulldown circuit) to the cameras to trigger exposure timing. The timing and duration of digital pulses were
controlled by custom MATLAB software through a programmable digital acquisition card (“NIDAQ”, National Instruments PCIe
6343 ). Voltage pulses were sent back from the cameras to the NIDAQ card after exposure of each frame to confirm proper
camera triggering and to align imaging data with behavior data.

#### Behavior data

Behavioral data is collected at 2kHz via a programmable digital acquisition card (NIDAQ, National Instruments PCIe 6343) controlled via custom MATLAB programs.
TTL pulses sent from the imaging cameras enable syncing of behavioral recordings with neural, i.e., imaging, data (see split_and_bin_grid_behav_files.m).
The resulting "binned" behavioral data measures have one datapoint (calculated via averaging, and for binary variables, subsequently rounded) corresponding to one frame of the recorded neural data movie.

### Preprocessing steps

All neural data were preprocessed using the scripts in https://github.com/HoweLab/BouabidVu2026 and https://github.com/HoweLab/MultifiberProcessing

1. Raw neural data are acquired as movies and have filetype .cxd
2. These movies are converted to .tif, and then motion-corrected.
3. Fluorescence is extracted from ROIs corresponding to fiber tops, and delta-F-over-F is calculated.

### Folder structure

The dataset is organized in the following way:

    ExperimentFolder/
    ├── UG27
    │   ├── 240214
    │   │   ├── UG27_240214.mat
    │   │   ├── raw
    |   |   |   ├── data11.cxd
    |   |   |   ├── data89.cxd
    |   |   |   ├── UG27_<notes>_<date>_<time>.mat
    │   └── fiber_table.xlsx
    ├── UG28
    ├── AD1
    ├── AD2
    └── data_table.xlsx

The `ExperimentFolder` contains subfolders for each animal. Each animal folder contains subfolders for each session.

- `UG27_<notes>_<date>_<time>.mat`: contains the raw behavioral data and the TTL pulses from the imaging cameras
- `data11.cxd`: raw imaging data
- `UG27_<date>_<time>.mat`: the raw behavioral data and extracted fluorescence data aligned via TTL pulses from the imaging cameras. Imaging fields are named according to the sensor, and associated behavior fields start with 'behav_' followed by sensor shorthand
- the field `behav_DA`: contains the preprocessed behavioral data downsampled to match the sampling rate of the imaging data for the dopamine (DA) sensor, likewise for other sensors
  The possible relevant fields in the behavior field are:
  * mouse: the name of the file
  * starttime: the timestamp of the beginning of the recording
  * timestamp: the time (s) elapsed since the start of the recording
  * ballSensor1_x: raw voltage reflecting the magnitude of the x-velocity coming from optical mouse sensor placed behind the mouse on the ball treadmill
  * ballSensor1_y: raw voltage reflecting the magnitude of the y-velocity coming from optical mouse sensor placed behind the mouse on the ball treadmill
  * ballSensor1_xsign: the sign (direction) of the x-velocity coming from optical mouse sensor placed behind the mouse on the ball treadmill
  * ballSensor1_ysign: the sign (direction) of the y-velocity coming from optical mouse sensor placed behind the mouse on
  * ballSensor2_x: raw voltage reflecting the magnitude of the x-velocity coming from optical mouse sensor placed to the side of the mouse on the ball treadmill
  * ballSensor2_y: raw voltage reflecting the magnitude of the y-velocity coming from optical mouse sensor placed to the side of the mouse on the ball treadmill
  * ballSensor2_xsign: the sign (direction) of the x-velocity coming from optical mouse sensor placed to the side of the mouse on the ball treadmill
  * ballSensor2_ysign: the sign (direction) of the y-velocity coming from optical mouse sensor placed to the side of the mouse on the ball treadmill
  * ballYaw: conversion to yaw velocity; see ball2xy.m
  * ballPitch: conversion to pitch velocity; see ball2xy.m
  * ballRoll: conversion to roll velocity; see ball2xy.m
  * rotaryEncoderRaw: the raw rotary encoder data from the wheel treadmill
  * rotaryEncoderRotations: the rotary encoder rotations from the wheel treadmill
  * rotaryEncoderDistance: rotary encoder rotations from the wheel treadmill converted to m
  * rotaryEncoderVelocity: velocity on the wheel treadmill in (m/s)
  * stimDriver: signal sent to trigger the optogenetic stimulation laser
  * reward: (binary) reward trigger
  * lick: (binary) lick touch sensor
  * ttlOut: (binary) TTLs sent from the program (user determined)
  * ttlIn1: (binary) TTLs coming in from neural imaging camera #1 (if applicable)
  * ttlIn2: (binary) TTLs coming in from neural imaging camera #2 (if applicable)
 
- the field `DA` contains the fluorescence data extracted from the ROIs for the dopamine (DA) sensor, and likewise for other sensors
   The possible fields are:
   * ROIs: the centers of the ROIs
   * datapath: the path to the associated .tif file
   * snapshot: a snapshot of a frame from the .tif movie
   * radius: the radius of the ROIs
   * ROImasks: an m x n x p matrix of p binary ROI masks
   * FtoFcWindow: the window used to calculate baseline
   * F: the extracted raw fluorescence
   * Fc_baseline_exp: the calculated exponential fit baseline
   * Fc_exp: the calculated ΔF/F from the exponential baseline
   * Fc_exp_hp: the calculated ΔF/F from the exponential baseline, high-pass filtered
   * Fc_exp_hp_art: the calculated ΔF/F from the exponential baseline, high-pass filtered, artifacts removed

- the field `DA_idx` provides the first and last frame of the imaging data included


- `fiber_table.xlsx`: contains the stereotactic coordinates of the fiber tips and the brain area they were implanted in and whether they were included in analysis

## Run conversion for a single session

First install the conversion specific dependencies:

```bash
cd src/howe_lab_to_nwb/bouabid_vu_2026
pip install -r bouabid_vu_2026_requirements.txt
```

### Convert single-wavelength sessions

To convert a single-wavelength session, you can do in Python:

```python
from howe_lab_to_nwb.bouabid_vu_2026.bouabid_vu_2026_convert_single_wavelength_session import  single_wavelength_session_to_nwb
single_wavelength_session_to_nwb(
        raw_imaging_file_path="D:/UG27/240214/raw/data11.cxd",        
        ttl_file_path="D:/UG27/240214/raw/UG27_bb1_570_470_norew_2024.02.14_09.34.53.mat",
        ttl_stream_name="ttlIn1",        
        fiber_locations_file_path="D:/UG27/fiber_table.xlsx",
        excitation_wavelength_in_nm=470,
        indicator="ACh3.0",        
        processed_data_file_path="D:/UG27/240214/UG27_240214.mat",
        fiber_photometry_field="ACh",        
        behavior_field="behav_ACh",
        index_field="ACh_idx",
        nwbfile_path="D:/NWB/sub-UG27/sub-UG27_ses-240214.nwb",
        sampling_frequency=18,
    )

```

#### Conversion parameters

The `single_wavelength_session_to_nwb` functions takes the following parameters:

- `raw_imaging_file_path`: The path to the .cxd file containing the raw imaging data.
- `ttl_file_path`: The path to the .mat file containing the TTL signals.
- `ttl_stream_name`: The name of the TTL stream for the imaging camera (e.g. 'ttlIn1').
- `fiber_locations_file_path`: The path to the .xlsx file containing the fiber locations.
- `excitation_wavelength_in_nm`: The excitation wavelength in nm.
- `indicator`: The name of the indicator used for the fiber photometry recording.

- `processed_data_file_path`: The path to the .mat struct containing fields for each photometry channel, accompanying behavior data, and included indices.
- `fiber_photometry_field`: The field in the processed data struct (`processed_data_file_path`) containing the processed fiber photometry data
- `behavior_field`: The field in the processed data struct (`processed_data_file_path`) containing the processed behavior data
- `index_field`: The field in the processed data struct (`processed_data_file_path`) containing the indices of the first and last frame included
- `sampling_frequency`: The sampling frequency. If omitted, will be automatically filled in.
- `nwbfile_path`: The path to the output NWB file.
- `stub_test`: if True, only a small subset of the data is converted (default: False).


### Convert dual-wavelength sessions

To convert a single dual-wavelength session, you can do in Python:

```python
from howe_lab_to_nwb.bouabid_vu_2026.bouabid_vu_2026_convert_dual_wavelength_session import dual_wavelength_session_to_nwb
dual_wavelength_session_to_nwb(
        raw_imaging_file_paths=["D:/UG27/240214/raw/data11.cxd", "D:/UG27/240214/raw/data89.cxd"],
        ttl_file_path="D:/UG27/240214/rawUG27_bb1_570_470_norew_2024.02.14_09.34.53.mat",
        ttl_stream_names=["ttlIn1", "ttlIn2"],
        fiber_locations_file_path="D:/UG27/fiber_table.xlsx",
        excitation_wavelengths_in_nm=[470, 570],
        indicators=["Ach3.0", "rDA3m"],     
        processed_data_file_path="D:/UG27/240214/UG27_240214.mat",
        fiber_photometry_fields=["ACh", "DA"],
        behavior_fields=["behav_ACh","behav_DA"],
        index_fields=["ACh_idx","DA_idx"],
        nwbfile_path="D:/NWB/sub-UG27/sub-UG27_ses-240214.nwb",
        sampling_frequency=18,
    )
```

To convert all dual-wavelength sessions, you can do in Python:
```python
from howe_lab_to_nwb.bouabid_vu_2026.bouabid_vu_2026_convert_all_dual_wavelength_sessions import convert_all_dual_wavelength_sessions
convert_all_dual_wavelength_sessions(
        data_table_path="D:/data_table.xlsx",
        folder_path="D:",
        nwbfile_folder_path="D:/NWB",
        subject_ids=["UG27", "AD1","ADS6"],
        stub_test=False,
        overwrite=False,
    )
```

#### Conversion parameters

The `convert_all_dual_wavelength_sessions` function takes the following parameters:

- `data_table_path`: The path to the XLSX file containing info for all the sessions. (required)
- `folder_path`: The root folder path to search for the filenames in the data table. (required)
- `nwbfile_folder_path`: The folder path to save the NWB files. (required)
- `subject_ids`: The list of subject IDs to convert. (required)
- `stub_test`: if True, only a small subset of the data is converted (default: False).
- `overwrite`: if True, overwrite existing NWB files (default: False).
