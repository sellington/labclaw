# LabClaw Cloud Brain -- Complete Tool Inventory

> Compiled 2026-03-20. Sources: ToolUniverse, K-Dense AI, Biomni, Anthropic Life Sciences.

---

## 1. ToolUniverse (mims-harvard/ToolUniverse)

**2,124 tools across 447 tool configurations and 58 research skills.**

### 1.1 Research Skills (48 domain skills + 10 developer skills)

| Skill Name | Category | Description |
|---|---|---|
| tooluniverse | Router | Dispatches to the right specialized skill automatically |
| tooluniverse-adverse-event-detection | Drug Safety | Identifies adverse drug signals using FDA FAERS data |
| tooluniverse-antibody-engineering | Protein Design | Antibody humanization, affinity maturation, and optimization |
| tooluniverse-binder-discovery | Drug Discovery | Small molecule binder discovery via structure and ligand approaches |
| tooluniverse-cancer-variant-interpretation | Oncology | Interprets somatic cancer mutations clinically |
| tooluniverse-chemical-compound-retrieval | Chemistry | Retrieves chemical compound info from PubChem and ChEMBL |
| tooluniverse-chemical-safety | Toxicology | Chemical safety assessment using ADMET-AI, CTD, and FDA data |
| tooluniverse-clinical-guidelines | Medicine | Clinical practice guidelines from 12+ sources |
| tooluniverse-clinical-trial-design | Trials | Evaluates clinical trial design feasibility |
| tooluniverse-clinical-trial-matching | Precision Medicine | Matches patients to appropriate clinical trials |
| tooluniverse-crispr-screen-analysis | Genomics | Analyzes CRISPR knockout/activation screening results |
| tooluniverse-custom-tool | Framework | Creates and registers custom tools at runtime |
| tooluniverse-disease-research | Research | Comprehensive disease reports using 100+ tools |
| tooluniverse-drug-drug-interaction | Pharmacology | Predicts and assesses drug-drug interaction risks |
| tooluniverse-drug-repurposing | Drug Discovery | Target-, compound-, and disease-driven repurposing strategies |
| tooluniverse-drug-research | Pharmacology | Comprehensive drug reports with evidence grading |
| tooluniverse-drug-target-validation | Target Research | Validates drug targets across 10 computational dimensions |
| tooluniverse-epigenomics | Genomics | Epigenomics and gene regulation (ENCODE, JASPAR, methylation) |
| tooluniverse-expression-data-retrieval | Genomics | Retrieves gene expression datasets from ArrayExpress and BioStudies |
| tooluniverse-gene-enrichment | Bioinformatics | Gene enrichment and pathway analysis via multiple platforms |
| tooluniverse-gwas-drug-discovery | Genetics | Converts GWAS signals to drug targets and repurposing opportunities |
| tooluniverse-gwas-finemapping | Genetics | Prioritizes causal variants via statistical fine-mapping |
| tooluniverse-gwas-snp-interpretation | Genetics | Interprets genetic variants from GWAS studies |
| tooluniverse-gwas-study-explorer | Genetics | GWAS study comparison and meta-analysis |
| tooluniverse-gwas-trait-to-gene | Genetics | Maps gene-trait associations from GWAS Catalog and Open Targets |
| tooluniverse-image-analysis | Imaging | Microscopy image analysis and quantitative imaging |
| tooluniverse-immune-repertoire-analysis | Immunology | TCR/BCR immune repertoire data analysis |
| tooluniverse-immunotherapy-response-prediction | Oncology | Predicts response to immune checkpoint inhibitors |
| tooluniverse-infectious-disease | Disease | Pathogen characterization and drug repurposing for outbreaks |
| tooluniverse-literature-deep-research | Research | Literature research with evidence grading and theme extraction |
| tooluniverse-metabolomics | Omics | Metabolomics research including metabolite identification |
| tooluniverse-metabolomics-analysis | Omics | Metabolomics data quantification, pathway, and flux analysis |
| tooluniverse-multi-omics-integration | Omics | Multi-omics dataset integration |
| tooluniverse-multiomic-disease-characterization | Disease | Multi-omics disease characterization |
| tooluniverse-network-pharmacology | Pharmacology | Compound-target-disease network analysis |
| tooluniverse-pharmacovigilance | Drug Safety | Drug safety signal analysis from FDA reports |
| tooluniverse-phylogenetics | Genomics | Phylogenetics and sequence analysis |
| tooluniverse-polygenic-risk-score | Genetics | Polygenic risk score construction and interpretation |
| tooluniverse-precision-medicine-stratification | Medicine | Patient stratification for precision medicine |
| tooluniverse-precision-oncology | Oncology | Actionable cancer treatment recommendations from molecular profiles |
| tooluniverse-protein-interactions | Proteomics | Protein-protein interaction network analysis (STRING, BioGRID) |
| tooluniverse-protein-structure-retrieval | Proteomics | Protein structure retrieval from PDB, PDBe, and AlphaFold |
| tooluniverse-protein-therapeutic-design | Drug Design | Protein therapeutic design using AI methods |
| tooluniverse-proteomics-analysis | Omics | Mass spectrometry proteomics data analysis |
| tooluniverse-rare-disease-diagnosis | Medicine | Rare disease differential diagnosis from phenotype and genetics |
| tooluniverse-rnaseq-deseq2 | Genomics | RNA-seq differential expression with PyDESeq2 |
| tooluniverse-sequence-retrieval | Genomics | DNA, RNA, and protein sequence retrieval from NCBI and ENA |
| tooluniverse-single-cell | Genomics | Single-cell RNA-seq analysis (scanpy, anndata) |
| tooluniverse-spatial-omics-analysis | Omics | Spatial multi-omics data integration |
| tooluniverse-spatial-transcriptomics | Genomics | Spatial transcriptomics from Visium, MERFISH, seqFISH |
| tooluniverse-statistical-modeling | Bioinformatics | Statistical modeling for biomedical data |
| tooluniverse-structural-variant-analysis | Genomics | Structural variant analysis for clinical genomics |
| tooluniverse-systems-biology | Bioinformatics | Pathway analysis via Reactome, KEGG, WikiPathways |
| tooluniverse-target-research | Research | Comprehensive drug target profiling (9 research paths) |
| tooluniverse-variant-analysis | Genomics | VCF processing, structural and copy number variant annotation |
| tooluniverse-variant-interpretation | Genomics | Clinical variant interpretation with ACMG classification |
| setup-tooluniverse | DevTool | Installation and configuration across MCP, CLI, SDK |
| create-tooluniverse-skill | DevTool | Creates new skills using test-driven methodology |
| devtu-auto-discover-apis | DevTool | Discovers life science APIs and generates tools |
| devtu-create-tool | DevTool | Structures new scientific tools with testing protocols |
| devtu-code-optimization | DevTool | Code optimization for tool implementations |
| devtu-docs-quality | DevTool | Validates and audits documentation standards |
| devtu-fix-tool | DevTool | Diagnoses and repairs failing tools |
| devtu-github | DevTool | GitHub workflows, hooks, and testing management |
| devtu-optimize-descriptions | DevTool | Improves tool description clarity |
| devtu-optimize-skills | DevTool | Skill quality enhancement through grading and disambiguation |
| devtu-self-evolve | DevTool | Full improvement cycles executed automatically |
| tooluniverse-sdk | DevTool | Python SDK for building AI scientist systems |
| tooluniverse-install-skills | DevTool | Auto-detects and installs missing skills |

### 1.2 API Tool Classes (447 tool configurations, 832 class mappings)

Organized by database/API source. Each configuration file defines multiple tool endpoints.

| Tool Config | Source/Database | Tool Class(es) |
|---|---|---|
| ada_aha_nccn_tools | ADA/AHA/NCCN Clinical Guidelines | ADAStandardsTool, AHAACCGuidelineTool, NCCNGuidelineTool |
| addgene_tools | Addgene Plasmid Repository | AddgeneTool |
| admetai_tools | ADMET-AI Drug Properties | ADMETAITool |
| adverse_event_tools | FDA Adverse Events | FAERSAnalyticsTool |
| allen_brain_tools | Allen Brain Atlas | AllenBrainTool |
| alliance_genome_tools | Alliance of Genome Resources | AllianceGenomeTool |
| alphafold_tools | AlphaFold DB | AlphaFoldRESTTool |
| alphamissense_tools | AlphaMissense | AlphaMissenseTool |
| arrayexpress_tools | ArrayExpress | ArrayExpressRESTTool |
| arxiv_tools | arXiv Preprints | ArXivTool, ArXivPDFSnippetsTool |
| bgee_tools | Bgee Gene Expression | BgeeTool |
| bigg_models_tools | BiGG Metabolic Models | BiGGModelsTool |
| bindingdb_tools | BindingDB | BindingDBTool |
| bioconductor_tools | Bioconductor R Packages | PackageTool |
| biogrid_tools | BioGRID Interactions | BioGRIDRESTTool |
| bioimage_archive_tools | BioImage Archive | BioImageArchiveTool |
| biomodels_tools | BioModels Repository | BioModelsRESTTool |
| bioportal_tools | BioPortal Ontologies | BioPortalTool |
| biorxiv_tools | bioRxiv Preprints | BioRxivTool |
| biosamples_tools | BioSamples | BioSamplesTool |
| biostudies_tools | BioStudies | BioStudiesRESTTool |
| biothings_tools | BioThings API | MyGeneTool, MyChemTool, MyDiseaseTool, MyVariantTool |
| biotools_registry_tools | bio.tools Registry | BaseRESTTool |
| blast_tools | NCBI BLAST | NCBIBlastTool |
| bmrb_tools | BMRB NMR Data | BaseRESTTool |
| boltz_mcp_loader_tools | Boltz Molecular Docking | Boltz2DockingTool |
| brenda_tools | BRENDA Enzyme DB | BRENDATool |
| bridgedb_tools | BridgeDb ID Mapping | BridgeDbTool |
| bvbrc_tools | BV-BRC Pathogen Data | BVBRCTool |
| cadd_tools | CADD Variant Scoring | CADDTool |
| cancer_prognosis_tools | Cancer Prognosis | CancerPrognosisTool |
| cath_tools | CATH Protein Structure | CATHTool |
| cbioportal_tools | cBioPortal Cancer Genomics | CBioPortalRESTTool |
| cdc_tools | CDC Public Health | CDCRESTTool |
| cellmarker_tools | CellMarker | CellMarkerTool |
| cellosaurus_tools | Cellosaurus Cell Lines | CellosaurusSearchTool, CellosaurusGetCellLineInfoTool, CellosaurusQueryConverterTool |
| cellpainting_tools | Cell Painting | CellPaintingTool |
| cellxgene_census_tools | CZ CELLxGENE Census | CELLxGENECensusTool |
| cellxgene_discovery_tools | CZ CELLxGENE Discovery | CellxGeneDiscoveryTool |
| chebi_tools | ChEBI Chemical Entities | ChEBITool |
| chembl_tools | ChEMBL Drug DB | ChEMBLRESTTool, ChEMBLTool |
| chem_compute_tools | Chemical Computation | ChemComputeTool |
| chipatlas_tools | ChIP-Atlas | ChIPAtlasTool |
| civic_tools | CIViC Clinical Variants | CIViCTool |
| clingen_tools | ClinGen | ClinGenTool |
| clingen_ar_tools | ClinGen Actionability | ClinGenARTool |
| clingen_dosage_api_tools | ClinGen Dosage | ClinGenDosageTool |
| clinical_guidelines_tools | Clinical Guidelines (multi) | EuropePMCGuidelinesTool, PubMedGuidelinesTool, WHOGuidelinesTool, NICEGuidelineFullTextTool, OpenAlexGuidelinesTool, SIGNSearchGuidelinesTool, GINGuidelinesTool, CTFPHCSearchGuidelinesTool, CMAGuidelinesTool, TRIPDatabaseTool |
| clinicaltrials_gov_tools | ClinicalTrials.gov | CTGovAPITool, ClinicalTrialsGovTool, ClinicalTrialsSearchTool, ClinicalTrialsTool, ClinicalTrialsDetailsTool |
| clinvar_tools | ClinVar | ClinVarRESTTool, ClinVarSearchVariants, ClinVarGetVariantDetails, ClinVarGetClinicalSignificance |
| clue_tools | CLUE / Connectivity Map | ClueTool |
| complex_portal_tools | Complex Portal | ComplexPortalTool |
| compose_tools | Tool Composition | ComposeTool |
| core_tools | CORE Aggregator | CoreTool, CorePDFSnippetsTool |
| cosmic_tools | COSMIC Somatic Mutations | COSMICTool |
| cpic_tools | CPIC Pharmacogenomics | CPICSearchPairsTool |
| crossref_tools | Crossref Metadata | CrossrefRESTTool |
| cryoet_tools | CryoET Data Portal | BaseRESTTool |
| ctd_tools | CTD Toxicogenomics | CTDTool |
| dailymed_tools | DailyMed Drug Labels | DailyMedSPLParserTool, SearchSPLTool, GetSPLBySetIDTool |
| dbfetch_tools | EBI DBfetch | DbfetchRESTTool |
| dblp_tools | DBLP Computer Science | DBLPTool |
| dbpedia_tools | DBpedia Knowledge Graph | DBpediaSPARQLTool |
| dbsnp_tools | dbSNP Variants | dbSNPRESTTool, dbSNPGetVariantByRsID, dbSNPSearchByGene, dbSNPGetFrequencies |
| deepgo_tools | DeepGO Protein Function | DeepGOTool |
| depmap_tools | DepMap Cancer Dependencies | DepMapTool |
| dfam_tools | Dfam Repeat Families | DfamTool |
| dgidb_tools | DGIdb Drug-Gene | DGIdbTool |
| disease_ontology_tools | Disease Ontology | DiseaseOntologyTool |
| disgenet_tools | DisGeNET | DisGeNETTool |
| disprot_tools | DisProt Disordered Proteins | DisProtTool |
| dna_tools | DNA Sequence Tools | DNATool |
| doaj_tools | DOAJ Open Access | DOAJTool |
| dose_response_tools | Dose-Response Analysis | DoseResponseTool |
| drug_properties_tools | Drug Properties Computation | DrugPropertiesTool |
| drug_synergy_tools | Drug Synergy Prediction | DrugSynergyTool |
| dynamut2_tools | DynaMut2 Stability | DynaMut2Tool |
| ebi_proteins_coordinates_tools | EBI Proteins Coordinates | EBIProteinsCoordinatesTool |
| ebi_proteins_epitope_tools | EBI Proteins Epitopes | EBIProteinsEpitopeTool |
| ebi_proteins_ext_tools | EBI Proteins Extended | EBIProteinsExtTool |
| ebi_proteins_features_tools | EBI Proteins Features | EBIProteinsFeaturesTool |
| ebi_proteins_interactions_tools | EBI Proteins Interactions | EBIProteinsInteractionsTool |
| ebi_search_tools | EBI Search | EBISearchRESTTool |
| ebi_taxonomy_tools | EBI Taxonomy | EBITaxonomyTool |
| efo_tools | EFO Ontology | EFOTool, OLSRESTTool |
| emdb_tools | EMDB Electron Microscopy | EMDBRESTTool |
| emolecules_tools | eMolecules Chemical | EMoleculesTool |
| ena_browser_tools | ENA Browser | ENABrowserRESTTool |
| ena_portal_tools | ENA Portal | ENAPortalTool |
| encode_tools | ENCODE Functional Genomics | ENCODERESTTool, ENCODESearchTool, ENCODEFilesTool, ENCODESearchBiosamplesTool |
| enamine_tools | Enamine Chemical | EnamineTool |
| enrichr_tools | Enrichr Gene Set | EnrichrTool |
| ensembl_tools | Ensembl Genome Browser | EnsemblRESTTool, EnsemblLookupGene, EnsemblGetSequence, EnsemblGetVariants |
| ensembl_archive_tools | Ensembl Archive | EnsemblArchiveTool |
| ensembl_compara_tools | Ensembl Compara | EnsemblComparaTool |
| ensembl_info_tools | Ensembl Info | EnsemblInfoTool |
| ensembl_ld_tools | Ensembl Linkage Disequilibrium | EnsemblLDTool |
| ensembl_map_tools | Ensembl Coordinate Mapping | EnsemblMapTool |
| ensembl_overlap_tools | Ensembl Overlap | EnsemblOverlapTool |
| ensembl_phenotype_tools | Ensembl Phenotype | EnsemblPhenotypeTool |
| ensembl_regulation_tools | Ensembl Regulation | EnsemblRegulationTool |
| ensembl_sequence_tools | Ensembl Sequence | EnsemblSequenceTool |
| ensembl_variation_ext_tools | Ensembl Variation Extended | EnsemblVariationExtTool |
| ensembl_vep_tools | Ensembl VEP | EnsemblVEPTool |
| ensembl_xrefs_tools | Ensembl Cross-References | EnsemblXrefsTool |
| eol_tools | Encyclopedia of Life | EOLTool |
| epigenomics_tools | UCSC Epigenomics | EpigenomicsTool, UCSCEpigenomicsTool |
| epigraphdb_tools | EpiGraphDB Epidemiology | EpiGraphDBTool |
| esm_tools | ESM Protein Language Model | PackageTool |
| euhealth_tools | EU Health Resources | EuHealthTopicSearchTool, EuHealthDeepDiveTool |
| europepmc_annotations_tools | Europe PMC Annotations | EuroPMCAnnotationsTool |
| europe_pmc_tools | Europe PMC | EuropePMCRESTTool, EuropePMCTool, EuropePMCFullTextFetchTool, EuropePMCFullTextSnippetsTool |
| eve_tools | EVE Variant Effect | EVETool |
| expression_atlas_tools | Expression Atlas | ExpressionAtlasTool |
| faers_analytics_tools | FAERS Analytics | FAERSAnalyticsTool |
| fatcat_tools | Fatcat/Internet Archive Scholar | FatcatScholarTool, FatcatResultParser, FatcatMetadataParser |
| fda_drug_adverse_event_tools | FDA Drug Adverse Events | FDADrugAdverseEventTool |
| fda_drug_adverse_event_detail_tools | FDA Drug Adverse Event Detail | FDADrugAdverseEventDetailTool, FDADrugInteractionDetailTool, FDACountAdditiveReactionsTool |
| fda_drug_labeling_tools | FDA Drug Labeling | FDADrugLabel (152 drug-specific tools) |
| fda_orange_book_tools | FDA Orange Book | FDAOrangeBookTool |
| fda_pharmacogenomic_biomarkers_tools | FDA Pharmacogenomics | FDAPharmacogenomicBiomarkersTool |
| figshare_tools | Figshare Data Repository | BaseRESTTool |
| file_download_tools | File Download | FileDownloadTool, TextDownloadTool, BinaryDownloadTool |
| fooddata_central_tools | USDA FoodData Central | FoodDataCentralTool |
| fourdn_tools | 4DN Data Portal | FourDNTool |
| gbif_tools | GBIF Biodiversity | GBIFTool, GBIFOccurrenceTool |
| gdc_tools | GDC Cancer Data | GDCProjectsTool, GDCCasesTool, GDCFilesTool, GDCGeneExpressionTool, GDCMutationFrequencyTool, GDCSSMTool, GDCCNVTool |
| gencc_tools | GenCC Gene-Disease | GenCCTool |
| gene_ontology_tools | Gene Ontology | GeneOntologyTool |
| genome_nexus_tools | Genome Nexus | GenomeNexusTool |
| geo_tools | GEO Expression | GEORESTTool, GEOSearchDatasets, GEOGetDatasetInfo, GEOGetSampleInfo |
| glygen_tools | GlyGen Glycoscience | GlyGenTool |
| gnomad_tools | gnomAD Population Variants | gnomADGraphQLTool, gnomADGraphQLQueryTool, gnomADGetGeneConstraints |
| gnps_tools | GNPS Natural Products | GNPSTool |
| go_api_tools | GO API | GOAPITool |
| gpcrdb_tools | GPCRdb Receptors | GPCRdbTool |
| gprofiler_tools | g:Profiler Enrichment | GProfilerTool |
| gtdb_tools | GTDB Taxonomy | GTDBTool |
| gtex_tools | GTEx Expression | GTExExpressionTool, GTExEQTLTool |
| gtex_v2_tools | GTEx V2 API | GTExV2Tool |
| gtopdb_tools | GtoPdb Pharmacology | GtoPdbRESTTool |
| gwas_tools | GWAS Catalog | GWASRESTTool, GWASStudySearch, GWASStudyByID, GWASAssociationSearch, GWASAssociationByID, GWASSNPSearch, GWASSNPByID, GWASStudiesForTrait, GWASAssociationsForTrait, GWASVariantsForTrait, GWASAssociationsForStudy, GWASAssociationsForSNP, GWASSNPsForGene |
| gxa_tools | Gene Expression Atlas | GxATool |
| hal_tools | HAL Open Archive | HALTool |
| harmonizome_tools | Harmonizome | HarmonizomeTool |
| hca_tools | Human Cell Atlas | HCATool |
| health_disparities_tools | Health Disparities | HealthDisparitiesTool |
| hgnc_tools | HGNC Gene Nomenclature | HGNCTool |
| hmdb_tools | HMDB Metabolites | HMDBTool |
| hpa_tools | Human Protein Atlas | HPASearchTool, HPAGetGenePageDetailsTool, HPAGetSubcellularLocationTool, HPAGetRnaExpressionByTissueTool, HPAGetCancerPrognosticsTool, HPAGetProteinInteractionsTool, HPAGetBiologicalProcessTool, HPAGetDiseaseExpressionTool, + 9 more |
| hpo_tools | HPO Phenotype Ontology | HPOTool |
| humanbase_tools | HumanBase Functional Genomics | HumanBaseTool |
| icd_tools | ICD Classification | ICDTool, ICD10Tool |
| icite_tools | iCite Citation Analysis | ICiteSearchPublicationsTool |
| identifiers_org_tools | Identifiers.org | IdentifiersOrgTool |
| idt_tools | IDT Oligo Design | IDTTool |
| iedb_tools | IEDB Immune Epitope | IEDBTool |
| imgt_tools | IMGT Immunogenetics | IMGTTool |
| impc_tools | IMPC Mouse Phenotyping | IMPCTool |
| inaturalist_tools | iNaturalist Biodiversity | INaturalistTool |
| intact_tools | IntAct Molecular Interactions | IntActRESTTool |
| interpro_tools | InterPro Protein Families | InterProRESTTool |
| interpro_domain_arch_tools | InterPro Domain Architecture | InterProDomainArchTool |
| interpro_entry_tools | InterPro Entry | InterProEntryTool |
| interpro_ext_tools | InterPro Extended | InterProExtTool |
| interproscan_tools | InterProScan | InterProScanTool |
| intogen_tools | IntOGen Cancer Drivers | IntOGenTool |
| itis_tools | ITIS Taxonomic Information | ITISTool |
| jaspar_tools | JASPAR TF Binding | JASPARRESTTool |
| kegg_tools | KEGG Pathways | KEGGRESTTool, KEGGSearchPathway, KEGGGetPathwayInfo, KEGGFindGenes, KEGGGetGeneInfo, KEGGListOrganisms |
| kegg_ext_tools | KEGG Extended | KEGGExtTool |
| l1000fwd_tools | L1000FWD Perturbations | L1000FWDTool |
| lipidmaps_tools | LIPID MAPS | LipidMapsTool |
| loinc_tools | LOINC Lab Codes | LOINCTool |
| lovd_tools | LOVD Variant DB | LOVDTool |
| markitdown_tools | MarkItDown Document Converter | MarkItDownTool |
| mcule_tools | Mcule Chemical | MculeTool |
| medlineplus_tools | MedlinePlus Health Info | MedlinePlusRESTTool |
| meme_tools | MEME Motif Discovery | MEMETool |
| mesh_tools | MeSH Medical Terms | MeSHTool |
| metaboanalyst_tools | MetaboAnalyst | MetaboAnalystTool |
| metabolights_tools | MetaboLights | MetaboLightsRESTTool |
| metabolomics_workbench_tools | Metabolomics Workbench | MetabolomicsWorkbenchTool |
| metacyc_tools | MetaCyc Metabolism | MetaCycTool |
| mgnify_tools | MGnify Metagenomics | MGnifyStudiesTool, MGnifyAnalysesTool |
| mgnify_expanded_tools | MGnify Expanded | MGnifyExpandedTool |
| mirna_tools | miRNA | miRNASearchTool, miRNAGetTool |
| mobidb_tools | MobiDB Disorder | MobiDBTool |
| molecule_2d_tools | 2D Molecular Visualization | Molecule2DTool |
| molecule_3d_tools | 3D Molecular Visualization | Molecule3DTool |
| monarch_tools | Monarch Initiative | MonarchTool |
| monarch_v3_tools | Monarch V3 | MonarchV3Tool |
| mpd_tools | Mouse Phenome DB | MPDRESTTool |
| mydisease_tools | MyDisease.info | MyDiseaseTool |
| ncbi_datasets_tools | NCBI Datasets | NCBIDatasetsTool |
| ncbi_nucleotide_tools | NCBI Nucleotide | NCBINucleotideSearchTool |
| ncbi_sra_tools | NCBI SRA | NCBISRATool |
| nci_thesaurus_tools | NCI Thesaurus | NCIThesaurusTool |
| ndex_tools | NDEx Network Exchange | NDExTool |
| neb_tm_tools | NEB Tm Calculator | NEBTmTool |
| neuromorpho_tools | NeuroMorpho.Org | NeuroMorphoTool |
| nextstrain_tools | Nextstrain Pathogen Evolution | NextstrainTool |
| nhanes_tools | NHANES Survey Data | NHANESTool |
| nvidia_nim_tools | NVIDIA NIM (16 tools) | NvidiaNIMTool |
| obis_tools | OBIS Marine Biodiversity | OBISOccurrenceTool, OBISTaxaTool |
| odphp_tools | ODPHP Health Prevention | ODPHPRESTTool, ODPHPTopicSearch, ODPHPItemList, ODPHPMyHealthfinder, ODPHPOutlinkFetch |
| ols_tools | OLS Ontology Lookup | OLSTool |
| oma_tools | OMA Orthology | OMATool |
| omim_tools | OMIM Genetic Disorders | OMIMTool |
| omnipath_tools | OmniPath Signaling | OmniPathTool |
| oncokb_tools | OncoKB Precision Oncology | OncoKBTool |
| openaire_tools | OpenAIRE Research | OpenAIRETool |
| openalex_tools | OpenAlex Scholarly | OpenAlexRESTTool, OpenAlexTool |
| openfda_tools | OpenFDA | FDATool, FDADrugLabelTool, FDADrugLabelSearchTool, FDADrugLabelSearchIDTool, FDADrugLabelFieldValueTool, FDADrugLabelGetDrugGenericNameTool, FDADrugLabelGetDrugNamesByIndicationAggregated, FDADrugLabelGetDrugNamesByIndicationStats, FDADrugLabel, FDADrugLabelAggregated, FDADrugLabelStats |
| openfda_approval_tools | OpenFDA Approval | OpenFDAApprovalTool |
| openneuro_tools | OpenNeuro Neuroimaging | OpenNeuroTool |
| opentarget_tools | Open Targets Platform | OpenTarget, OpentargetTool, OpentargetToolDrugNameMatch, DiseaseTargetScoreTool |
| opentarget_genetics_tools | Open Targets Genetics | OpenTargetGenetics, OpentargetGeneticsTool |
| opentree_tools | Open Tree of Life | OpenTreeTool |
| orcid_tools | ORCID Researcher IDs | ORCIDTool |
| orphanet_tools | Orphanet Rare Diseases | OrphanetTool |
| orthodb_tools | OrthoDB Orthology | OrthoDBTool |
| osf_preprints_tools | OSF Preprints | OSFPreprintsTool |
| oxo_tools | OxO Ontology Mapping | OxOTool |
| paleobiology_tools | Paleobiology DB | PaleobiologyRESTTool |
| panther_tools | PANTHER Classification | PANTHERTool |
| pathway_commons_tools | Pathway Commons | PathwayCommonsTool |
| pdbe_api_tools | PDBe API | PDBeAPIRESTTool |
| pdbe_compound_tools | PDBe Compound | PDBECompoundTool |
| pdbe_kb_tools | PDBe Knowledge Base | PDBe_KB_Tool |
| pdbe_ligands_tools | PDBe Ligands | PDBeLigandsTool |
| pdbepisa_tools | PDBe PISA Assemblies | PDBePISATool |
| pdbe_search_tools | PDBe Search | PDBeSearchTool |
| pdbe_sifts_tools | PDBe SIFTS Mapping | PDBeSIFTSTool |
| pdbe_validation_tools | PDBe Validation | PDBeValidationTool |
| pdc_tools | PDC Proteomics | PDCTool |
| pfam_tools | Pfam Protein Families | PfamTool |
| pharmacodb_tools | PharmacoDB | PharmacoDBTool |
| pharmgkb_tools | PharmGKB Pharmacogenomics | PharmGKBTool |
| pharos_tools | Pharos Druggable Genome | PharosTool |
| plant_reactome_tools | Plant Reactome | PlantReactomeTool |
| pmc_tools | PubMed Central | PMCTool |
| pombase_tools | PomBase Fission Yeast | PomBaseTool |
| pride_tools | PRIDE Proteomics | PRIDERESTTool |
| prosite_tools | PROSITE Protein Motifs | PROSITETool |
| protacdb_tools | PROTAC-DB | ProtacDBTool |
| proteins_api_tools | UniProt Proteins API | ProteinsAPIRESTTool |
| proteinsplus_tools | ProteinsPlus Structure | ProteinsPlusRESTTool |
| protein_structure_3d_tools | 3D Protein Structure | ProteinStructure3DTool |
| proteomexchange_tools | ProteomeXchange | ProteomeXchangeTool |
| proteomicsdb_tools | ProteomicsDB | ProteomicsDBTool |
| pubchem_tools | PubChem Chemistry | PubChemRESTTool |
| pubchem_bioassay_tools | PubChem BioAssay | PubChemBioAssayTool |
| pubchem_tox_tools | PubChem Toxicology | PubChemToxTool |
| pubmed_tools | PubMed Literature | PubMedRESTTool |
| pubtator_tools | PubTator NER | PubTatorTool |
| quickgo_tools | QuickGO Annotations | QuickGOTool |
| rcsb_pdb_tools | RCSB PDB | RCSBTool |
| rcsb_advanced_search_tools | RCSB Advanced Search | RCSBAdvancedSearchTool |
| rcsb_data_tools | RCSB Data | RCSBDataTool |
| rcsb_graphql_tools | RCSB GraphQL | RCSBGraphQLTool |
| rcsb_search_tools | RCSB Search | RCSBSearchTool |
| rdkit_cheminfo_tools | RDKit Cheminformatics | RDKitCheminfoTool |
| reactome_tools | Reactome Pathways | ReactomeRESTTool |
| reactome_analysis_tools | Reactome Analysis | ReactomeAnalysisTool |
| reactome_content_tools | Reactome Content | ReactomeContentTool |
| reactome_interactors_tools | Reactome Interactors | ReactomeInteractorsTool |
| regulomedb_tools | RegulomeDB Regulatory | RegulomeDBRESTTool |
| remap_tools | ReMap Regulatory | ReMapRESTTool |
| rfam_tools | Rfam RNA Families | RfamTool |
| rhea_tools | Rhea Reactions | RheaTool |
| rnacentral_tools | RNAcentral | RNAcentralSearchTool, RNAcentralGetTool |
| rxnorm_tools | RxNorm Drug Names | RxNormTool |
| sabdab_tools | SAbDab Antibody Structure | SAbDabTool |
| sasbdb_tools | SASBDB Small-Angle Scattering | SASBDBRESTTool, SASBDBSearchTool |
| screen_tools | ENCODE SCREEN cCREs | SCREENRESTTool |
| semantic_scholar_tools | Semantic Scholar | SemanticScholarTool, SemanticScholarPDFSnippetsTool |
| sgd_tools | SGD Yeast Genome | SGDTool |
| sider_tools | SIDER Drug Side Effects | SiderTool |
| simbad_tools | SIMBAD Astronomical | SIMBADTool, SIMBADAdvancedTool |
| spliceai_tools | SpliceAI Splicing | SpliceAITool |
| stitch_tools | STITCH Chemical-Protein | STITCHTool |
| string_tools | STRING Protein Networks | STRINGRESTTool |
| string_ext_tools | STRING Extended | STRINGExtTool |
| survival_tools | Survival Analysis | SurvivalTool |
| swissadme_tools | SwissADME Drug Properties | SwissADMETool |
| swissdock_tools | SwissDock Docking | SwissDockTool |
| swissmodel_tools | SWISS-MODEL Homology | SwissModelTool |
| swiss_target_tools | SwissTargetPrediction | SwissTargetTool |
| synbiohub_tools | SynBioHub Synthetic Bio | SynBioHubTool |
| synergxdb_tools | SYNERGxDB Drug Synergy | SYNERGxDBTool |
| therasabdab_tools | TheraSAbDab Therapeutic Ab | TheraSAbDabTool |
| three_d_beacons_tools | 3D-Beacons Structure | ThreeDBeaconsTool |
| timer_tools | TIMER Immune Infiltration | TIMERTool |
| ucsc_genome_tools | UCSC Genome Browser | UCSCGenomeTool |
| umls_tools | UMLS Metathesaurus | UMLSRESTTool |
| unichem_tools | UniChem Chemical Mapping | UniChemTool |
| unified_guideline_tools | Unified Clinical Guidelines | WHO, NICE, SIGN, GIN, CTFPHC, CMA, TRIP, EuropePMC, PubMed, OpenAlex guidelines |
| uniparc_tools | UniParc Sequence Archive | UniParcTool |
| uniprot_tools | UniProt Protein KB | UniProtRESTTool |
| uniprot_idmapping_tools | UniProt ID Mapping | UniProtIDMappingTool |
| uniprot_locations_tools | UniProt Subcellular Locations | UniProtLocationsTool |
| uniprot_ref_tools | UniProt References | UniProtRefTool |
| uniprot_taxonomy_tools | UniProt Taxonomy | UniProtTaxonomyTool |
| uniref_tools | UniRef Clusters | UniRefTool |
| unpaywall_tools | Unpaywall Open Access | UnpaywallTool |
| uspto_tools | USPTO Patent Data | USPTOOpenDataPortalTool |
| vdjdb_tools | VDJdb TCR Specificity | VDJDBTool |
| wfgy_promptbundle_tools | WFGY Prompt Bundles | WFGYPromptBundleTool |
| who_gho_tools | WHO Global Health Observatory | WHOGHORESTTool, WHOGHOTopicTool, WHOGHOStatisticTool, WHOGHOQueryTool |
| wikidata_sparql_tools | Wikidata SPARQL | WikidataSPARQLTool |
| wikipathways_tools | WikiPathways | WikiPathwaysSearchTool, WikiPathwaysGetTool |
| wikipathways_ext_tools | WikiPathways Extended | WikiPathwaysExtTool |
| wikipedia_tools | Wikipedia | WikipediaSearchTool, WikipediaSummaryTool, WikipediaContentTool |
| wormbase_tools | WormBase Nematode Genomics | WormBaseTool |
| worms_tools | WoRMS Marine Species | WoRMSRESTTool |
| xml_tools | XML Data Processing | XMLTool, XMLDatasetTool |
| zenodo_tools | Zenodo Open Repository | ZenodoRESTTool |
| zinc_tools | ZINC Chemical Library | ZINCTool, ZincTool |

**Additional tool configs (environment/earth/space/misc):**

| Tool Config | Domain | Description |
|---|---|---|
| ceda_tools | Climate | CEDA Environmental Data Archive |
| col_tools | Taxonomy | Catalogue of Life |
| cod_crystal_tools | Crystallography | Crystallography Open Database |
| datacite_tools | Research Data | DataCite DOI Registry |
| dataone_tools | Environmental Data | DataONE Environmental Repository |
| dataverse_tools | Research Data | Dataverse Research Data |
| dryad_tools | Research Data | Dryad Digital Repository |
| erddap_tools | Oceanography | ERDDAP Scientific Data Server |
| eurostat_tools | Statistics | Eurostat European Statistics |
| ebird_taxonomy_tools | Ornithology | eBird Taxonomy |
| federal_register_tools | Government | US Federal Register |
| flybase_tools | Genetics | FlyBase Drosophila Genome |
| flymine_tools | Genetics | FlyMine Drosophila Data |
| fpbase_tools | Fluorescence | FPbase Fluorescent Proteins |
| gbif_ext_tools | Biodiversity | GBIF Extended |
| genenetwork_tools | Genetics | GeneNetwork Systems Genetics |
| github_tools | Development | GitHub Repository |
| huggingface_tools | AI/ML | Hugging Face Models |
| humanmine_tools | Genomics | HumanMine Genomic Data |
| idigbio_tools | Biodiversity | iDigBio Specimen Records |
| idr_tools | Imaging | Image Data Resource |
| inspirehep_tools | Physics | INSPIRE-HEP Literature |
| jpl_horizons_tools | Astronomy | JPL Horizons Ephemeris |
| klifs_tools | Kinases | KLIFS Kinase-Ligand |
| litvar_tools | Genetics | LitVar Literature Variants |
| lncrna_tools | Genomics | lncRNA Database |
| lotus_tools | Chemistry | LOTUS Natural Products |
| marine_regions_tools | Oceanography | Marine Regions Gazetteer |
| massbank_tools | Chemistry | MassBank Mass Spectra |
| medrxiv_tools | Preprints | medRxiv Medical Preprints |
| metnorway_tools | Meteorology | MET Norway Weather |
| mibig_tools | Microbiology | MIBiG Biosynthetic Gene Clusters |
| modeldb_tools | Neuroscience | ModelDB Computational Models |
| mondo_tools | Ontology | Mondo Disease Ontology |
| mousemine_tools | Genetics | MouseMine Mouse Genome |
| msigdb_tools | Genomics | MSigDB Gene Sets |
| nasa_cmr_tools | Space | NASA Common Metadata Repository |
| nasa_donki_tools | Space | NASA Space Weather |
| nasa_eonet_tools | Earth Science | NASA Natural Events |
| nasa_exoplanet_tools | Astronomy | NASA Exoplanet Archive |
| nasa_ned_tools | Astronomy | NED Extragalactic Database |
| nasa_sbdb_tools | Astronomy | NASA Small Body Database |
| nci_drugdict_tools | Oncology | NCI Drug Dictionary |
| neurovault_tools | Neuroscience | NeuroVault Brain Imaging |
| nominatim_tools | Geography | Nominatim Geocoding |
| nws_tools | Weather | NWS Weather Data |
| omicsdi_tools | Omics | OmicsDI Multi-Omics Discovery |
| opencitations_tools | Literature | OpenCitations Citation Data |
| openfoodfacts_tools | Nutrition | Open Food Facts |
| open_meteo_tools | Weather | Open-Meteo Weather API |
| open_meteo_airquality_tools | Environment | Open-Meteo Air Quality |
| open_meteo_climate_tools | Climate | Open-Meteo Climate Change |
| open_meteo_flood_tools | Environment | Open-Meteo Flood Forecasting |
| open_meteo_marine_tools | Oceanography | Open-Meteo Marine Forecast |
| openml_tools | AI/ML | OpenML Machine Learning |
| opentopodata_tools | Geography | Open Topo Data Elevation |
| panelapp_tools | Genetics | Genomics England PanelApp |
| pdb_redo_tools | Structural Biology | PDB-REDO Refined Structures |
| pharmvar_tools | Pharmacogenomics | PharmVar Allele Database |
| powo_tools | Botany | Plants of the World Online |
| scite_tools | Literature | scite Citation Analysis |
| sdss_tools | Astronomy | SDSS Sky Survey |
| soilgrids_tools | Earth Science | SoilGrids Global Soil |
| sunrise_sunset_tools | Astronomy | Sunrise/Sunset Times |
| targetmine_tools | Drug Discovery | TargetMine Integrated Data |
| tcia_tools | Imaging | TCIA Cancer Imaging |
| txagent_client_tools | Agent | TxAgent Client |
| uscensus_tools | Demographics | US Census Data |
| usgs_earthquake_tools | Geophysics | USGS Earthquake Data |
| usgs_water_tools | Hydrology | USGS Water Data |
| variant_validator_tools | Genetics | VariantValidator |
| veupathdb_tools | Parasitology | VEuPathDB Eukaryotic Pathogens |
| waqi_tools | Environment | World Air Quality Index |
| worldbank_tools | Economics | World Bank Data |
| zfin_tools | Genetics | ZFIN Zebrafish Genome |

---

## 2. K-Dense AI (claude-scientific-skills)

**170+ skills across 17 categories, accessing 250+ databases/data sources.**

### 2.1 Bioinformatics & Genomics

| Skill Name | Category | Description |
|---|---|---|
| biopython | Bioinformatics | Sequence analysis, alignment, BLAST, phylogenetics |
| pysam | Genomics | BAM/CRAM/VCF file reading and manipulation |
| scikit-bio | Bioinformatics | Biological sequence analysis and diversity calculations |
| bioservices | Bioinformatics | Access to biological web services (UniProt, KEGG, etc.) |
| scanpy | Single-Cell | Single-cell RNA-seq analysis framework |
| anndata | Data Structure | Annotated data matrices for omics data |
| scvi-tools | Single-Cell | Deep learning for single-cell omics analysis |
| scvelo | Single-Cell | RNA velocity analysis for single-cell data |
| arboreto | Gene Networks | Gene regulatory network inference (GRNBoost2, GENIE3) |
| cellxgene-census | Single-Cell | CZ CELLxGENE Census data access |
| gget | Bioinformatics | Gene and sequence information retrieval |
| geniml | Genomics | Genomic interval machine learning |
| gtars | Genomics | Genomic tool for annotation and region search |
| deeptools | Epigenomics | Deep sequencing data analysis and visualization |
| flowio | Flow Cytometry | FCS file reading for flow cytometry data |
| zarr-python | Data Format | Chunked compressed N-dimensional arrays |
| tiledbvcf | Genomics | Variant call format database management |
| etetoolkit | Phylogenetics | Phylogenetic tree analysis and visualization |
| phylogenetics | Phylogenetics | MAFFT, IQ-TREE 2, FastTree phylogenetic analysis |
| polars-bio | Bioinformatics | High-performance bioinformatics data operations |

### 2.2 Cheminformatics & Drug Discovery

| Skill Name | Category | Description |
|---|---|---|
| rdkit | Cheminformatics | Open-source cheminformatics and machine learning |
| datamol | Cheminformatics | Molecular manipulation and featurization |
| molfeat | Molecular Features | Molecular featurization for ML models |
| deepchem | Drug Discovery | Deep learning for drug discovery and materials |
| torchdrug | Drug Discovery | Drug discovery with graph neural networks |
| diffdock | Molecular Docking | Diffusion-based molecular docking |
| molecular-dynamics | Simulation | OpenMM and MDAnalysis molecular dynamics |
| rowan | Quantum Chemistry | Quantum chemistry computations |
| medchem | Medicinal Chemistry | Medicinal chemistry filters and rules |
| bindingdb-database | Database | Measured binding affinity data |
| pytdc | Drug Discovery | Therapeutics Data Commons benchmark access |

### 2.3 Proteomics & Mass Spectrometry

| Skill Name | Category | Description |
|---|---|---|
| matchms | Mass Spectrometry | Mass spectra processing and similarity scoring |
| pyopenms | Proteomics | Mass spectrometry data processing (OpenMS) |

### 2.4 Clinical Research & Precision Medicine

| Skill Name | Category | Description |
|---|---|---|
| clinicaltrials-database | Clinical | ClinicalTrials.gov data access and search |
| clinvar-database | Genetics | ClinVar clinical variant interpretation |
| clinpgx-database | Pharmacogenomics | Clinical pharmacogenomics annotations |
| cosmic-database | Cancer | COSMIC somatic mutation data |
| fda-database | Regulatory | FDA drug approval and label data |
| cbioportal-database | Cancer Genomics | cBioPortal cancer genomics data |
| depmap | Cancer | Cancer Dependency Map data access |
| monarch-database | Disease | Monarch Initiative disease-gene associations |
| imaging-data-commons | Medical Imaging | NCI Imaging Data Commons access |
| pyhealth | Health ML | Machine learning for healthcare data |
| neurokit2 | Neurophysiology | Neurophysiological signal processing |
| clinical-decision-support | Clinical | Clinical decision support systems |
| clinical-reports | Clinical | Clinical report generation |
| treatment-plans | Clinical | Treatment plan creation |
| ensembl-database | Genomics | Ensembl genome annotation access |
| gene-database | Genomics | NCBI Gene database access |

### 2.5 Medical Imaging & Digital Pathology

| Skill Name | Category | Description |
|---|---|---|
| pydicom | Medical Imaging | DICOM medical imaging file handling |
| histolab | Digital Pathology | Histological slide analysis and preprocessing |
| pathml | Digital Pathology | Digital pathology analysis framework |

### 2.6 Neuroscience

| Skill Name | Category | Description |
|---|---|---|
| neuropixels-analysis | Neuroscience | Neuropixels high-density neural probe data analysis |

### 2.7 Machine Learning & AI

| Skill Name | Category | Description |
|---|---|---|
| pytorch-lightning | Deep Learning | PyTorch training framework |
| transformers | NLP/ML | Hugging Face transformers library |
| stable-baselines3 | RL | Reinforcement learning algorithms |
| pufferlib | RL | PufferFish reinforcement learning framework |
| scikit-learn | ML | General machine learning algorithms |
| scikit-survival | ML | Survival analysis with machine learning |
| shap | ML Interpretability | SHAP model explanation values |
| aeon | Time Series | Time series classification and analysis |
| timesfm-forecasting | Forecasting | TimesFM time series foundation model |
| pymc | Bayesian | Bayesian statistical modeling |
| pymoo | Optimization | Multi-objective optimization |
| torch-geometric | Graph ML | Geometric deep learning on graphs |
| umap-learn | Dimensionality Reduction | UMAP dimensionality reduction |
| statsmodels | Statistics | Statistical modeling and econometrics |
| hypogenic | Hypothesis | Automated hypothesis generation |

### 2.8 Materials Science, Chemistry & Physics

| Skill Name | Category | Description |
|---|---|---|
| pymatgen | Materials Science | Materials analysis and crystal structure |
| cobrapy | Metabolic Modeling | Constraint-based metabolic modeling |
| astropy | Astronomy | Astronomical computations and data |
| cirq | Quantum Computing | Google quantum circuit simulation |
| pennylane | Quantum ML | Quantum machine learning framework |
| qiskit | Quantum Computing | IBM quantum computing SDK |
| qutip | Quantum Physics | Quantum dynamics simulation |

### 2.9 Engineering & Simulation

| Skill Name | Category | Description |
|---|---|---|
| matlab | Numerical Computing | MATLAB/Octave numerical analysis |
| fluidsim | Fluid Dynamics | Computational fluid dynamics simulation |
| simpy | Discrete Event Simulation | Process-based discrete event simulation |
| dask | Parallel Computing | Parallel computing and big data processing |
| polars | Data Processing | Fast DataFrame library |
| vaex | Big Data | Out-of-core DataFrame for billion rows |

### 2.10 Data Analysis & Visualization

| Skill Name | Category | Description |
|---|---|---|
| matplotlib | Visualization | Publication-quality plotting |
| seaborn | Visualization | Statistical data visualization |
| plotly | Visualization | Interactive plots and dashboards |
| scientific-visualization | Visualization | Specialized scientific figure generation |
| geopandas | Geospatial | Geospatial data analysis |
| geomaster | Geospatial | Geographic data processing |
| networkx | Graph Analysis | Network and graph theory analysis |
| sympy | Symbolic Math | Symbolic mathematics |
| docx | Document | Word document generation |
| xlsx | Document | Excel spreadsheet generation |
| pdf | Document | PDF document processing |
| pptx | Document | PowerPoint generation |
| infographics | Communication | Scientific infographic creation |
| markdown-mermaid-writing | Communication | Markdown and Mermaid diagram writing |
| datacommons-client | Data Access | Google Data Commons access |
| exploratory-data-analysis | Analysis | EDA workflow automation |
| statistical-analysis | Analysis | Statistical analysis pipelines |

### 2.11 Laboratory Automation

| Skill Name | Category | Description |
|---|---|---|
| pylabrobot | Lab Robotics | Python for laboratory robotics (Hamilton, Opentrons) |
| ginkgo-cloud-lab | Cloud Lab | Ginkgo Bioworks cloud laboratory platform |
| protocolsio-integration | Protocols | Protocols.io method sharing integration |
| benchling-integration | LIMS | Benchling lab information management |
| labarchive-integration | ELN | LabArchives electronic lab notebook |
| opentrons-integration | Liquid Handling | Opentrons liquid handling robots |

### 2.12 Multi-omics & Systems Biology

| Skill Name | Category | Description |
|---|---|---|
| kegg-database | Pathways | KEGG pathway and molecular interaction data |
| reactome-database | Pathways | Reactome biological pathway data |
| string-database | Protein Networks | STRING protein-protein interaction data |
| denario | Data | Scientific data access and sharing |
| lamindb | Data Management | Biological data lake management |
| primekg | Knowledge Graph | Precision Medicine Knowledge Graph |

### 2.13 Protein Engineering & Design

| Skill Name | Category | Description |
|---|---|---|
| esm | Protein Language Model | Meta ESM protein language models |
| glycoengineering | Glycobiology | Glycan engineering and analysis |
| adaptyv | Protein Design | Adaptyv Bio protein design validation |

### 2.14 Scientific Communication

| Skill Name | Category | Description |
|---|---|---|
| openalex-database | Literature | OpenAlex scholarly metadata |
| pubmed-database | Literature | PubMed biomedical literature search |
| biorxiv-database | Preprints | bioRxiv preprint access |
| literature-review | Research | Systematic literature review automation |
| bgpt-paper-search | Literature | BioGPT-powered paper search |
| perplexity-search | Web Search | Perplexity AI-powered web search |
| parallel-web | Web Search | Parallel web content fetching |
| open-notebook | Research | Open notebook science documentation |
| scientific-writing | Writing | Scientific manuscript drafting |
| peer-review | Writing | Peer review report generation |
| markitdown | Document | Document format conversion |
| paper-2-web | Communication | Paper to web page conversion |
| venue-templates | Writing | Journal submission templates |
| scientific-slides | Presentation | Scientific presentation slides |
| latex-posters | Communication | LaTeX scientific poster creation |
| pptx-posters | Communication | PowerPoint poster creation |
| scientific-schematics | Diagrams | Scientific schematic diagrams |
| citation-management | References | Citation management (Zotero integration) |
| generate-image | Imaging | AI image generation for science |
| writing | Writing | General scientific writing assistance |
| pyzotero | References | Zotero API access for reference management |

### 2.15 Scientific Databases

| Skill Name | Category | Description |
|---|---|---|
| uniprot-database | Protein | UniProt protein knowledgebase |
| pdb-database | Structural Biology | Protein Data Bank 3D structures |
| alphafold-database | Structural Biology | AlphaFold predicted structures |
| interpro-database | Protein | InterPro protein families and domains |
| pubchem-database | Chemistry | PubChem chemical information |
| chembl-database | Drug Discovery | ChEMBL bioactivity data |
| drugbank-database | Pharmacology | DrugBank drug and target data |
| zinc-database | Chemistry | ZINC commercially available compounds |
| hmdb-database | Metabolomics | Human Metabolome Database |
| ena-database | Genomics | European Nucleotide Archive |
| gwas-database | Genetics | GWAS Catalog associations |
| gnomad-database | Population Genetics | gnomAD population variant frequencies |
| gtex-database | Expression | GTEx tissue expression data |
| jaspar-database | Genomics | JASPAR transcription factor binding profiles |
| opentargets-database | Drug Discovery | Open Targets disease-target associations |
| metabolomics-workbench-database | Metabolomics | Metabolomics Workbench repository |
| brenda-database | Enzymology | BRENDA enzyme functional data |
| uspto-database | Patents | USPTO patent data access |
| geo-database | Genomics | GEO gene expression data |
| arxiv-database | Preprints | arXiv preprint search |

### 2.16 Research Methodology & Planning

| Skill Name | Category | Description |
|---|---|---|
| scientific-brainstorming | Ideation | Structured scientific brainstorming |
| hypothesis-generation | Research | Automated hypothesis generation |
| scientific-critical-thinking | Analysis | Scientific critical thinking framework |
| scholar-evaluation | Assessment | Scholar and paper evaluation |
| what-if-oracle | Analysis | What-if scenario analysis |
| consciousness-council | Decision | Multi-perspective decision making |
| dhdna-profiler | Analysis | DHDNA profiler analysis |
| research-grants | Funding | Research grant identification |
| research-lookup | Research | Research topic discovery |
| market-research-reports | Business | Market research report generation |

### 2.17 Infrastructure & Platforms

| Skill Name | Category | Description |
|---|---|---|
| modal | Cloud Compute | Modal serverless GPU computing |
| dnanexus-integration | Genomics Cloud | DNAnexus genomics cloud platform |
| latchbio-integration | Bioinformatics Cloud | Latch bioinformatics platform |
| omero-integration | Bio-Imaging | OMERO bio-image data management |
| get-available-resources | Discovery | List available skills and resources |
| offer-k-dense-web | Platform | K-Dense web service offerings |

### 2.18 Regulatory & Financial

| Skill Name | Category | Description |
|---|---|---|
| iso-13485-certification | Regulatory | ISO 13485 medical device quality management |
| edgartools | Finance | SEC EDGAR financial filings |
| usfiscaldata | Finance | US fiscal and treasury data |
| fred-economic-data | Economics | FRED economic time series data |
| hedgefundmonitor | Finance | Hedge fund performance monitoring |
| alpha-vantage | Finance | Stock market and financial data |

---

## 3. Biomni (snap-stanford/Biomni)

**155+ tools across 18 domains + 33 database connectors + 90+ data lake datasets.**

### 3.1 Biochemistry (6 tools)

| Tool Name | Category | Description |
|---|---|---|
| analyze_circular_dichroism_spectra | Spectroscopy | Analyzes CD spectra for secondary structure and thermal stability |
| analyze_rna_secondary_structure_features | RNA Analysis | Calculates structural features of RNA secondary structure |
| analyze_protease_kinetics | Enzymology | Analyzes protease kinetics from fluorogenic peptide assays |
| analyze_enzyme_kinetics_assay | Enzymology | In vitro enzyme kinetics assay with dose-dependent modulator analysis |
| analyze_itc_binding_thermodynamics | Biophysics | ITC data analysis for binding affinity and thermodynamics |
| analyze_protein_conservation | Evolutionary Biology | Multiple sequence alignment and phylogenetic analysis for conserved regions |

### 3.2 Bioengineering (7 tools)

| Tool Name | Category | Description |
|---|---|---|
| analyze_cell_migration_metrics | Cell Biology | Cell migration analysis from time-lapse microscopy |
| perform_crispr_cas9_genome_editing | Genome Editing | Simulates CRISPR-Cas9 editing including gRNA design and analysis |
| analyze_calcium_imaging_data | Neuroscience | Calcium imaging analysis for neuronal activity metrics |
| analyze_in_vitro_drug_release_kinetics | Drug Delivery | Drug release kinetics analysis from biomaterial formulations |
| analyze_myofiber_morphology | Tissue Analysis | Myofiber morphological quantification from microscopy |
| decode_behavior_from_neural_trajectories | Neuroscience | Neural trajectory modeling and behavioral decoding |
| simulate_whole_cell_ode_model | Systems Biology | Whole-cell ODE model simulation |

### 3.3 Bioimaging (10 tools)

| Tool Name | Category | Description |
|---|---|---|
| split_modalities | Medical Imaging | Splits 4D NIfTI files into separate modality files |
| prepare_input_for_nnunet | Medical Imaging | Prepares input data for nnUNet segmentation |
| segment_with_nn_unet | Medical Imaging | nnUNet-based image segmentation |
| create_segmentation_visualization | Medical Imaging | Segmentation result visualization with nilearn |
| quick_rigid_registration | Image Registration | Rigid (translation+rotation) image registration |
| quick_affine_registration | Image Registration | Affine image registration (translate, rotate, scale, shear) |
| quick_deformable_registration | Image Registration | B-spline deformable image registration |
| batch_register_images | Image Registration | Batch registration to a reference image |
| calculate_similarity_metrics | Image Analysis | Multi-metric image similarity evaluation |
| create_registration_visualization | Image Registration | Registration result visualization |

### 3.4 Biophysics (3 tools)

| Tool Name | Category | Description |
|---|---|---|
| predict_protein_disorder_regions | Protein Analysis | Intrinsically disordered region prediction using IUPred2A |
| analyze_cell_morphology_and_cytoskeleton | Cell Biology | Cell morphology and cytoskeletal organization quantification |
| analyze_tissue_deformation_flow | Tissue Mechanics | Tissue deformation and flow dynamics quantification |

### 3.5 Cancer Biology (6 tools)

| Tool Name | Category | Description |
|---|---|---|
| analyze_ddr_network_in_cancer | DNA Repair | DDR network alterations and dependencies in cancer |
| analyze_cell_senescence_and_apoptosis | Cell Biology | Flow cytometry analysis for senescent and apoptotic cells |
| detect_and_annotate_somatic_mutations | Cancer Genomics | Somatic mutation detection with GATK Mutect2 and SnpEff |
| detect_and_characterize_structural_variations | Cancer Genomics | Structural variation detection with LUMPY |
| perform_gene_expression_nmf_analysis | Cancer Genomics | NMF on gene expression for tumor classification |
| analyze_copy_number_purity_ploidy_and_focal_events | Cancer Genomics | CNVkit copy number analysis with purity/ploidy estimation |

### 3.6 Cell Biology (5 tools)

| Tool Name | Category | Description |
|---|---|---|
| quantify_cell_cycle_phases_from_microscopy | Cell Cycle | Cell cycle phase quantification from Calcofluor staining |
| quantify_and_cluster_cell_motility | Cell Motility | Cell motility feature quantification and clustering |
| perform_facs_cell_sorting | Flow Cytometry | FACS simulation for cell population enrichment |
| analyze_flow_cytometry_immunophenotyping | Flow Cytometry | Flow cytometry immunophenotyping analysis |
| analyze_mitochondrial_morphology_and_potential | Cell Biology | Mitochondrial morphology and membrane potential quantification |

### 3.7 Genetics (9 tools)

| Tool Name | Category | Description |
|---|---|---|
| liftover_coordinates | Genome Coordinates | Liftover between hg19 and hg38 |
| bayesian_finemapping_with_deep_vi | Statistical Genetics | Bayesian fine-mapping with deep variational inference |
| analyze_cas9_mutation_outcomes | CRISPR | Cas9-induced mutation categorization |
| analyze_crispr_genome_editing | CRISPR | CRISPR-Cas9 editing result evaluation |
| simulate_demographic_history | Population Genetics | Demographic simulation with msprime |
| identify_transcription_factor_binding_sites | Regulatory Genomics | TF binding site identification in genomic sequences |
| fit_genomic_prediction_model | Genomic Prediction | Linear mixed model for genotype-phenotype prediction |
| perform_pcr_and_gel_electrophoresis | Molecular Biology | PCR amplification and gel electrophoresis simulation |
| analyze_protein_phylogeny | Evolutionary Biology | Protein sequence alignment and phylogenetic tree construction |

### 3.8 Genomics (19 tools)

| Tool Name | Category | Description |
|---|---|---|
| annotate_celltype_scRNA | Single-Cell | Cell type annotation using gene markers and LLM |
| annotate_celltype_with_panhumanpy | Single-Cell | Cell type annotation with Panhuman Azimuth Neural Network |
| create_scvi_embeddings_scRNA | Single-Cell | scVI and scANVI embeddings for single-cell RNA-seq |
| create_harmony_embeddings_scRNA | Single-Cell | Harmony batch integration for scRNA-seq |
| get_uce_embeddings_scRNA | Single-Cell | UCE embeddings with reference dataset mapping |
| map_to_ima_interpret_scRNA | Single-Cell | IMA reference mapping using UCE embeddings |
| get_rna_seq_archs4 | Transcriptomics | RNA-seq expression data from ARCHS4 |
| get_gene_set_enrichment_analysis_supported_database_list | Enrichment | Lists supported enrichment analysis databases |
| gene_set_enrichment_analysis | Enrichment | Gene set enrichment analysis with visualization |
| analyze_chromatin_interactions | Epigenomics | Hi-C data analysis for enhancer-promoter interactions and TADs |
| analyze_comparative_genomics_and_haplotypes | Comparative Genomics | Cross-genome comparative analysis and haplotyping |
| perform_chipseq_peak_calling_with_macs2 | ChIP-seq | ChIP-seq peak calling with MACS2 |
| find_enriched_motifs_with_homer | Motif Discovery | DNA motif enrichment analysis with HOMER |
| analyze_genomic_region_overlap | Genomic Analysis | Multi-region overlap analysis |
| unsupervised_celltype_transfer_between_scRNA_datasets | Single-Cell | Cell type label transfer using popV |
| generate_embeddings_with_state | Single-Cell | State SE-600M embeddings for scRNA-seq |
| interspecies_gene_conversion | Comparative Genomics | ENSEMBL gene ID conversion via BioMart homology |
| generate_gene_embeddings_with_ESM_models | Protein ML | ESM protein embeddings for genes |
| generate_transcriptformer_embeddings | Single-Cell | Transformer-based scRNA-seq embeddings |

### 3.9 Glycoengineering (3 tools)

| Tool Name | Category | Description |
|---|---|---|
| find_n_glycosylation_motifs | Glycobiology | N-glycosylation sequon scanning |
| predict_o_glycosylation_hotspots | Glycobiology | O-glycosylation hotspot prediction |
| list_glycoengineering_resources | Glycobiology | Curated glycoengineering tool and resource list |

### 3.10 Immunology (10 tools)

| Tool Name | Category | Description |
|---|---|---|
| analyze_atac_seq_differential_accessibility | Epigenomics | ATAC-seq peak calling and differential accessibility |
| analyze_bacterial_growth_curve | Microbiology | Bacterial growth metric determination |
| isolate_purify_immune_cells | Immunology | Immune cell isolation and purification simulation |
| estimate_cell_cycle_phase_durations | Cell Biology | Cell cycle phase timing estimation from pulse labeling |
| track_immune_cells_under_flow | Immunology | Immune cell tracking and behavior classification under flow |
| analyze_cfse_cell_proliferation | Immunology | CFSE-labeled cell proliferation quantification |
| analyze_cytokine_production_in_cd4_tcells | Immunology | CD4+ T cell cytokine production analysis |
| analyze_ebv_antibody_titers | Immunology | EBV antibody titer quantification from ELISA |
| analyze_cns_lesion_histology | Neuropathology | CNS immune infiltration and demyelination quantification |
| analyze_immunohistochemistry_image | Pathology | IHC image protein expression quantification |

### 3.11 Lab Automation (3 tools)

| Tool Name | Category | Description |
|---|---|---|
| test_pylabrobot_script | Lab Robotics | PyLabRobot script testing |
| get_pylabrobot_documentation_liquid | Lab Robotics | PyLabRobot liquid handling documentation |
| get_pylabrobot_documentation_material | Lab Robotics | PyLabRobot material handling documentation |

### 3.12 Literature (8 tools)

| Tool Name | Category | Description |
|---|---|---|
| fetch_supplementary_info_from_doi | Literature | Fetches supplementary information by DOI |
| query_arxiv | Literature | arXiv paper search |
| query_scholar | Literature | Google Scholar paper search |
| query_pubmed | Literature | PubMed paper search |
| search_google | Web | Google web search |
| extract_url_content | Web | Webpage text content extraction |
| extract_pdf_content | Document | PDF text content extraction |
| advanced_web_search_claude | Web Research | Multi-search agent for information and citations |

### 3.13 Microbiology (12 tools)

| Tool Name | Category | Description |
|---|---|---|
| optimize_anaerobic_digestion_process | Bioprocess | Anaerobic digestion optimization for VFA/methane |
| analyze_arsenic_speciation_hplc_icpms | Analytical Chemistry | Arsenic speciation via HPLC-ICP-MS |
| count_bacterial_colonies | Microbiology | Colony counting from agar plate images |
| annotate_bacterial_genome | Genomics | Bacterial genome annotation with Prokka |
| enumerate_bacterial_cfu_by_serial_dilution | Microbiology | CFU quantification by serial dilution |
| model_bacterial_growth_dynamics | Modeling | Bacterial population dynamics ODE modeling |
| quantify_biofilm_biomass_crystal_violet | Microbiology | Biofilm biomass quantification by crystal violet |
| segment_and_analyze_microbial_cells | Microscopy | Automated microbial cell segmentation and morphometry |
| segment_cells_with_deep_learning | Microscopy | Deep learning cell segmentation from fluorescence |
| simulate_generalized_lotka_volterra_dynamics | Ecology | Microbial community GLV dynamics simulation |
| predict_rna_secondary_structure | RNA Biology | RNA secondary structure prediction with ViennaRNA |
| simulate_microbial_population_dynamics | Modeling | Stochastic microbial population simulation (Gillespie) |

### 3.14 Molecular Biology (18 tools)

| Tool Name | Category | Description |
|---|---|---|
| annotate_open_reading_frames | Sequence Analysis | ORF identification in DNA sequences |
| annotate_plasmid | Cloning | DNA annotation with pLannotate |
| get_gene_coding_sequence | Sequence Retrieval | Coding sequence retrieval from NCBI |
| get_plasmid_sequence | Cloning | Plasmid sequence retrieval from Addgene/NCBI |
| align_sequences | Sequence Analysis | Short sequence alignment with mismatch tolerance |
| pcr_simple | Molecular Biology | PCR amplification simulation |
| digest_sequence | Molecular Biology | Restriction enzyme digestion simulation |
| find_restriction_sites | Molecular Biology | Restriction site identification |
| find_restriction_enzymes | Molecular Biology | Common restriction enzyme recognition site search |
| find_sequence_mutations | Sequence Analysis | DNA sequence difference identification |
| design_knockout_sgrna | CRISPR | CRISPR guide RNA design for gene knockout |
| get_oligo_annealing_protocol | Protocols | Oligonucleotide annealing protocol |
| get_golden_gate_assembly_protocol | Protocols | Golden Gate assembly protocol generation |
| get_bacterial_transformation_protocol | Protocols | Bacterial transformation protocol |
| design_primer | Primer Design | Individual primer design with parameter constraints |
| design_verification_primers | Primer Design | Sanger sequencing primer design for plasmid verification |
| design_golden_gate_oligos | Cloning | Golden Gate complementary oligonucleotide design |
| golden_gate_assembly | Cloning | Golden Gate assembly construct prediction |

### 3.15 Pathology (7 tools)

| Tool Name | Category | Description |
|---|---|---|
| analyze_aortic_diameter_and_geometry | Cardiovascular | Aortic geometry measurement from cardiovascular imaging |
| analyze_atp_luminescence_assay | Cell Biology | ATP luminescence assay analysis |
| analyze_thrombus_histology | Hematology | H&E thrombus histology component quantification |
| analyze_intracellular_calcium_with_rhod2 | Cell Biology | Rhod-2 calcium indicator microscopy analysis |
| quantify_corneal_nerve_fibers | Ophthalmology | Corneal nerve fiber density quantification |
| segment_and_quantify_cells_in_multiplexed_images | Spatial Biology | Multichannel tissue cell segmentation and protein quantification |
| analyze_bone_microct_morphometry | Musculoskeletal | Bone microarchitecture analysis from micro-CT |

### 3.16 Pharmacology (25 tools)

| Tool Name | Category | Description |
|---|---|---|
| run_diffdock_with_smiles | Molecular Docking | DiffDock docking with SMILES input |
| docking_autodock_vina | Molecular Docking | AutoDock Vina binding affinity prediction |
| run_autosite | Binding Site | Protein binding site identification |
| retrieve_topk_repurposing_drugs_from_disease_txgnn | Drug Repurposing | TxGNN disease-based drug repurposing prediction |
| predict_admet_properties | ADMET | ADMET property computation for compounds |
| predict_binding_affinity_protein_1d_sequence | Binding Prediction | Deep learning protein-ligand binding affinity |
| analyze_accelerated_stability_of_pharmaceutical_formulations | Formulation | Pharmaceutical formulation stability evaluation |
| run_3d_chondrogenic_aggregate_assay | Assay Protocol | 3D chondrogenic culture assay protocol |
| grade_adverse_events_using_vcog_ctcae | Veterinary | VCOG-CTCAE adverse event grading |
| analyze_radiolabeled_antibody_biodistribution | Radiopharmacy | Radiolabeled antibody PK and biodistribution |
| estimate_alpha_particle_radiotherapy_dosimetry | Dosimetry | Alpha-particle radiotherapy dose calculation |
| perform_mwas_cyp2c19_metabolizer_status | Pharmacogenomics | CYP2C19 methylome-wide association |
| calculate_physicochemical_properties | Medicinal Chemistry | Drug candidate physicochemical property computation |
| analyze_xenograft_tumor_growth_inhibition | Oncology | Xenograft tumor growth inhibition evaluation |
| analyze_pixel_distribution | Image Analysis | Western blot pixel intensity statistics |
| find_roi_from_image | Image Analysis | Protein band ROI detection from gels |
| analyze_western_blot | Image Analysis | Western blot densitometric analysis |
| query_drug_interactions | Drug Safety | DDInter drug interaction retrieval |
| check_drug_combination_safety | Drug Safety | Drug combination safety assessment |
| analyze_interaction_mechanisms | Drug Safety | Drug-drug interaction mechanism analysis |
| find_alternative_drugs_ddinter | Drug Safety | Alternative drug identification without interactions |
| query_fda_adverse_events | Pharmacovigilance | OpenFDA adverse event query |
| get_fda_drug_label_info | Regulatory | FDA drug label information retrieval |
| check_fda_drug_recalls | Pharmacovigilance | FDA recall and enforcement query |
| analyze_fda_safety_signals | Pharmacovigilance | Comparative drug safety pattern analysis |

### 3.17 Physiology (11 tools)

| Tool Name | Category | Description |
|---|---|---|
| reconstruct_3d_face_from_mri | Medical Imaging | 3D facial model from head/neck MRI |
| analyze_abr_waveform_p1_metrics | Audiology | ABR waveform P1 amplitude and latency extraction |
| analyze_ciliary_beat_frequency | Pulmonology | Ciliary beat frequency from high-speed video |
| analyze_protein_colocalization | Microscopy | Fluorescent protein colocalization analysis |
| perform_cosinor_analysis | Chronobiology | Circadian rhythm characterization from time series |
| calculate_brain_adc_map | Neuroimaging | Brain ADC map from diffusion-weighted MRI |
| analyze_endolysosomal_calcium_dynamics | Cell Biology | Endolysosomal calcium dynamics with ELGA probe |
| analyze_fatty_acid_composition_by_gc | Analytical Chemistry | Gas chromatography fatty acid composition |
| analyze_hemodynamic_data | Cardiovascular | Blood pressure hemodynamic parameter calculation |
| simulate_thyroid_hormone_pharmacokinetics | Endocrinology | Thyroid hormone ODE-based PK simulation |
| quantify_amyloid_beta_plaques | Neuropathology | Amyloid-beta plaque detection and quantification |

### 3.18 Synthetic Biology (8 tools)

| Tool Name | Category | Description |
|---|---|---|
| engineer_bacterial_genome_for_therapeutic_delivery | Genome Engineering | Bacterial genome engineering for therapeutics |
| analyze_bacterial_growth_rate | Microbiology | Bacterial growth parameter extraction from OD600 |
| analyze_barcode_sequencing_data | Sequencing | Barcode sequencing lineage analysis |
| analyze_bifurcation_diagram | Dynamical Systems | Bifurcation analysis and diagram generation |
| create_biochemical_network_sbml_model | Modeling | SBML biochemical network model generation |
| optimize_codons_for_heterologous_expression | Molecular Biology | Codon optimization for heterologous expression |
| simulate_gene_circuit_with_growth_feedback | Synthetic Biology | Gene circuit dynamics with growth feedback |
| identify_fas_functional_domains | Protein Analysis | FAS functional domain identification |

### 3.19 Systems Biology (7 tools)

| Tool Name | Category | Description |
|---|---|---|
| perform_flux_balance_analysis | Metabolic Modeling | FBA on metabolic network models |
| model_protein_dimerization_network | Protein Biochemistry | Protein dimer equilibrium concentration calculation |
| simulate_metabolic_network_perturbation | Metabolic Modeling | Kinetic metabolic model perturbation analysis |
| simulate_protein_signaling_network | Signal Transduction | ODE-based protein signaling dynamics with Hill functions |
| compare_protein_structures | Structural Biology | Protein structure conformational comparison |
| simulate_renin_angiotensin_system_dynamics | Physiology | RAS system component dynamics simulation |
| query_chatnt | DNA Analysis | DNA sequence function and property queries |

### 3.20 Protocols (4 tools)

| Tool Name | Category | Description |
|---|---|---|
| search_protocols | Protocol Management | Protocols.io keyword search |
| get_protocol_details | Protocol Management | Protocol metadata retrieval by ID |
| list_local_protocols | Protocol Management | Local protocol file listing |
| read_local_protocol | Protocol Management | Local protocol file reading |

### 3.21 Support Tools (3 tools)

| Tool Name | Category | Description |
|---|---|---|
| run_python_repl | Computing | Python code execution in notebook environment |
| read_function_source_code | Development | Function source code reading from any module |
| download_synapse_data | Data Access | Synapse data download by entity ID |

### 3.22 Database Connectors (33 databases)

| Database | Domain | Query Tool |
|---|---|---|
| UniProt | Protein KB | query_uniprot |
| AlphaFold DB | Protein Structure | query_alphafold |
| InterPro | Protein Families | query_interpro |
| RCSB PDB | 3D Structures | query_pdb, query_pdb_identifiers |
| KEGG | Pathways | query_kegg |
| STRING | Protein Interactions | query_stringdb |
| IUCN Red List | Conservation | query_iucn |
| Paleobiology DB | Paleontology | query_paleobiology |
| JASPAR | TF Binding Profiles | query_jaspar |
| WoRMS | Marine Species | query_worms |
| cBioPortal | Cancer Genomics | query_cbioportal |
| ClinVar | Clinical Variants | query_clinvar |
| GEO | Gene Expression | query_geo |
| dbSNP | Genetic Variants | query_dbsnp |
| UCSC Genome Browser | Genome Browsing | query_ucsc |
| Ensembl | Genome Annotation | query_ensembl |
| Open Targets | Drug Targets | query_opentarget |
| Monarch Initiative | Disease-Gene | query_monarch |
| OpenFDA | Drug Safety | query_openfda |
| GWAS Catalog | GWAS Associations | query_gwas_catalog |
| gnomAD | Population Variants | query_gnomad |
| NCBI BLAST | Sequence Similarity | blast_sequence |
| Reactome | Biological Pathways | query_reactome |
| RegulomeDB | Regulatory Variants | query_regulomedb |
| PRIDE | Proteomics | query_pride |
| GtoPdb | Pharmacology | query_gtopdb |
| ReMap | Regulatory Elements | query_remap |
| MPD | Mouse Phenome | query_mpd |
| EMDB | Electron Microscopy | query_emdb |
| Synapse | Biomedical Datasets | query_synapse |
| PubChem | Chemistry | query_pubchem |
| ChEMBL | Bioactivity | query_chembl |
| UniChem | Chemical Mapping | query_unichem |
| ClinicalTrials.gov | Clinical Trials | query_clinicaltrials |
| DailyMed | Drug Labels | query_dailymed |
| QuickGO | GO Annotations | query_quickgo |
| ENCODE | Functional Genomics | query_encode |
| ENCODE SCREEN | cCREs | region_to_ccre_screen, get_genes_near_ccre |

### 3.23 Data Lake (90+ datasets)

Bundled datasets across: protein interactions, drug discovery, cancer genomics (DepMap), drug-drug interactions (DDInter), gene-disease (DisGeNET, OMIM), gene expression (GTEx, HPA), genetic variants (GeneBass, GWAS Catalog), regulatory/miRNA, gene sets (MSigDB, MouseMine), immune/cell (McPAS-TCR, CZI Census), CRISPR (sgRNA libraries), phenotype ontology, and screening data (EveBio).

### 3.24 Software Stack

- **Python packages**: 70+ (biopython, scanpy, rdkit, deeppurpose, openmm, pytorch, etc.)
- **R packages**: 15+ (DESeq2, edgeR, limma, clusterProfiler, WGCNA, etc.)
- **CLI tools**: 25+ (samtools, bowtie2, bwa, macs2, plink, vina, etc.)

---

## 4. Anthropic Life Sciences (anthropics/life-sciences)

**21 plugins: 12 remote MCP servers + 4 local skills + 5 MCP server connectors.**

### 4.1 Remote MCP Servers

| Plugin Name | Provider | Description |
|---|---|---|
| pubmed | Anthropic | Search and access PubMed biomedical literature |
| biorxiv | deepsense.ai | Access bioRxiv and medRxiv preprint data |
| biorender | BioRender | Create and access scientific illustrations and diagrams |
| synapse | Sage Bionetworks | Collaborative research data management on Synapse.org |
| wiley-scholar-gateway | Wiley | Access Wiley academic research publications |
| chembl | deepsense.ai | ChEMBL bioactive compound database with quantitative binding data |
| clinical-trials | deepsense.ai | ClinicalTrials.gov NIH/NLM clinical study registry |
| medidata | Medidata Solutions | Platform help and predictive site ranking for clinical trials |
| open-targets | OpenTargets | Drug target discovery and prioritization platform |
| owkin | Owkin | HistoPLUS: H&E slide analysis, cell quantification, spatial TME analysis, survival analysis |
| tooluniverse | MIMS Harvard | 1000+ scientific tools via ToolUniverse MCP server |

### 4.2 Local MCP Servers

| Plugin Name | Provider | Description |
|---|---|---|
| 10x-genomics | 10x Genomics | 10x Genomics Cloud analysis data and workflows |

### 4.3 Skills

| Plugin Name | Category | Description |
|---|---|---|
| single-cell-rna-qc | Genomics | Automated scRNA-seq QC with MAD-based filtering and scverse best practices |
| instrument-data-to-allotrope | Lab Data | Convert instrument data to Allotrope Simple Model (ASM) format |
| nextflow-development | Bioinformatics | Run nf-core pipelines (rnaseq, sarek, atacseq) on sequencing data |
| scvi-tools | Single-Cell | Deep learning for single-cell omics (scVI, scANVI, totalVI, SOLO) |
| clinical-trial-protocol-skill | Clinical | Generate clinical trial protocols for devices/drugs with regulatory documentation |
| scientific-problem-selection | Research Methodology | 9 sub-skills: intuition pumps, risk assessment, optimization function, parameter strategy, decision tree navigation, adversity response, problem inversion, integration/synthesis, meta-framework |

---

## Summary Statistics

| Source | Tools/Skills | Databases | Categories |
|---|---|---|---|
| ToolUniverse | 2,124 tools + 58 skills | 447 API sources | 832 tool classes |
| K-Dense AI | 170+ skills | 250+ data sources | 17 categories |
| Biomni | 155+ tools | 33 DB connectors + 90 datasets | 18 domains |
| Anthropic Life Sciences | 21 plugins | -- | MCP servers + skills |
| **Total (deduplicated)** | **~2,400+ unique capabilities** | **~500+ databases** | **--** |
