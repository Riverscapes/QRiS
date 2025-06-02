import json
import os


def update_json(workspace, original_json, new_json, output_json):
    """Merge two Climate Engine JSON files into a single output file.
    Args:   
        workspace (str): The directory where the JSON files are located.
        original_json (str): Path to the original Climate Engine JSON file.
        new_json (str): Path to the new Climate Engine JSON file with QRiS variables.
        output_json (str): Path to the output JSON file where the merged data will be saved.
    """
    
    final_data = {}
    
    # Load the oiriginal Climate Engine JSON file
    with open(original_json, 'r', encoding='utf-8') as file1:
        original_Data = json.load(file1)
        for datasetName, val2 in original_Data.items():
            path = val2.get('path', None)
            datasetId = val2.get('id', None)

            final_data[datasetId] = {
                "datasetName": datasetName,
                "datasetId": datasetId,
                "path": path,
                "warn": False,
                "mapping": False,
                "variables": []
            }

    # load the JSON file
    with open(new_json, 'r', encoding='utf-8') as file2:
        new_data = json.load(file2)

        for datasetId, val1 in new_data.items():
            variables = val1.get('all_vars', [])
            qris_vars = val1.get('qris_vars', [])
            warn  = val1.get('qris_warn', False)

            existing_data = final_data.get(datasetId, {})
            existing_data['datasetId'] = datasetId
            existing_data['path'] = existing_data.get('path', None)
            existing_data['datasetName'] = existing_data.get('datasetName', datasetId)
            existing_data['variables'] = [{"variableName": var, "defaultVisible": (var in qris_vars if qris_vars else False)} for var in variables]
            existing_data['mapping'] = val1.get('for_qris_mapping', False)
            existing_data["warn"] = warn
            final_data[datasetId] = existing_data

    data_as_list = list(final_data.values())

    with open(output_json, 'w', encoding='utf-8') as file3:
        json.dump(data_as_list, file3, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    workspace = os.path.dirname(os.path.abspath(__file__))
    original_json = os.path.join(workspace, 'original_climate_engine.json')
    new_json = os.path.join(workspace, 'CEDatasets_QRiS_20250507.json')
    output_json = os.path.join(workspace, 'merged.json')
    update_json(workspace, original_json, new_json, output_json)
    print(f"Updated JSON file created at: {output_json}")
