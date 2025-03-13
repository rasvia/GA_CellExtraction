## GA-assisted Golden-Free Standard Cell Library Extraction<br><sub>Official PyTorch implementation of the ISQED2025 paper</sub>

![Teaser image](./docs/framework_cropped.pdf)

**GA-assisted Golden-free Standard Cell Library Extraction from SEM Images**<br>
Mengdi Zhu, Ronald Wilson, Reiner N. Dizon-Paradis, Olivia P. Dizon-Paradis, Domenic J. Forte, Damon L. Woodard<br>
https://aaig.ece.ufl.edu/projects/ga-assisted-standard-cell-extraction/<br>

Abstract: Reverse Engineering (RE) of Integrated Circuits (ICs) involves studying an IC to comprehend its design, structure, and functionality. This process often entails identifying the key components within the design layout, frequently utilizing scanning electron microscope (SEM) images due to their high resolution, which offers detailed views of the IC's layers. However, current approaches in IC RE generally assume access to a standard cell library for the transition from layout to netlist for functional verification, which is not always available. To overcome this limitation, we propose a golden-free automated pipeline for extracting the standard cell library from SEM layout images. Our method has achieved over 85\% detection rate on the AES and DES design layouts in both 90nm and 32nm technology nodes, compared to the golden reference, by relying solely on information from the contact layer. This finding highlights the potential of our approach to efficiently detect standard cells in complex layouts by focusing on the most relevant and distinctive features of the design.

### Release Notes:
This repository includes the implementation of proposed algorithm in the ISQED2025 paper.

#### Python dependencies 
The required python dependencies can be found at `docs/requirements.txt`

#### Working Folder Structure
- **project_root/** (Main project directory)
  - **`data/`** (Contains the images of design layouts)
    - `layouts/` (The original design layouts)
    - `strip_{design}_{node_tech}/` (The image strips after segmentation)

  - **`encodings/`** (Stores encoding-related files)
    - `{design}_{node_tech}nm/`
      - column_dictionary/ (Dictionary of columns and their encodings)
      - image_encodings/ (Encoding of the design layout)
      - info_capture.pkl (Information coverage w.r.t number of selected columns)
      - unique_columns.npy (Extracted unique columns from layout)
      - column_counts.npy (Counts of unique columns)
  - **`results/`** (Stores final results)
    - `{design}_{node_tech}nm/`
      - final_results.pkl (The extracted potential cells)
  
  - `omp.py`
  - `graph_utils.py`
  - `preprocess.py`
  - `main.py` (Script for running the algorithm)

#### Code Execution
Use the following command to execute: `python main.py`. You can change the arguments in `main.py` for different design and parameters.

