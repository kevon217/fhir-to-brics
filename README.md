# fhir_to_json

`fhir_to_json` is a preliminary Python package designed for extracting and transforming HL7 FHIR resource element schemas into Biomedical Resource Informatics Computing System (BRICS) data elements.

*NOTE*: This package is currently a work in progress and does not fully implement the required BRICS data element specifications. Mapping FHIR resources and elements to BRICS is still underway.

## Table of Contents
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Utilities](#utilities)

## Installation

To install `fhir_to_json`, clone the repository and set up the environment. The package is not available via pip, so installation involves cloning the repository and installing the required dependencies.

```sh
git clone https://github.com/kevon217/fhir-to-brics
cd fhir-to-json
# If using poetry
poetry install
# If using pip
pip install -r requirements.txt
```

## Configuration

Before using fhir_to_json, you need to set up your environment variables by creating a `.env` file at the top level of the directory which includes the following:
```
PROFILE_STARTSWITH = us-core
RESOURCE_NAME = patient
EXTENSION_ID_STARTSWITH = Extension
UMLS_API_KEY = "your_umls_api_key"
```

You need a `UMLS_API_KEY` as some of the element valuesets are sourced from the National Library of Medicine (NLM), which requires a UMLS API key.

These variables will be loaded as environment variables into the execution environment with `load_dotenv`.

Additionally, ensure that the `all-profiles.csv` and `ImportUDETemplate.csv` files are present in the `/templates` folder.

- [all-profiles.csv](https://build.fhir.org/ig/HL7/US-Core/csvs.zip)
- [ImportUDETemplate.csv](https://fitbir.nih.gov/dictionary/template/importUDE/ImportUDETemplate.csv)

## Usage

The `main.py` module serves as the entry point for the package. It orchestrates the transformation process based on the provided parameters in the `.env` file:

- `profile_startswith`: String filter for profiles e.g., us-core
- `resource_name`: The type of FHIR resource to process e.g., patient
- `extension_Id_startswith`: String filter for identifying extensions e.g., Extension
- `UMLS_API_KEY`: Needed for fetching valuesets from URIs at NLM.

*NOTE*: You'll need to edit the mappings dictionary in `main.py` if you want to modify the hard-coded one-to-one or many-to-one mappings from `all-profiles.csv` headers to `ImportUDETemplate.csv` headers.

```
mappings = {
    "short description": ["Path", "Slice Name", "Must Support?", "Short"],
    "definition": [
        "Definition",
        "Comments",
        "Requirements",
        "Meaning When Missing",
    ],
    "guidelines/instructions": ["Binding Strength", "Binding Description"],
    "notes": ["Is Modifier?", "Is Summary?"],
    "references": ["Binding Value Set"],
}
```

To execute the package, run:

```
cd path/to/fhir-to-brics
python -m fhir_to_brics.main
```

## Utilities

The `utils.py` module provides utility functions for data processing:

- `load_profile`, `load_resource`, `load_extensions`: Load and filter data from CSV files into pandas DataFrames.
- `create_variable_name`, `combine_columns_into_string`: Assist in creating structured names and descriptions for BRICS data elements.
- `fetch_fhir_valueset`, `fetch_nlm_valueset`, `fetch_valueset`: Retrieve value sets from FHIR or NLM sources.
- `parse_valueset_to_list`: Extract values and descriptions from a FHIR value set.
- `process_resource_rows`, `process_extension_rows`: Process FHIR data and map it to the BRICS format.
- `merge_with_template`: Combine processed data with a BRICS data element template.

Logging is used throughout to track the execution and aid in troubleshooting, but you'll want to tweak it further to suite your needs.

## Contact

This package was created by [Kevin Armengol](kevin.armengol@gmail.com), but will be further developed by [Henry Ogoe](henry.ogoe@nih.gov) and [Olga Vovk](olga.vovk@nih.gov>).
