# Description
![versions](https://img.shields.io/pypi/pyversions/pybadges.svg)
[![DOI](https://zenodo.org/badge/880366201.svg)](https://doi.org/10.5281/zenodo.14012462)

This repository provides the technical validation scripts for the Mondragon Unibertsitatea tool condition monitoring (MU-TCM) face-milling dataset, 
enabling reproducible data processing, synchronisation, and feature extraction for TCM in milling processes.

# Acknowledgements
This work was developed at the [Software and systems engineering](https://www.mondragon.edu/en/research-transfer/engineering-technology/research-and-transfer-groups/software-systems-engineering) and the [High-performance machining](https://www.mondragon.edu/en/research-transfer/engineering-technology/research-and-transfer-groups/high-performance-machining) groups at Mondragon University, as part of the [Digital Manufacturing and Design Training Network](https://dimanditn.eu/es/home).

This project has received funding from the European Union’s Horizon 2020 research and innovation programme under the Marie Skłodowska-Curie grant agreement No 814078.

# Installation
1. Fork the project.
2. Clone the project.
3. Install requirements with PIP
```bash
pip install -r requirements.txt
```
4. Follow the instructions in the [Usage](#usage) section.

# Usage
This code is meant to be used alongside the MU-TCM face-milling dataset. This repository provides three main scripts to process and evaluate the dataset. Below are the instructions for each script:

1. **Signal_sync.py**:
This script handles the synchronisation of internal and external signals, aligning them based on peak analysis to ensure that all data sources are accurately aligned for further analysis. 

```bash
   python Signal_sync.py --input_dir <path_to_raw_data> --output_dir <path_to_synced_data>
```
- `--input_dir`: Path to the directory containing the unsynchronised signal data. Default value is `../signals_unsynced`.
- `--output_dir`: Path to the directory where synchronised data will be saved. Default value is `../signals_synced`. A CSV file (`signals_sync.csv`) with the synchronisation selections is saved also in this directory  upon script completion.

2. **Signal_feature_extraction.py**:
This script performs feature extraction on the synchronised signals, generating time, frequency, and time-frequency-domain features (e.g., RMS, kurtosis, peak-to-peak, wavelet energy) that can be used for TCM.

```bash
python Signal_feature_extraction.py --input_dir <path_to_synced_data>
```
- `--input_dir`: Path to the directory containing synchronised signal data. Default value is `../signals_synced`. A CSV file (`signals_stats.csv`) with the extracted features is saved in this directory upon script completion.

3. **Signal_evaluator.py**:
This script evaluates the extracted features against tool wear annotations, providing insights into which features show strong correlations with tool wear, and is useful for understanding the most relevant metrics for TCM.

```bash
python Signal_evaluator.py --features_path <path_to_features_file>
```
- `--features_path`: Path to the file containing the extracted features. Default value is `../signals_synced/signals_stats.csv`.

# Example Workflow
1. **Step 1**: Synchronise Signals

Run Signal_sync.py to align raw signals from different sources, creating synchronised files ready for feature extraction.

2. **Step 2**: Extract Features

Use Signal_feature_extraction.py to process synchronised signals and extract a range of relevant features.

3. **Step 3**: Evaluate Features

Finally, apply Signal_evaluator.py to analyze the extracted features against tool wear data, identifying metrics most associated with tool wear progression.

This sequence allows users to go from raw data to insights on the most relevant features for TCM in milling processes.

# Contributors

[//]: contributor-faces

<a href="https://github.com/spartanjoax"><img src="https://avatars.githubusercontent.com/u/29443664?v=4" title="José Joaquín Peralta Abadía" width="80" height="80"></a>

[//]: contributor-faces

# Cite

If you use this code in your own work, please use the following bibtex entries:

```bibtex
@software{Peralta_Abadia_MU-TCM_2024,
  author = {Peralta Abadia, Jose Joaquin},
  license = {AGPL-3.0},
  month = oct,
  title={{Technical validation code for the MU-TCM face-milling dataset}}, 
  url = {https://github.com/spartanjoax/MU-TCM},
  version = {1.1},
  year = {2024},
  doi={https://doi.org/10.5281/zenodo.14012462}
}
  
@article{peralta2025tocomon,
  title={{MU-TCM face-milling dataset for smart tool condition monitoring}},
  author={Peralta Abadia, Jose Joaquin and Cuesta Zabaljauregui, Mikel and Larrinaga Barrenechea, Felix},
  journal={...pending...},
  year={2025}
}
```