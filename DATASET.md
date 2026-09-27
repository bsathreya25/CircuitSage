# CircuitSage Dataset

## Dataset Architecture and Knowledge Base

CircuitSage uses a curated embedded-systems dataset as the technical foundation for its retrieval and diagnostic workflow.

The dataset is intentionally separated into:

1. Raw source material
2. Curated canonical projects
3. Retrieval indexes
4. Project artifacts and metadata

This separation allows CircuitSage to preserve the original dataset while operating on a controlled and reproducible canonical corpus.


# 1. Dataset Overview

CircuitSage was developed using a larger Arduino-oriented project collection that was subsequently inspected and curated for use in the diagnostic system.
The current repository does **not** treat the entire raw collection as the active diagnostic corpus.
Instead, CircuitSage uses a curated canonical subset containing:

89 canonical projects
There is also: 1 duplicate alias

The duplicate alias corresponds to an exact duplicate project and is not counted as an additional canonical project.
Therefore:
Canonical projects = 89
Duplicate aliases   = 1

## Raw Dataset

The original Arduino dataset is maintained separately from the curated CircuitSage corpus.
The raw dataset contained approximately:
533 top-level projects

The raw dataset also contained a mixture of:
- Arduino source code
- Header files
- C++ source files
- Images
- Schematics
- PDFs
- Other project artifacts
- 
The raw dataset is treated as the original source material.

Important Principle

The raw dataset should remain untouched.
CircuitSage does not modify the original source collection merely to make it fit the diagnostic pipeline.
Instead:
Raw Dataset
     │
     ▼
Inspection + Curation
     │
     ▼
Canonical Corpus
     │
     ▼
Retrieval / Diagnostic System

This preserves the original data while allowing CircuitSage to operate on a controlled subset.

## Canonical Corpus
The canonical corpus is the curated set of projects selected for use by CircuitSage.
Current size:
89 canonical projects

The selection process was intended to prioritize projects that provide useful technical and diagnostic evidence rather than simply maximizing the number of projects included.
The canonical corpus provides the basis for:

- Technical retrieval
- Component identification
- Source-code evidence
- Diagnostic context
- Engineering parameter extraction
- Representative embedded-system examples
  
## Duplicate Handling
  
During dataset inspection, one exact duplicate project was identified.
The duplicate was:
421 LoRa_AT

which was identified as an exact duplicate of:
276 LoRa_AT

The duplicate is treated as an alias rather than as a separate canonical project.
Therefore the canonical corpus counts the project only once.
Canonical:
276 LoRa_AT

Alias / duplicate:
421 LoRa_AT

This prevents duplicated technical evidence from artificially increasing the apparent representation of a particular project.

## Canonical Source Files
The canonical corpus contains the following source-file composition:
File Type	Count
.ino	136
.cpp	21
.h	38
Total source/header files	195


These files represent the firmware and supporting source material available to the CircuitSage retrieval and diagnostic workflow.
The presence of a source file in the corpus does not automatically imply that every part of that file is interpreted or validated.
Component-specific deterministic validators operate only where explicit validation logic exists.

## Project Artifacts
   
In addition to source code, the canonical corpus contains project artifacts.
The current artifact inventory contains approximately:
143 image/PDF artifacts

These include project materials such as:
- Schematics
- Images
- PDFs
- Other visual/reference artifacts
Artifacts provide additional technical context for the project corpus.
However, artifact availability should not be confused with complete visual understanding.

## Schematic and Visual Evidence

CircuitSage preserves schematic and other visual artifacts where they are available.
The current architecture distinguishes between:
Artifact exists

and:
Artifact has been fully interpreted

The current V1.0 diagnostic workflow does not perform complete visual schematic reasoning across the entire corpus.
Therefore, schematic artifacts are currently best understood as an available evidence layer rather than as a fully automated visual-diagnosis system.

## Canonical Dataset Structure

The curated dataset is represented inside the repository separately from the raw source collection.
The relevant repository areas include:
data/
└── canonical/

knowledge_base/
├── retrieval_index.json
└── project_records.json

The canonical data contains the selected projects and their associated technical source material.
The retrieval index provides the structured representation used by the retrieval system.

## Retrieval Index

CircuitSage uses a retrieval index to make the canonical corpus searchable.
The primary retrieval index is:
knowledge_base/retrieval_index.json

The current index contains:
89 records
corresponding to the canonical project corpus.
The index contains structured project-level information used to rank technically relevant evidence.

## Retrieval Fields

The retrieval system uses multiple fields when evaluating technical relevance.
These include:
Field	Purpose
Component	Identify component-specific relevance
Library	Identify software/library relationships
Diagnostic signal	Identify troubleshooting-related evidence
Source file	Match relevant source material
Artifact file	Identify supporting project artifacts
Project name	Match project-level terminology
Interface	Identify communication/interface relevance
Category	Provide broader project context
These fields allow CircuitSage to retrieve technically relevant projects rather than relying only on project-name similarity.

## Retrieval Weighting

The current retrieval weighting is:
Evidence Field	Weight
Component	10
Library	10
Diagnostic signal	10
Source file	7
Artifact file	5
Project name	4
Interface	3
Category	1

These values are used for ranking retrieval results.
They should not be interpreted as:
- Diagnostic confidence
- Hardware reliability
- Probability of failure
- Correctness of the retrieved project

For example:
High retrieval score
        ≠
Confirmed hardware fault

The retrieval system identifies useful technical evidence; deterministic validation and reasoning operate on that evidence afterward.

## Canonical Manifest

The canonical corpus is tracked through a manifest to maintain a controlled project set.
The canonical manifest was verified against the selected corpus.
The verification result was:
89 / 89 canonical projects accounted for

No canonical project was missing from the verified set.
This provides a basic consistency check between the curated dataset and the repository representation.

## Dataset Selection Philosophy

The canonical corpus was not created simply by taking the first available projects.
Selection emphasized technical usefulness and diagnostic value.
Relevant considerations included:
- Component diversity
- Embedded-system diversity
- Availability of source code
- Diagnostic usefulness
- Technical representation
- Availability of supporting project artifacts
- Relevance to the intended CircuitSage workflow
The goal was to create a manageable diagnostic corpus rather than an unnecessarily large collection with weak or redundant evidence.

## Representative Technical Coverage
    
The canonical corpus contains projects involving multiple embedded-system components and systems.
Representative components used during validation of the retrieval pipeline include:
HC-SR04
DHT11 / DHT22
MPU6050
nRF24L01
GSM
Stepper motor systems

These projects were also used to evaluate whether retrieval could surface technically relevant evidence.
Retrieval relevance does not require that the expected project always appear as the highest-ranked result.

## Dataset and Deterministic Validators
    
The dataset and deterministic validation system have different responsibilities.
The dataset provides:
Technical examples
Source-code evidence
Project context
Component relationships
Artifacts

The deterministic validators provide:
Explicit implementation checks
PASS / FAIL / UNKNOWN findings
Component-specific validation

Therefore:
Dataset
   ↓
Evidence

Validator
   ↓
Deterministic finding

The existence of a project in the dataset does not automatically mean that the system can deterministically validate every aspect of that project.

## Dataset and LLM Reasoning

The dataset also provides context for the evidence-constrained reasoning layer.
The LLM should reason over evidence retrieved from the corpus and findings produced by deterministic analysis.
It should not treat the corpus as proof that the user's physical hardware behaves identically to a stored project.

For example:
Retrieved HC-SR04 project
        ↓
Technical reference
        ≠
Proof of user's wiring

This distinction is essential to maintaining evidence-grounded diagnostics.
## Project_records.json
The repository contains:
knowledge_base/project_records.json

This file is not the canonical source of truth for the complete CircuitSage corpus.
It represents an older/test artifact containing only a small number of records.
The canonical corpus is represented through the curated project data and retrieval index rather than treating this older file as the complete dataset.
This distinction prevents an outdated test artifact from being mistaken for the production knowledge base.

## Dataset Artifacts vs Diagnostic Path

Not Every stored dataset artifact is consumed by every diagnostic request.
The current architecture separates:
Available dataset evidence

from:
Evidence actively consumed by the diagnostic path

For example, a schematic may exist for a project without being fully interpreted by the current diagnostic engine.
Similarly, a source file can exist in the corpus without a dedicated deterministic validator being implemented for every behavior within that file.

## Dataset Integrity Principles

CircuitSage follows several dataset-management principles.
Preserve raw source material
The original dataset should remain unchanged.
Curate before diagnostic use
Only selected projects form the canonical diagnostic corpus.

Avoid duplicate evidence
Exact duplicates should not be counted as independent canonical projects.
Separate data from indexes
The underlying project data and retrieval indexes have different roles.

Do not confuse availability with interpretation
An artifact existing in the repository does not mean the system has automatically understood it.
Keep diagnostic scope explicit
The dataset does not imply universal embedded-system coverage.

## Current Dataset Statistics
    
The current CircuitSage dataset can be summarized as follows: 

Metric	Current Value
Raw top-level projects	~533
Canonical projects	89
Duplicate aliases	1
Canonical source/header files	195
.ino files	136
.cpp files	21
.h files	38
Image/PDF artifacts	143
Retrieval index records	89
Canonical manifest coverage	89 / 89


These values describe the current curated dataset state documented for CircuitSage V1.0.

## Dataset Limitations
The dataset has several limitations.
Arduino-oriented scope
The corpus is primarily oriented toward Arduino and embedded-system projects. 

It should not be interpreted as a comprehensive representation of all embedded platforms.
Uneven project coverage
Different components and systems are represented with different levels of depth.

Source-code availability does not imply hardware verification
Stored code can provide software evidence but cannot establish the physical state of the corresponding hardware.
Artifact availability is uneven
Not every project necessarily contains the same types or quantity of supporting artifacts.
Retrieval is not exhaustive diagnosis

The retrieval layer provides relevant evidence; it does not replace engineering validation.

## Reproducibility
    
The dataset architecture is designed to make the distinction between source material and curated diagnostic data explicit.
The important layers are:
Raw Dataset
    ↓
Project Inspection
    ↓
Canonical Selection
    ↓
Canonical Repository Data
    ↓
Retrieval Index
    ↓
Diagnostic Pipeline

This separation makes it possible to reason about changes to the dataset without confusing the original source collection with the active diagnostic corpus.

## Dataset Role in CircuitSage

The dataset is not simply a collection of examples.
It forms the technical evidence layer supporting the diagnostic workflow.
The overall relationship is:
                 ┌──────────────────┐
                 │   Raw Dataset    │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Curated Corpus   │
                 │ 89 Projects      │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Retrieval Index  │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Evidence Package │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Diagnostic       │
                 │ Reasoning        │
                 └──────────────────┘

The dataset therefore acts as the foundation for evidence retrieval while deterministic validators and reasoning provide additional diagnostic layers.
# Final Dataset Principle
**The central dataset principle is:**

CircuitSage uses a curated, controlled evidence corpus rather than treating every available project as equally relevant or every stored artifact as automatically understood.

The current V1.0 dataset provides the foundation for retrieval-driven embedded-system diagnostics while keeping the original raw source material separate from the curated diagnostic corpus.
