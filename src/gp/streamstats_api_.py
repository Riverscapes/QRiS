import requests
import json
import os


def get_streamstats_data(lat, lon, new_file_dir=None):
    state_code = get_state_from_coordinates(lat, lon)
    watershed_data = delineate_watershed(lat, lon, state_code, new_file_dir)
    workspace_id = watershed_data["workspaceID"]

    basin_characteristics = get_basin_characteristics(state_code, workspace_id, new_file_dir)
    flow_statistics = get_flow_statistics(state_code, workspace_id, new_file_dir)


def delineate_watershed(lat, lon, rcode, file_path=None):
    url = "https://streamstats.usgs.gov/streamstatsservices/watershed.geojson"

    parameters = {
        "rcode": rcode,
        "xlocation": lon,
        "ylocation": lat,
        "crs": "4326",
        "includeparameters": "false",
        "includeflowtypes": "false",
        "includefeatures": "true",
        "simplify": "true"
    }

    response = requests.get(url, params=parameters)
    response_dict = response.json()

    if file_path is not None:
        save_json(response_dict, file_path, response_dict["workspaceID"] + "_wats.geojson")
    return response_dict

    # response_json = json.load(x)
    # watershed = response_json["featurecollection"][]


def get_basin_characteristics(rcode, workspace_id, file_path=None):
    url = "https://streamstats.usgs.gov/streamstatsservices/parameters.json"
    parameters = {
        "rcode": rcode,
        "workspaceID": workspace_id,
        "includeparameters": "true"
    }
    response = requests.get(url, params=parameters)
    basin_data = response.json()
    if file_path is not None:
        save_json(basin_data, file_path, workspace_id + "_basin.json")
    return basin_data


'UT20220818211335897000'


def get_flow_statistics(rcode, workspace_id, file_path=None):
    url = "https://streamstats.usgs.gov/streamstatsservices/flowstatistics.json"
    parameters = {
        "rcode": rcode,
        "workspaceID": workspace_id,
        "includeflowtypes": "true"
    }
    response = requests.get(url, params=parameters)
    flow_data = response.json()

    if file_path is not None:
        save_json(flow_data, file_path, workspace_id + "_flow.json")
    return flow_data


def save_json(dict, directory, file_name):
    with open(os.path.join(directory, file_name), 'w') as file:
        json.dump(dict, file)


def get_state_from_coordinates(latitude, longitude):
    url = "https://nominatim.openstreetmap.org/reverse"
    parameters = {
        "lat": latitude,
        "lon": longitude,
        "format": "json"
    }
    response = requests.get(url, params=parameters)
    location_data = response.json()
    location_code = location_data["address"]["ISO3166-2-lvl4"]
    # Extracts state abbreviation from location code
    return location_code[location_code.index("-") + 1:]


def jprint(obj):
    text = json.dumps(obj, indent=4)
    print(text)


if __name__ == '__main__':
    get_streamstats_data(lat="41.81010425321681", lon="-112.07464769059571", new_file_dir="C:\\Users\\tyguy\\Documents")
# 41.81010425321681, -112.07464769059571
