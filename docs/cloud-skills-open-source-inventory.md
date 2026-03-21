# Cloud Brain: Open-Source Scientific Tool Inventory

> Compiled 2026-03-20. All GitHub star counts and URLs verified via `gh api`.
> Criteria: actively maintained (pushed 2025-2026), >500 stars (exceptions noted), working APIs/SDKs.

---

## Integration Type Legend

| Symbol | Meaning | Integration Path |
|--------|---------|-----------------|
| REST | REST/HTTP API | MCP server wrapper |
| SDK | Python SDK/library | AgentTool wrapper, direct `import` |
| CLI | Command-line tool | `subprocess` / container exec |
| LIB | C++/Java library with Python bindings | Install + SDK wrapper |

---

## 1. Protein Structure & Design

| Name | GitHub | Stars | Install | API Type | Integration Complexity | Notes |
|------|--------|-------|---------|----------|----------------------|-------|
| **AlphaFold 2** | [google-deepmind/alphafold](https://github.com/google-deepmind/alphafold) | 14,384 | `pip install alphafold` | SDK, CLI | HIGH - requires large DBs (~2.5TB), GPU | Gold standard for protein structure prediction |
| **AlphaFold 3** | [google-deepmind/alphafold3](https://github.com/google-deepmind/alphafold3) | 7,755 | source install | SDK, CLI | HIGH - complex deps, GPU | Biomolecular complex prediction (protein+DNA+RNA+ligand) |
| **Boltz** | [jwohlwend/boltz](https://github.com/jwohlwend/boltz) | 3,850 | `pip install boltz` | SDK, CLI | MEDIUM - GPU | Open-source biomolecular structure prediction, AlphaFold3 competitor |
| **OpenFold** | [aqlaboratory/openfold](https://github.com/aqlaboratory/openfold) | 3,307 | `pip install openfold` | SDK | HIGH - GPU, large DBs | Trainable PyTorch reproduction of AlphaFold 2 |
| **OpenFold 3** | [aqlaboratory/openfold-3](https://github.com/aqlaboratory/openfold-3) | 641 | source install | SDK | HIGH - GPU | Fully open-source AlphaFold3 reproduction |
| **RFdiffusion** | [RosettaCommons/RFdiffusion](https://github.com/RosettaCommons/RFdiffusion) | 2,788 | source install | SDK, CLI | HIGH - GPU | Protein design via diffusion; de novo backbone generation |
| **ColabFold** | [sokrypton/ColabFold](https://github.com/sokrypton/ColabFold) | 2,675 | `pip install colabfold` | SDK, CLI | MEDIUM - uses MMseqs2 server | Fast AlphaFold2 via MMseqs2; Colab-friendly |
| **ESM (Meta, archived)** | [facebookresearch/esm](https://github.com/facebookresearch/esm) | 4,008 | `pip install fair-esm` | SDK | MEDIUM - GPU for large models | ESM-2, ESMFold protein language models. Archived Feb 2024 |
| **ESM3 (EvolutionaryScale)** | [evolutionaryscale/esm](https://github.com/evolutionaryscale/esm) | 2,278 | `pip install esm` | SDK, REST | MEDIUM - API available | Next-gen protein language model; also has hosted API |
| **Chai-1** | [chaidiscovery/chai-lab](https://github.com/chaidiscovery/chai-lab) | 1,906 | `pip install chai-lab` | SDK | MEDIUM - GPU | SOTA biomolecular structure prediction |
| **ProteinMPNN** | [dauparas/ProteinMPNN](https://github.com/dauparas/ProteinMPNN) | 1,665 | source install | SDK | MEDIUM - GPU | Inverse folding: design sequences for given structures |
| **ProtTrans** | [agemagician/ProtTrans](https://github.com/agemagician/ProtTrans) | 1,293 | `pip install bio-embeddings` | SDK | MEDIUM - GPU | Pretrained protein language models (BERT, Albert, XLNet, etc.) |
| **OpenCRISPR** | [Profluent-AI/OpenCRISPR](https://github.com/Profluent-AI/OpenCRISPR) | 1,180 | source install | SDK | MEDIUM | AI-generated gene editing systems |
| **Uni-Mol** | [deepmodeling/Uni-Mol](https://github.com/deepmodeling/Uni-Mol) | 1,080 | `pip install unimol_tools` | SDK | MEDIUM - GPU | Universal molecular representation learning |
| **MACE** | [ACEsuit/mace](https://github.com/ACEsuit/mace) | 1,112 | `pip install mace-torch` | SDK | MEDIUM - GPU | Fast equivariant ML interatomic potentials |
| **Biotite** | [biotite-dev/biotite](https://github.com/biotite-dev/biotite) | 934 | `pip install biotite` | SDK | LOW | Comprehensive molecular biology library |
| **AlphaFlow** | [bjing2016/alphaflow](https://github.com/bjing2016/alphaflow) | 518 | source install | SDK | MEDIUM - GPU | Protein ensemble generation via flow matching |

### Priority for Cloud Brain Integration

**Tier 1 (must-have):** AlphaFold 2/3, Boltz, ESM3, ColabFold, RFdiffusion
**Tier 2 (high value):** ProteinMPNN, Chai-1, OpenFold, MACE
**Tier 3 (specialized):** OpenCRISPR, ProtTrans, Uni-Mol, AlphaFlow

---

## 2. Genomics & Single-Cell

| Name | GitHub | Stars | Install | API Type | Integration Complexity | Notes |
|------|--------|-------|---------|----------|----------------------|-------|
| **Nextflow** | [nextflow-io/nextflow](https://github.com/nextflow-io/nextflow) | 3,331 | `curl -s get.nextflow.io \| bash` | CLI | MEDIUM - JVM | Data-driven computational pipelines; nf-core ecosystem |
| **Snakemake** | [snakemake/snakemake](https://github.com/snakemake/snakemake) | 2,732 | `pip install snakemake` | SDK, CLI | LOW | Python-native workflow management |
| **Scanpy** | [scverse/scanpy](https://github.com/scverse/scanpy) | 2,380 | `pip install scanpy` | SDK | LOW | Single-cell analysis in Python; scales >100M cells |
| **STAR** | [alexdobin/STAR](https://github.com/alexdobin/STAR) | 2,162 | `conda install star` | CLI | MEDIUM - needs genome index | Spliced transcript aligner for RNA-seq |
| **minimap2** | [lh3/minimap2](https://github.com/lh3/minimap2) | 2,144 | `conda install minimap2` | CLI, LIB | LOW | Versatile pairwise aligner for genomic sequences |
| **GATK** | [broadinstitute/gatk](https://github.com/broadinstitute/gatk) | 1,919 | `conda install gatk4` | CLI | MEDIUM - JVM | Gold standard variant calling toolkit |
| **Bioconda** | [bioconda/bioconda-recipes](https://github.com/bioconda/bioconda-recipes) | 1,793 | `conda config --add channels bioconda` | CLI | LOW | 10,000+ bioinformatics packages; install anything |
| **scvi-tools** | [scverse/scvi-tools](https://github.com/scverse/scvi-tools) | 1,585 | `pip install scvi-tools` | SDK | MEDIUM - GPU optional | Deep probabilistic analysis of single-cell/spatial omics |
| **nf-core/rnaseq** | [nf-core/rnaseq](https://github.com/nf-core/rnaseq) | 1,234 | `nextflow run nf-core/rnaseq` | CLI | MEDIUM | Production RNA-seq pipeline (STAR+Salmon+QC) |
| **scikit-bio** | [scikit-bio/scikit-bio](https://github.com/scikit-bio/scikit-bio) | 1,183 | `pip install scikit-bio` | SDK | LOW | Community bioinformatics library |
| **Picard** | [broadinstitute/picard](https://github.com/broadinstitute/picard) | 1,054 | `conda install picard` | CLI | LOW - JVM | HTS data manipulation (BAM/SAM/CRAM/VCF) |
| **Salmon** | [COMBINE-lab/salmon](https://github.com/COMBINE-lab/salmon) | 872 | `conda install salmon` | CLI | LOW | Ultra-fast transcript quantification from RNA-seq |
| **Nucleotide Transformer** | [instadeepai/nucleotide-transformer](https://github.com/instadeepai/nucleotide-transformer) | 845 | `pip install nucleotide-transformer` | SDK | MEDIUM - GPU | Foundation models for genomics & transcriptomics |
| **Dorado** | [nanoporetech/dorado](https://github.com/nanoporetech/dorado) | 806 | prebuilt binary | CLI | MEDIUM - GPU | Oxford Nanopore basecaller |
| **HyenaDNA** | [HazyResearch/hyena-dna](https://github.com/HazyResearch/hyena-dna) | 769 | source install | SDK | MEDIUM - GPU | Long-range genomic foundation model |
| **kallisto** | [pachterlab/kallisto](https://github.com/pachterlab/kallisto) | 753 | `conda install kallisto` | CLI | LOW | Near-optimal RNA-seq quantification |
| **SpikeInterface** | [SpikeInterface/spikeinterface](https://github.com/SpikeInterface/spikeinterface) | 752 | `pip install spikeinterface` | SDK | LOW | Unified spike sorting interface |
| **AnnData** | [scverse/anndata](https://github.com/scverse/anndata) | 722 | `pip install anndata` | SDK | LOW | Annotated data matrices; core data format for scRNA-seq |
| **DNABERT** | [jerryji1993/DNABERT](https://github.com/jerryji1993/DNABERT) | 748 | source install | SDK | MEDIUM - GPU | Pre-trained BERT for DNA sequences |
| **CaImAn** | [flatironinstitute/CaImAn](https://github.com/flatironinstitute/CaImAn) | 720 | `pip install caiman` | SDK | MEDIUM | Calcium imaging analysis (motion correction, source extraction) |
| **SLEAP** | [talmolab/sleap](https://github.com/talmolab/sleap) | 570 | `pip install sleap` | SDK, CLI | MEDIUM - GPU | Multi-animal pose tracking |
| **Squidpy** | [scverse/squidpy](https://github.com/scverse/squidpy) | 555 | `pip install squidpy` | SDK | LOW | Spatial single-cell analysis |
| **nf-core/sarek** | [nf-core/sarek](https://github.com/nf-core/sarek) | 555 | `nextflow run nf-core/sarek` | CLI | MEDIUM | Variant calling pipeline (WGS/WES) |
| **NCBI Datasets** | [ncbi/datasets](https://github.com/ncbi/datasets) | 519 | `conda install ncbi-datasets-cli` | CLI, REST | LOW | Official NCBI data access tool |
| **10x CellRanger** | [10XGenomics/cellranger](https://github.com/10XGenomics/cellranger) | 453 | proprietary installer | CLI | HIGH - commercial | 10x single-cell analysis (open-source since 2024) |

### Priority for Cloud Brain Integration

**Tier 1 (must-have):** Scanpy, scvi-tools, AnnData, Nextflow, Snakemake, STAR, Salmon
**Tier 2 (high value):** nf-core pipelines, GATK, Nucleotide Transformer, SpikeInterface, CaImAn
**Tier 3 (specialized):** HyenaDNA, DNABERT, SLEAP, Squidpy, Dorado

---

## 3. Drug Discovery & Cheminformatics

| Name | GitHub | Stars | Install | API Type | Integration Complexity | Notes |
|------|--------|-------|---------|----------|----------------------|-------|
| **DeepChem** | [deepchem/deepchem](https://github.com/deepchem/deepchem) | 6,618 | `pip install deepchem` | SDK | LOW | Comprehensive deep learning for drug discovery |
| **RDKit** | [rdkit/rdkit](https://github.com/rdkit/rdkit) | 3,346 | `pip install rdkit` | SDK, LIB | LOW | Industry-standard cheminformatics toolkit |
| **Chemprop** | [chemprop/chemprop](https://github.com/chemprop/chemprop) | 2,298 | `pip install chemprop` | SDK, CLI | LOW | Message passing neural networks for molecular property prediction |
| **FAIR-Chem (OCP)** | [facebookresearch/fairchem](https://github.com/facebookresearch/fairchem) | 2,011 | `pip install fairchem` | SDK | MEDIUM - GPU | ML methods for catalysis and chemistry |
| **OpenMM** | [openmm/openmm](https://github.com/openmm/openmm) | 1,818 | `conda install openmm` | SDK | MEDIUM | GPU-accelerated molecular simulation toolkit |
| **DiffDock** | [gcorso/DiffDock](https://github.com/gcorso/DiffDock) | 1,462 | source install | SDK | MEDIUM - GPU | Diffusion-based molecular docking |
| **Open Babel** | [openbabel/openbabel](https://github.com/openbabel/openbabel) | 1,292 | `conda install openbabel` | SDK, CLI, LIB | LOW | Chemical format converter; speaks 100+ file formats |
| **TDC** | [mims-harvard/TDC](https://github.com/mims-harvard/TDC) | 1,218 | `pip install PyTDC` | SDK | LOW | Therapeutics data commons; 66 benchmarks |
| **Psi4** | [psi4/psi4](https://github.com/psi4/psi4) | 1,152 | `conda install psi4` | SDK | HIGH - compute intensive | Open-source quantum chemistry |
| **Uni-Mol** | [deepmodeling/Uni-Mol](https://github.com/deepmodeling/Uni-Mol) | 1,080 | `pip install unimol_tools` | SDK | MEDIUM - GPU | Universal molecular representation learning |
| **AutoDock Vina** | [ccsb-scripps/AutoDock-Vina](https://github.com/ccsb-scripps/AutoDock-Vina) | 946 | `pip install vina` | SDK, CLI | LOW | Classic molecular docking engine |
| **SchNetPack** | [atomistic-machine-learning/schnetpack](https://github.com/atomistic-machine-learning/schnetpack) | 912 | `pip install schnetpack` | SDK | MEDIUM - GPU | Deep neural networks for atomistic systems |
| **gnina** | [gnina/gnina](https://github.com/gnina/gnina) | 876 | `conda install gnina` | CLI | MEDIUM - GPU | Deep learning framework for molecular docking |
| **AiZynthFinder** | [MolecularAI/aizynthfinder](https://github.com/MolecularAI/aizynthfinder) | 803 | `pip install aizynthfinder` | SDK | MEDIUM | Retrosynthetic planning tool |
| **MDTraj** | [mdtraj/mdtraj](https://github.com/mdtraj/mdtraj) | 706 | `pip install mdtraj` | SDK | LOW | Molecular dynamics trajectory analysis |
| **NVIDIA BioNeMo** | [NVIDIA/bionemo-framework](https://github.com/NVIDIA/bionemo-framework) | 695 | `pip install bionemo` | SDK | HIGH - GPU (multi-GPU) | Building/adapting AI models for drug discovery at scale |
| **Matminer** | [hackingmaterials/matminer](https://github.com/hackingmaterials/matminer) | 576 | `pip install matminer` | SDK | LOW | Data mining for materials science |
| **Datamol** | [datamol-io/datamol](https://github.com/datamol-io/datamol) | 532 | `pip install datamol` | SDK | LOW | Simplified molecular processing on top of RDKit |
| **MatGL** | [materialyzeai/matgl](https://github.com/materialyzeai/matgl) | 523 | `pip install matgl` | SDK | MEDIUM - GPU | Graph deep learning for materials |
| **Bio Embeddings** | [sacdallago/bio_embeddings](https://github.com/sacdallago/bio_embeddings) | 507 | `pip install bio-embeddings` | SDK | MEDIUM - GPU | Protein embeddings from sequences |

### External APIs (no GitHub repo, REST-based)

| Name | Endpoint | API Type | Auth | Integration Complexity | Notes |
|------|----------|----------|------|----------------------|-------|
| **ChEMBL** | `https://www.ebi.ac.uk/chembl/api/data/` | REST, SDK | None (free) | LOW | Python client: `chembl_webresource_client` (436 stars). 2.4M compounds |
| **DrugBank** | `https://go.drugbank.com/releases/latest` | REST | API key (commercial) | MEDIUM | 16,000+ drug entries; free academic tier |
| **PubChem** | `https://pubchem.ncbi.nlm.nih.gov/rest/pug/` | REST | None (free) | LOW | 116M+ compounds; PUG REST API |
| **UniProt** | `https://rest.uniprot.org/` | REST | None (free) | LOW | 250M+ protein sequences; new REST API (2022+) |
| **RCSB PDB** | `https://data.rcsb.org/rest/v1/` | REST, SDK | None (free) | LOW | 220K+ structures; Python client `rcsb-api` |

### Priority for Cloud Brain Integration

**Tier 1 (must-have):** RDKit, DeepChem, ChEMBL API, PubChem API, UniProt API, OpenMM
**Tier 2 (high value):** DiffDock, Chemprop, AutoDock Vina, TDC, FAIR-Chem
**Tier 3 (specialized):** BioNeMo, AiZynthFinder, Psi4, gnina

---

## 4. Literature & Knowledge APIs

| Name | Endpoint / GitHub | Stars | Install | API Type | Auth | Integration Complexity |
|------|-------------------|-------|---------|----------|------|----------------------|
| **Semantic Scholar** | `https://api.semanticscholar.org/` | N/A (service) | `pip install semanticscholar` | REST | API key (free) | LOW |
| S2 Python Client | [danielnsilva/semanticscholar](https://github.com/danielnsilva/semanticscholar) | 436 | `pip install semanticscholar` | SDK | -- | LOW |
| **PubMed E-utilities** | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` | N/A (service) | `pip install biopython` | REST | API key (free) | LOW |
| **OpenAlex** | `https://api.openalex.org/` | N/A (service) | `pip install pyalex` | REST | Polite pool (email) | LOW |
| PyAlex Client | [J535D165/pyalex](https://github.com/J535D165/pyalex) | 359 | `pip install pyalex` | SDK | -- | LOW |
| **Biopython** | [biopython/biopython](https://github.com/biopython/biopython) | 4,929 | `pip install biopython` | SDK | -- | LOW |
| **SciSpaCy** | [allenai/scispacy](https://github.com/allenai/scispacy) | 1,934 | `pip install scispacy` | SDK | -- | LOW |
| **spaCy** | [explosion/spaCy](https://github.com/explosion/spaCy) | 33,356 | `pip install spacy` | SDK | -- | LOW |
| **PaperMage** | [allenai/papermage](https://github.com/allenai/papermage) | 791 | `pip install papermage` | SDK | -- | LOW |
| **S2ORC** | [allenai/s2orc](https://github.com/allenai/s2orc) | 1,022 | download dataset | SDK | -- | MEDIUM |
| **BioGPT** | [microsoft/BioGPT](https://github.com/microsoft/BioGPT) | 4,490 | source install | SDK | -- | MEDIUM - GPU |
| **BioBERT** | [dmis-lab/biobert](https://github.com/dmis-lab/biobert) | 2,192 | HuggingFace model | SDK | -- | MEDIUM - GPU |

### API Rate Limits Summary

| API | Free Tier | Authenticated |
|-----|-----------|---------------|
| Semantic Scholar | Shared pool | 1 RPS (default key), up to 100 RPS |
| PubMed E-utilities | 3 req/sec | 10 req/sec with API key |
| OpenAlex | 100 req/sec (polite pool with email) | Same |
| ChEMBL | Unlimited (reasonable use) | N/A |
| PubChem | 5 req/sec | Same |
| UniProt | Reasonable use | N/A |

### Priority for Cloud Brain Integration

**Tier 1 (must-have):** Semantic Scholar API, PubMed E-utilities, OpenAlex, Biopython
**Tier 2 (high value):** SciSpaCy, PaperMage, BioGPT
**Tier 3 (specialized):** BioBERT, S2ORC

---

## 5. Lab Automation & Instruments

| Name | GitHub | Stars | Install | API Type | Integration Complexity | Notes |
|------|--------|-------|---------|----------|----------------------|-------|
| **Pint** | [hgrecco/pint](https://github.com/hgrecco/pint) | 2,709 | `pip install pint` | SDK | LOW | Physical quantities with units; essential for lab calculations |
| **Opentrons** | [Opentrons/opentrons](https://github.com/Opentrons/opentrons) | 495 | `pip install opentrons` | SDK, REST | MEDIUM | OT-2 and Flex liquid handling robots |
| **PyLabRobot** | [PyLabRobot/pylabrobot](https://github.com/PyLabRobot/pylabrobot) | 409 | `pip install pylabrobot` | SDK | MEDIUM | Hardware-agnostic lab automation SDK |
| **SciTools Iris** | [SciTools/iris](https://github.com/SciTools/iris) | 711 | `pip install scitools-iris` | SDK | LOW | Earth science data analysis |

### External APIs

| Name | Endpoint | API Type | Auth | Integration Complexity | Notes |
|------|----------|----------|------|----------------------|-------|
| **Protocols.io** | `https://www.protocols.io/api/v4/` | REST | OAuth2 (free) | LOW | Protocol sharing platform; 100K+ protocols |
| **Benchling** | `https://benchling.com/api/v2/` | REST | API key (commercial) | MEDIUM | Lab notebook and molecular biology platform |
| **Addgene** | `https://www.addgene.org/search/advanced/` | REST (limited) | None | LOW | Plasmid repository; 100K+ plasmids |

### Priority for Cloud Brain Integration

**Tier 1 (must-have):** Pint, Protocols.io API, PyLabRobot
**Tier 2 (high value):** Opentrons SDK
**Tier 3 (specialized):** Benchling API (if budget allows)

---

## 6. Bioimage Analysis

| Name | GitHub | Stars | Install | API Type | Integration Complexity | Notes |
|------|--------|-------|---------|----------|----------------------|-------|
| **MONAI** | [Project-MONAI/MONAI](https://github.com/Project-MONAI/MONAI) | 7,954 | `pip install monai` | SDK | MEDIUM - GPU | NVIDIA's AI toolkit for healthcare imaging |
| **DeepLabCut** | [DeepLabCut/DeepLabCut](https://github.com/DeepLabCut/DeepLabCut) | 5,555 | `pip install deeplabcut` | SDK, CLI | MEDIUM - GPU | Markerless pose estimation for all animals |
| **napari** | [napari/napari](https://github.com/napari/napari) | 2,613 | `pip install napari` | SDK | LOW | Multi-dimensional image viewer; rich plugin ecosystem |
| **Cellpose** | [MouseLand/cellpose](https://github.com/MouseLand/cellpose) | 2,119 | `pip install cellpose` | SDK, CLI | LOW (CPU or GPU) | Generalist cell segmentation with human-in-the-loop |
| **Zarr** | [zarr-developers/zarr-python](https://github.com/zarr-developers/zarr-python) | 1,943 | `pip install zarr` | SDK | LOW | Chunked, compressed N-dimensional arrays; cloud-native |
| **QuPath** | [qupath/qupath](https://github.com/qupath/qupath) | 1,315 | standalone installer | CLI (scripting), LIB | MEDIUM - Java/Groovy | Open-source bioimage analysis for pathology |
| **StarDist** | [stardist/stardist](https://github.com/stardist/stardist) | 1,188 | `pip install stardist` | SDK | LOW (CPU or GPU) | Star-convex object detection; excellent for nuclei |
| **CellProfiler** | [CellProfiler/CellProfiler](https://github.com/CellProfiler/CellProfiler) | 1,095 | `pip install cellprofiler` | SDK, CLI | MEDIUM | Biological image analysis pipelines |
| **MOABB** | [NeuroTechX/moabb](https://github.com/NeuroTechX/moabb) | 951 | `pip install moabb` | SDK | LOW | BCI benchmarking for neuroscience EEG |
| **Fiji/ImageJ** | [fiji/fiji](https://github.com/fiji/fiji) | 940 | standalone installer | CLI (macro), LIB | MEDIUM - Java | "Batteries-included" ImageJ distribution |
| **SLEAP** | [talmolab/sleap](https://github.com/talmolab/sleap) | 570 | `pip install sleap` | SDK, CLI | MEDIUM - GPU | Multi-animal pose tracking |
| **Suite2p** | [MouseLand/suite2p](https://github.com/MouseLand/suite2p) | 439 | `pip install suite2p` | SDK | MEDIUM - GPU optional | Two-photon calcium imaging pipeline |

### Priority for Cloud Brain Integration

**Tier 1 (must-have):** Cellpose, DeepLabCut, napari, Zarr, StarDist
**Tier 2 (high value):** MONAI, CellProfiler, Suite2p, CaImAn
**Tier 3 (specialized):** QuPath, SLEAP, MOABB, Fiji

---

## 7. Clinical & Health Data

| Name | GitHub / Endpoint | Stars | Install | API Type | Auth | Integration Complexity |
|------|-------------------|-------|---------|----------|------|----------------------|
| **OMOP CDM** | [OHDSI/CommonDataModel](https://github.com/OHDSI/CommonDataModel) | 1,027 | SQL DDLs | SDK (R/Python) | -- | HIGH - DB setup |
| **FHIR (SMART)** | [smart-on-fhir/client-py](https://github.com/smart-on-fhir/client-py) | 678 | `pip install fhirclient` | SDK, REST | OAuth2 | MEDIUM |
| **ClinicalTrials.gov** | `https://clinicaltrials.gov/data-api/api` | N/A | REST calls | REST (v2) | None (free) | LOW |
| **NCBI Datasets** | [ncbi/datasets](https://github.com/ncbi/datasets) | 519 | `conda install ncbi-datasets-cli` | CLI, REST | API key (free) | LOW |
| **FDA openFDA** | `https://api.fda.gov/` | N/A | REST calls | REST | API key (free) | LOW |

### Priority for Cloud Brain Integration

**Tier 1 (must-have):** ClinicalTrials.gov API, FHIR client, FDA openFDA
**Tier 2 (high value):** OMOP CDM (for data standardization)
**Tier 3 (specialized):** NCBI Datasets

---

## 8. ML for Science

| Name | GitHub | Stars | Install | API Type | Integration Complexity | Notes |
|------|--------|-------|---------|----------|----------------------|-------|
| **PyTorch Geometric** | [pyg-team/pytorch_geometric](https://github.com/pyg-team/pytorch_geometric) | 23,587 | `pip install torch-geometric` | SDK | MEDIUM - GPU | GNN library; essential for molecular/protein graphs |
| **DGL** | [dmlc/dgl](https://github.com/dmlc/dgl) | 14,247 | `pip install dgl` | SDK | MEDIUM - GPU | Deep learning on graphs; alternative to PyG |
| **GraphCast** | [google-deepmind/graphcast](https://github.com/google-deepmind/graphcast) | 6,558 | source install | SDK | HIGH - TPU/GPU | Weather forecasting via GNNs |
| **Graphormer** | [microsoft/Graphormer](https://github.com/microsoft/Graphormer) | 2,429 | `pip install graphormer` | SDK | MEDIUM - GPU | General-purpose graph transformer for molecular modeling |
| **PyMatGen** | [materialsproject/pymatgen](https://github.com/materialsproject/pymatgen) | 1,834 | `pip install pymatgen` | SDK | LOW | Python materials genomics; powers Materials Project |
| **PyBaMM** | [pybamm-team/PyBaMM](https://github.com/pybamm-team/PyBaMM) | 1,516 | `pip install pybamm` | SDK | MEDIUM | Physics-based battery models |
| **JAX-MD** | [jax-md/jax-md](https://github.com/jax-md/jax-md) | 1,393 | `pip install jax-md` | SDK | MEDIUM - GPU | Differentiable molecular dynamics in JAX |
| **e3nn** | [e3nn/e3nn](https://github.com/e3nn/e3nn) | 1,227 | `pip install e3nn` | SDK | MEDIUM | Euclidean symmetry equivariant neural networks |
| **GNoME** | [google-deepmind/materials_discovery](https://github.com/google-deepmind/materials_discovery) | 1,147 | source install | SDK | HIGH | Graph Networks for Materials Exploration |
| **PaddleHelix** | [PaddlePaddle/PaddleHelix](https://github.com/PaddlePaddle/PaddleHelix) | 1,108 | `pip install paddlehelix` | SDK | MEDIUM - GPU | Bio-computing platform (Baidu) |
| **TorchGeo** | [torchgeo/torchgeo](https://github.com/torchgeo/torchgeo) | 3,931 | `pip install torchgeo` | SDK | MEDIUM - GPU | Datasets and models for geospatial data |

### Priority for Cloud Brain Integration

**Tier 1 (must-have):** PyTorch Geometric, e3nn, JAX-MD
**Tier 2 (high value):** DGL, PyMatGen, Graphormer
**Tier 3 (specialized):** GraphCast, GNoME, PaddleHelix

---

## 9. Data Standards & Formats

| Name | GitHub | Stars | Install | API Type | Integration Complexity | Notes |
|------|--------|-------|---------|----------|----------------------|-------|
| **Zarr** | [zarr-developers/zarr-python](https://github.com/zarr-developers/zarr-python) | 1,943 | `pip install zarr` | SDK | LOW | Cloud-native chunked arrays; supports S3/GCS |
| **AnnData** | [scverse/anndata](https://github.com/scverse/anndata) | 722 | `pip install anndata` | SDK | LOW | Annotated data matrices; standard for single-cell |
| **BIDS** | [bids-standard/bids-specification](https://github.com/bids-standard/bids-specification) | 348 | spec only | SDK (pybids) | LOW | Brain Imaging Data Structure standard |
| **OME-Zarr** | [ome/ome-zarr-py](https://github.com/ome/ome-zarr-py) | 227 | `pip install ome-zarr` | SDK | LOW | Next-gen bioimaging file format |
| **NWB (PyNWB)** | [NeurodataWithoutBorders/pynwb](https://github.com/NeurodataWithoutBorders/pynwb) | 210 | `pip install pynwb` | SDK | MEDIUM | Neurodata Without Borders; standard for neurophysiology |

### Priority for Cloud Brain Integration

**Tier 1 (must-have):** Zarr, AnnData, NWB/PyNWB
**Tier 2 (high value):** BIDS, OME-Zarr

---

## 10. Neuroscience-Specific

| Name | GitHub | Stars | Install | API Type | Integration Complexity | Notes |
|------|--------|-------|---------|----------|----------------------|-------|
| **DeepLabCut** | [DeepLabCut/DeepLabCut](https://github.com/DeepLabCut/DeepLabCut) | 5,555 | `pip install deeplabcut` | SDK, CLI | MEDIUM - GPU | Markerless animal pose estimation |
| **Biopython** | [biopython/biopython](https://github.com/biopython/biopython) | 4,929 | `pip install biopython` | SDK | LOW | Swiss army knife for bioinformatics |
| **SpikeInterface** | [SpikeInterface/spikeinterface](https://github.com/SpikeInterface/spikeinterface) | 752 | `pip install spikeinterface` | SDK | LOW | Unified spike sorting across 10+ sorters |
| **CaImAn** | [flatironinstitute/CaImAn](https://github.com/flatironinstitute/CaImAn) | 720 | `pip install caiman` | SDK | MEDIUM | Calcium imaging analysis |
| **SLEAP** | [talmolab/sleap](https://github.com/talmolab/sleap) | 570 | `pip install sleap` | SDK, CLI | MEDIUM - GPU | Multi-animal pose tracking |
| **Suite2p** | [MouseLand/suite2p](https://github.com/MouseLand/suite2p) | 439 | `pip install suite2p` | SDK | MEDIUM | Two-photon calcium imaging pipeline |
| **GLUE** | [gao-lab/GLUE](https://github.com/gao-lab/GLUE) | 456 | `pip install scglue` | SDK | MEDIUM - GPU | Multi-omics single-cell integration |
| **AllenSDK** | [AllenInstitute/AllenSDK](https://github.com/AllenInstitute/AllenSDK) | 378 | `pip install allensdk` | SDK, REST | MEDIUM | Allen Brain Atlas data access |
| **NWB (PyNWB)** | [NeurodataWithoutBorders/pynwb](https://github.com/NeurodataWithoutBorders/pynwb) | 210 | `pip install pynwb` | SDK | MEDIUM | Neurodata Without Borders standard |

---

## 11. Workflow & MLOps Infrastructure

| Name | GitHub | Stars | Install | API Type | Integration Complexity | Notes |
|------|--------|-------|---------|----------|----------------------|-------|
| **MLflow** | [mlflow/mlflow](https://github.com/mlflow/mlflow) | 24,871 | `pip install mlflow` | SDK, REST | LOW | Experiment tracking, model registry |
| **DVC** | [treeverse/dvc](https://github.com/treeverse/dvc) | 15,458 | `pip install dvc` | SDK, CLI | LOW | Data version control for ML |
| **W&B** | [wandb/wandb](https://github.com/wandb/wandb) | 10,925 | `pip install wandb` | SDK, REST | LOW | Experiment tracking and visualization |
| **BentoML** | [bentoml/BentoML](https://github.com/bentoml/BentoML) | 8,529 | `pip install bentoml` | SDK, CLI | MEDIUM | Model serving and deployment |
| **LitServe** | [Lightning-AI/LitServe](https://github.com/Lightning-AI/LitServe) | 3,823 | `pip install litserve` | SDK | LOW | Lightweight AI inference servers |
| **Nextflow** | [nextflow-io/nextflow](https://github.com/nextflow-io/nextflow) | 3,331 | `curl -s get.nextflow.io \| bash` | CLI | MEDIUM | Data-driven computational pipelines |
| **Snakemake** | [snakemake/snakemake](https://github.com/snakemake/snakemake) | 2,732 | `pip install snakemake` | SDK, CLI | LOW | Python workflow management |
| **Fireworks** | [materialsproject/fireworks](https://github.com/materialsproject/fireworks) | 422 | `pip install fireworks` | SDK | MEDIUM | Scientific workflow management with MongoDB |

---

## Summary: Integration Classification

### REST APIs -- Easy MCP Server Wrapping (15 services)

These can be wrapped as MCP servers with minimal effort:

| Service | Base URL | Key? | Ideal MCP Actions |
|---------|----------|------|-------------------|
| Semantic Scholar | `api.semanticscholar.org` | Free key | search_papers, get_paper, get_citations, get_references |
| PubMed E-utilities | `eutils.ncbi.nlm.nih.gov` | Free key | search, fetch, link, summary |
| OpenAlex | `api.openalex.org` | Email (polite) | search_works, get_work, get_author, get_institution |
| ClinicalTrials.gov | `clinicaltrials.gov/data-api` | None | search_studies, get_study, get_stats |
| ChEMBL | `www.ebi.ac.uk/chembl/api` | None | search_molecules, get_assays, get_targets |
| PubChem | `pubchem.ncbi.nlm.nih.gov/rest/pug` | None | search_compounds, get_properties, get_assays |
| UniProt | `rest.uniprot.org` | None | search_proteins, get_protein, blast |
| RCSB PDB | `data.rcsb.org` | None | search_structures, get_structure, get_ligands |
| FDA openFDA | `api.fda.gov` | Free key | search_drugs, search_events, search_labels |
| Protocols.io | `protocols.io/api/v4` | OAuth2 | search_protocols, get_protocol |
| NCBI Datasets | `api.ncbi.nlm.nih.gov/datasets` | Free key | get_gene, get_genome, download_data |
| DrugBank | `go.drugbank.com` | Commercial | search_drugs, get_interactions |
| Addgene | `addgene.org` | None | search_plasmids |
| Benchling | `benchling.com/api/v2` | Commercial | manage_sequences, manage_entries |
| Materials Project | `api.materialsproject.org` | Free key | search_materials, get_properties |

### Python SDKs -- Easy AgentTool Wrapping (40+ libraries)

These have clean Python APIs and can be wrapped as AgentTools:

**Easiest (just `import` + wrap):**
- RDKit, DeepChem, Scanpy, AnnData, Biopython, Pint, SciSpaCy
- Cellpose, StarDist, Zarr, scikit-bio, Chemprop, PyAlex
- semanticscholar (Python client), fhirclient

**Medium (need GPU or data setup):**
- AlphaFold 2/3, ESM3, Boltz, Chai-1, ColabFold
- DeepLabCut, MONAI, DiffDock, ProteinMPNN
- PyTorch Geometric, DGL, JAX-MD, e3nn
- scvi-tools, Nucleotide Transformer, CaImAn, Suite2p
- OpenMM, FAIR-Chem

### CLI Tools -- Subprocess Execution (15+ tools)

These are best run via subprocess or containerized execution:

| Tool | Command Pattern | Container Available |
|------|----------------|-------------------|
| STAR | `STAR --runMode alignReads ...` | Yes (biocontainers) |
| Salmon | `salmon quant -i index -l A ...` | Yes (biocontainers) |
| minimap2 | `minimap2 -a ref.fa reads.fq` | Yes |
| GATK | `gatk HaplotypeCaller ...` | Yes (broadinstitute) |
| kallisto | `kallisto quant -i index ...` | Yes |
| Picard | `picard MarkDuplicates ...` | Yes |
| Dorado | `dorado basecaller model ...` | Yes |
| CellRanger | `cellranger count ...` | Yes (10x) |
| Nextflow | `nextflow run nf-core/rnaseq` | Self-contained |
| Snakemake | `snakemake --cores 8` | Yes |
| NCBI datasets | `datasets download genome ...` | Yes |
| AutoDock Vina | `vina --receptor ... --ligand ...` | Yes |
| gnina | `gnina -r receptor -l ligand` | Yes |
| Open Babel | `obabel -i sdf -o pdb` | Yes |
| QuPath | `QuPath script --script groovy` | No (desktop) |

---

## Top 30 "Must-Integrate" Tools (Ranked by Impact)

| Rank | Tool | Category | Stars | API Type | Why Critical |
|------|------|----------|-------|----------|-------------|
| 1 | AlphaFold 2/3 | Protein | 14,384/7,755 | SDK | Gold standard structure prediction |
| 2 | Semantic Scholar | Literature | N/A | REST | 220M+ papers, free API |
| 3 | RDKit | Drug Discovery | 3,346 | SDK | Industry-standard cheminformatics |
| 4 | Scanpy | Genomics | 2,380 | SDK | Standard for scRNA-seq analysis |
| 5 | DeepLabCut | Imaging | 5,555 | SDK | Standard for behavioral tracking |
| 6 | PubMed | Literature | N/A | REST | 36M+ biomedical articles |
| 7 | PyTorch Geometric | ML | 23,587 | SDK | GNNs for molecules/proteins |
| 8 | Cellpose | Imaging | 2,119 | SDK | Best general cell segmentation |
| 9 | Boltz | Protein | 3,850 | SDK | Open AF3 competitor, fast |
| 10 | DeepChem | Drug Discovery | 6,618 | SDK | Comprehensive DL for drug discovery |
| 11 | ESM3 | Protein | 2,278 | SDK+REST | Protein language model with API |
| 12 | ColabFold | Protein | 2,675 | SDK | Fast, accessible protein folding |
| 13 | OpenAlex | Literature | N/A | REST | Open scholarly graph |
| 14 | ChEMBL | Drug Discovery | N/A | REST | 2.4M compounds, free API |
| 15 | napari | Imaging | 2,613 | SDK | Multi-dim image viewer + plugins |
| 16 | Zarr | Data | 1,943 | SDK | Cloud-native array storage |
| 17 | MONAI | Imaging | 7,954 | SDK | Healthcare imaging AI toolkit |
| 18 | scvi-tools | Genomics | 1,585 | SDK | Deep learning for single-cell |
| 19 | AnnData | Data | 722 | SDK | Core data format for single-cell |
| 20 | Biopython | General | 4,929 | SDK | Swiss army knife for bioinformatics |
| 21 | RFdiffusion | Protein | 2,788 | SDK | Protein backbone design |
| 22 | Nextflow | Workflow | 3,331 | CLI | Production pipeline orchestration |
| 23 | DiffDock | Drug Discovery | 1,462 | SDK | SOTA molecular docking |
| 24 | Pint | Lab | 2,709 | SDK | Physical units handling |
| 25 | ClinicalTrials.gov | Clinical | N/A | REST | Trial search and matching |
| 26 | SpikeInterface | Neuro | 752 | SDK | Unified spike sorting |
| 27 | NWB/PyNWB | Data | 210 | SDK | Neurophysiology data standard |
| 28 | Chemprop | Drug Discovery | 2,298 | SDK | Molecular property prediction |
| 29 | OpenMM | Drug Discovery | 1,818 | SDK | Molecular dynamics simulation |
| 30 | ProteinMPNN | Protein | 1,665 | SDK | Inverse protein folding |

---

## Implementation Roadmap

### Phase 1: REST API MCP Servers (Week 1-2)
- Semantic Scholar, PubMed, OpenAlex, ChEMBL, PubChem, UniProt, ClinicalTrials.gov
- Each is a standalone MCP server, ~200 lines of code each

### Phase 2: Python SDK AgentTools (Week 3-4)
- RDKit, Scanpy, AnnData, Cellpose, Biopython, Pint, DeepChem
- Wrap as AgentTools with input validation and output parsing

### Phase 3: GPU-Intensive Model Services (Week 5-8)
- AlphaFold, Boltz, ESM3, DiffDock, ColabFold, DeepLabCut
- Deploy as containerized GPU services with queue management

### Phase 4: Pipeline Orchestration (Week 9-12)
- Nextflow/Snakemake integration for multi-step workflows
- nf-core pipeline catalog integration
- MLflow experiment tracking

---

*Last updated: 2026-03-20. All star counts verified via `gh api repos/{owner}/{repo}`.*
