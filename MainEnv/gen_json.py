import json
# Generates the file .json of with the measured max and min for each servomotor
config = {
    "thumb_big": {
        "range_from": 0,
        "range_to": 70
    },
    "thumb_little": {
        "range_from": 35,
        "range_to": 100
    },
    "index_finger": {
        "range_from": 0,
        "range_to": 160
    },
    "middle_finger": {
        "range_from": 0,
        "range_to": 180
    },
    "ring_pinky": {
        "range_from": 0,
        "range_to": 140
    },
    "forearm": {
        "range_from": 0,
        "range_to": 180
    }
}
# Opening file in write mode
with open("MainEnv/config.json", "w") as json_file:
    # Write data in json file
    json.dump(config, json_file)