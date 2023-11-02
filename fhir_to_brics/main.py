import os
import pandas as pd
import logging
from dotenv import load_dotenv

from fhir_to_brics.utils import (
    load_profile,
    load_resource,
    load_extensions,
    process_resource_rows,
    merge_with_template,
)

# Initialize logging
logging.basicConfig(level=logging.INFO)


def main(
    profile_startswith="us-core",
    resource_name="patient",
    extension_Id_startswith="Extension",
):
    """
    Main function to orchestrate the transformation of FHIR resources to BRICS data elements.

    Parameters:
    - profile_startswith (str): Starting string to filter profiles. Default is 'us-core'.
    - resource_name (str): Name of the FHIR resource to process. Default is 'patient'.
    - extension_Id_startswith (str): Starting string to filter extensions. Default is 'Extension'.
    """
    logging.info("Starting the FHIR to BRICS transformation process.")

    fp_de_template = "fhir_to_brics/templates/ImportUDETemplate.csv"
    fp_profiles = "fhir_to_brics/templates/all-profiles.csv"

    # Initialize headers for FHIR and NLM APIs
    fhir_headers = {"Accept": "application/fhir+json"}

    nlm_api_key = UMLS_API_KEY

    # Load dataframes
    logging.info("Loading dataframes.")
    df_profile = load_profile(fp=fp_profiles, profile_startswith=profile_startswith)
    df_resource = load_resource(df=df_profile, resource=resource_name)
    df_extensions = load_extensions(
        fp=fp_profiles, extension_Id_startswith=extension_Id_startswith
    )
    de_template = pd.read_csv(fp_de_template)

    # Define mappings
    logging.info("Defining mappings.")
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

    # Process the resource rows
    logging.info("Processing resource rows.")
    df_mapped = process_resource_rows(
        df_resource, df_extensions, de_template, mappings, fhir_headers, nlm_api_key
    )

    # Merge with template
    logging.info("Merging with template.")
    brics_des = merge_with_template(df_mapped, de_template)

    # Save the processed data
    logging.info("Saving the processed data.")
    fp_brics_des = f"fhir_to_brics/output/{resource_name}_des.csv"
    brics_des.to_csv(fp_brics_des, index=False)

    logging.info("FHIR to BRICS transformation process completed.")


if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    profile_startswith = os.getenv("PROFILE_STARTSWITH", "us-core")
    resource_name = os.getenv("RESOURCE_NAME", "patient")
    extension_Id_startswith = os.getenv("EXTENSION_ID_STARTSWITH", "Extension")
    UMLS_API_KEY = os.getenv("UMLS_API_KEY")
    main(profile_startswith, resource_name, extension_Id_startswith)
