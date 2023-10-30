import os
import pandas as pd
import requests
import json
import base64
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)


def load_profile(fp, profile_startswith):
    """
    Load profiles from a CSV into a DataFrame based on the starting string of the Profile column.

    Parameters:
    - fp (str): The file path to the CSV file.
    - profile_startswith (str): The starting string to filter the Profile column.

    Returns:
    - DataFrame: The DataFrame containing the filtered profiles.
    """
    logging.info(f"Loading profiles from {fp} that start with {profile_startswith}")
    df = pd.read_csv(fp)
    return df[df["Profile"].str.startswith(profile_startswith, na=False)]


def load_resource(df, resource):
    """
    Filter a DataFrame based on the resource type.

    Parameters:
    - df (DataFrame): The DataFrame to filter.
    - resource (str): The resource type to filter on.

    Returns:
    - DataFrame: The DataFrame containing only the specified resource type.
    """
    logging.info(f"Filtering DataFrame based on resource type: {resource}")
    return df[df["Profile"].str.endswith(resource, na=False)]


def load_extensions(fp, extension_Id_startswith):
    """
    Load extensions from a CSV into a DataFrame based on the starting string of the Id column.

    Parameters:
    - fp (str): The file path to the CSV file.
    - extension_Id_startswith (str): The starting string to filter the Id column.

    Returns:
    - DataFrame: The DataFrame containing the filtered extensions.
    """
    logging.info(
        f"Loading extensions from {fp} that start with {extension_Id_startswith}"
    )
    df = pd.read_csv(fp)
    return df[df["Id"].str.startswith(extension_Id_startswith, na=False)]


def initialize_brics_dataframe(de_template):
    """
    Create an empty DataFrame with the same columns as de_template.

    Parameters:
    - de_template (DataFrame): The DataFrame containing the DE template.

    Returns:
    - DataFrame: An empty DataFrame with the same columns as de_template.
    """
    brics_df = pd.DataFrame(columns=de_template.columns)
    return brics_df


def create_variable_name(df_or_row):
    """
    Create 'variable name' by combining 'Path' and 'Slice Name' from df_or_row.

    Parameters:
    - df_or_row (DataFrame or Series): The DataFrame or Series containing the FHIR US Core Patient Profile.

    Returns:
    - Series or str: The 'variable name' series if a DataFrame is passed, or a single string if a Series is passed.
    """
    if isinstance(df_or_row, pd.Series):
        path = df_or_row["Path"]
        slice_name = (
            df_or_row["Slice Name"] if pd.notna(df_or_row["Slice Name"]) else ""
        )
        return f"{path}:{slice_name}".rstrip(":")
    else:
        variable_names = df_or_row["Path"].str.cat(
            df_or_row["Slice Name"].fillna(""), sep=":"
        )
        return variable_names.str.rstrip(":")


def combine_columns_into_string(row, columns_dict, prefix="FHIR", sep=" | "):
    """
    Generate a combined column by concatenating the values of multiple columns from a row of the FHIR US Core Patient Profile.

    Parameters:
    - row (Series): The row of the DataFrame containing the FHIR US Core Patient Profile.
    - columns_dict (dict): A dictionary where the key is the column we are mapping to and the values are a list of the columns we are using.
    - prefix (str): A prefix to prepend to each part of the combined column.
    - sep (str): A separator to use between each part of the combined column.

    Returns:
    - str: The generated combined column.
    """
    combined_column_parts = []

    for columns in columns_dict.values():
        # Ensure columns is a list
        if isinstance(columns, str):
            columns = [columns]

        for column in columns:
            value = row[column]
            if pd.notna(value):
                combined_column_parts.append(f"{prefix} {column}: {value}")

    return sep.join(combined_column_parts)


def fetch_fhir_valueset(uri, headers=None):
    """
    Fetch a FHIR extension from a given URI.

    Parameters:
    - uri (str): The URI of the FHIR extension.
    - headers (dict): Optional HTTP headers.

    Returns:
    - dict: The FHIR extension as a dictionary, or None if the fetch fails.
    """
    logging.info(f"Fetching FHIR value set from URI: {uri}")
    try:
        response = requests.get(uri, headers=headers, timeout=10)
        response.raise_for_status()
        return json.loads(response.text)
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch data from {uri}: {e}")
        return None


def fetch_nlm_valueset(uri, api_key):
    """
    Fetch a value set from the National Library of Medicine (NLM).

    Parameters:
    - uri (str): The URI of the NLM value set.
    - api_key (str): The API key for NLM.

    Returns:
    - dict: The NLM value set as a dictionary, or None if the fetch fails.
    """
    logging.info(f"Fetching NLM value set from URI: {uri}")
    auth_header = base64.b64encode(f"apikey:{api_key}".encode("utf-8")).decode("utf-8")
    headers = {"Authorization": f"Basic {auth_header}"}
    try:
        response = requests.get(uri, headers=headers, timeout=10)
        response.raise_for_status()
        logging.info(f"Successfully fetched NLM value set from URI: {uri}")
        return json.loads(response.text)
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch data from {uri}: {e}")
        return None


def fetch_valueset(uri, headers=None, api_key=None):
    """
    Fetch a value set, either from FHIR or NLM based on the URI.

    Parameters:
    - uri (str): The URI of the value set.
    - headers (dict): Optional HTTP headers for FHIR.
    - api_key (str): Optional API key for NLM.

    Returns:
    - dict: The value set as a dictionary, or None if the fetch fails.
    """
    logging.info(f"Fetching value set from URI: {uri}")
    if "cts.nlm.nih.gov" in uri and api_key:
        return fetch_nlm_valueset(uri, api_key)
    else:
        return fetch_fhir_valueset(uri, headers)


def parse_valueset_to_list(valueset, fhir_headers=None, nlm_api_key=None):
    """
    Parse a FHIR value set to extract permissible values and descriptions.

    Parameters:
    - valueset (dict): The FHIR value set.
    - fhir_headers (dict): Optional headers for FHIR API requests.
    - nlm_api_key (str): Optional API key for NLM value sets.

    Returns:
    - tuple: Two pipe-separated strings, one for permissible values and one for descriptions.
    """
    logging.info("Parsing value set to extract permissible values and descriptions.")
    permissible_values = []
    permissible_values_descriptions = []

    if "compose" in valueset and "include" in valueset["compose"]:
        includes = valueset["compose"]["include"]

        for include in includes:
            if "concept" in include:
                for concept in include["concept"]:
                    code = concept.get("code", "")
                    display = concept.get("display", "")
                    permissible_values.append(code)
                    permissible_values_descriptions.append(display)

            elif "valueSet" in include:
                for valueSet_uri in include["valueSet"]:
                    nested_valueset = fetch_valueset(
                        valueSet_uri, fhir_headers, nlm_api_key
                    )
                    if nested_valueset:
                        nested_values, nested_descriptions = parse_valueset_to_list(
                            nested_valueset
                        )
                        if nested_values and nested_descriptions:
                            permissible_values.extend(nested_values.split("|"))
                            permissible_values_descriptions.extend(
                                nested_descriptions.split("|")
                            )

    if not permissible_values or not permissible_values_descriptions:
        return None, None

    return "|".join(permissible_values), "|".join(permissible_values_descriptions)


def get_resource_extensions(df_resource, df_extensions):
    """
    Extracts relevant extensions from a FHIR profile DataFrame.

    Parameters:
    - df_resource (DataFrame): DataFrame containing the FHIR profile.
    - df_extensions (DataFrame): DataFrame containing the FHIR extensions.

    Returns:
    - DataFrame: A DataFrame containing only the relevant extensions.
    """
    logging.info("Extracting relevant extensions from FHIR profile DataFrame.")
    # Initialize an empty DataFrame to hold the new rows
    df_resource_extensions = pd.DataFrame(columns=df_resource.columns)

    # Check df_resource['Slice Name']
    for index, row in df_resource.iterrows():
        slice_name = row["Slice Name"]

        if pd.notna(slice_name):
            # Filter df_extensions based on the slice_name
            df_relevant_extensions = df_extensions[
                df_extensions["Profile"].str.contains(
                    f"{slice_name}$", case=False, na=False
                )
            ]

            # Append the relevant_extensions to df_new_rows
            df_resource_extensions = pd.concat(
                [df_resource_extensions, df_relevant_extensions], ignore_index=True
            )

    return df_resource_extensions


def process_resource_rows(
    df_resource, df_extensions, de_template, mappings, fhir_headers, nlm_api_key
):
    """
    Process rows from a FHIR resource DataFrame and map them to a BRICS DataFrame.

    Parameters:
    - df_resource (DataFrame): DataFrame containing FHIR resource rows.
    - df_extensions (DataFrame): DataFrame containing FHIR extensions.
    - de_template (DataFrame): DataFrame containing the BRICS data element template.
    - mappings (dict): Dictionary mapping BRICS columns to FHIR resource columns.
    - fhir_headers (dict): Optional headers for FHIR API requests.
    - nlm_api_key (str): Optional API key for NLM value sets.

    Returns:
    - DataFrame: A DataFrame containing the mapped rows.
    """
    logging.info("Processing resource rows...")
    new_rows = []

    # Loop through each row in df_resource
    for index, row in df_resource.iterrows():
        # Create a new row as a dictionary
        new_row = {}

        # Create 'variable name'
        new_row["variable name"] = create_variable_name(row)

        # Map fields to BRICS
        for brics_column, resource_columns in mappings.items():
            new_row[brics_column] = combine_columns_into_string(
                row, {brics_column: resource_columns}
            )

        # Handle 'Binding Value Set' URIs
        if pd.notna(row["Binding Value Set"]):
            uri = row["Binding Value Set"]
            valueset = fetch_valueset(uri, fhir_headers, nlm_api_key)
            if valueset:
                (
                    permissible_values,
                    permissible_values_descriptions,
                ) = parse_valueset_to_list(valueset, fhir_headers, nlm_api_key)
                if permissible_values and permissible_values_descriptions:
                    new_row["permissible values"] = permissible_values
                    new_row[
                        "permissible value descriptions"
                    ] = permissible_values_descriptions

        # Add the new_row dictionary to the list
        new_rows.append(new_row)

        # Handle rows with 'Slice Name'
        if pd.notna(row["Slice Name"]):
            extension_rows_df = process_extension_rows(
                row, df_extensions, fhir_headers, nlm_api_key, mappings
            )
            new_rows.extend(extension_rows_df.to_dict("records"))

    # Create a DataFrame from the list of new rows
    df_mapped = pd.DataFrame(new_rows)

    return df_mapped


def process_extension_rows(row, df_extensions, fhir_headers, nlm_api_key, mappings):
    """
    Process extension rows for a given FHIR resource row.

    Parameters:
    - row (Series): A row from the FHIR resource DataFrame.
    - df_extensions (DataFrame): DataFrame containing FHIR extensions.
    - fhir_headers (dict): Optional headers for FHIR API requests.
    - nlm_api_key (str): Optional API key for NLM value sets.
    - mappings (dict): Dictionary mapping BRICS columns to FHIR resource columns.

    Returns:
    - DataFrame: A DataFrame containing the processed extension rows.
    """
    logging.info(f"Processing extension rows for slice name: {row['Slice Name']}")
    extension_rows = []

    slice_name = row["Slice Name"]
    original_var_name = create_variable_name(
        pd.Series(row)
    )  # Original variable name from df_resource

    # Filter df_extensions to find corresponding rows
    matching_extensions = df_extensions[
        df_extensions["Profile"].str.endswith(slice_name)
    ]
    matching_extensions = matching_extensions[
        matching_extensions["Id"].str.endswith(".value[x]")
    ]

    # Check if any matching extensions are found
    if matching_extensions.empty:
        print(f"No matching extensions found for slice name: {slice_name}")
        return pd.DataFrame(extension_rows)

    for _, ext_row in matching_extensions.iterrows():
        new_row = {}

        # Modify 'variable name'
        extension_id = ext_row["Id"]
        new_row["variable name"] = f"{original_var_name}.{extension_id}"

        # Map fields to BRICS using the same mappings as for the original row
        for brics_column, resource_columns in mappings.items():
            new_row[brics_column] = combine_columns_into_string(
                row, {brics_column: resource_columns}
            )

        # Fetch value sets if 'Binding Value Set' has a URI
        if pd.notna(ext_row["Binding Value Set"]):
            uri = ext_row["Binding Value Set"]
            valueset = fetch_valueset(uri, fhir_headers, nlm_api_key)

            if valueset:
                (
                    permissible_values,
                    permissible_values_descriptions,
                ) = parse_valueset_to_list(valueset, fhir_headers, nlm_api_key)
                if permissible_values and permissible_values_descriptions:
                    new_row["permissible values"] = permissible_values
                    new_row[
                        "permissible value descriptions"
                    ] = permissible_values_descriptions

        extension_rows.append(new_row)

    return pd.DataFrame(extension_rows)


def merge_with_template(df_mapped, de_template):
    """
    Merge the processed BRICS DataFrame with the DE template.

    Parameters:
    - df_mapped (DataFrame): DataFrame containing the processed BRICS rows.
    - de_template (DataFrame): DataFrame containing the BRICS data element template.

    Returns:
    - DataFrame: A DataFrame containing the merged rows.
    """
    logging.info("Merging processed DataFrame with DE template...")
    # Ensure that the columns in df_mapped are also in de_template
    for col in df_mapped.columns:
        if col not in de_template.columns:
            raise ValueError(f"Column {col} in df_mapped is not in de_template.")

    # Concatenate the DataFrames
    merged_df = pd.concat([de_template, df_mapped], ignore_index=True)

    return merged_df
