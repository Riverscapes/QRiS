import requests
import json
import os
from time import sleep


# Makes all 4 api calls. Currently not working consistently due to time delays
def get_streamstats_data(lat, lon, new_file_dir=None):
    state_code = get_state_from_coordinates(lat, lon)
    watershed_data = delineate_watershed(lat, lon, state_code, new_file_dir)
    # Added sleep timer to give time for USGS database to update
    # sleep(30)
    workspace_id = watershed_data["workspaceID"]
    basin_characteristics = get_basin_characteristics(state_code, workspace_id, new_file_dir)
    # sleep(30)
    flow_statistics = get_flow_statistics(state_code, workspace_id, new_file_dir)
    return (watershed_data, basin_characteristics, flow_statistics)


# Returns dictionary of watershed info based on coordinates and U.S. state
def delineate_watershed(lat, lon, rcode, file_dir=None):
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
    watershed_data = response.json()

    if file_dir is not None:
        save_json(watershed_data, file_dir, watershed_data["workspaceID"] + "_wats.geojson")
    return watershed_data


# Returns dictionary of river basin characteristics
def get_basin_characteristics(rcode, workspace_id, file_dir=None):
    url = "https://streamstats.usgs.gov/streamstatsservices/parameters.json"
    parameters = {
        "rcode": rcode,
        "workspaceID": workspace_id,
        "includeparameters": "true"
    }
    response = requests.get(url, params=parameters)
    basin_data = response.json()
    if file_dir is not None:
        save_json(basin_data, file_dir, workspace_id + "_basin.json")
    return basin_data


# Returns dictionary of river flow stats
def get_flow_statistics(rcode, workspace_id, file_dir=None):
    url = "https://streamstats.usgs.gov/streamstatsservices/flowstatistics.json"
    parameters = {
        "rcode": rcode,
        "workspaceID": workspace_id,
        "includeflowtypes": "true"
    }
    response = requests.get(url, params=parameters)
    flow_data = response.json()

    if file_dir is not None:
        save_json(flow_data, file_dir, workspace_id + "_flow.json")
    return flow_data


# Saves dictionary to custom location
def save_json(dict, directory, file_name):
    with open(os.path.join(directory, file_name), 'w') as file:
        json.dump(dict, file)


# Uses coordinates to determine U.S. state using API
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


# Prints dict/json
def jprint(obj):
    text = json.dumps(obj, indent=4)
    print(text)


if __name__ == '__main__':
    get_streamstats_data(lat="39.93001576699861", lon="-111.54599129378481", new_file_dir="C:\\Users\\tyguy\\Documents")
