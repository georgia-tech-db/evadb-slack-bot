import os
import shutil
import json

# code takes .json files from slack_dump folder opens the json file gets the "team" variable from it and creates a folder for all messages with same team id
def organize_slack_dump():
    root_path = "./slack_dump/"
    folder_path = root_path + "slack_dump/"
    
    dirs = os.listdir(folder_path)
    for file in dirs:
        if file.endswith(".json"):
            with open(folder_path + file, 'r') as f:
                data = json.load(f)
                if len(data)>0:
                    data = data[0]
                else:
                    continue
                team_id = data["user_profile"]["team"]
                if not os.path.exists(root_path + team_id + "___"):
                    os.mkdir(root_path + team_id + "___")
                os.system(f"cp {folder_path + file} {root_path + team_id + '___/' + file}" )

organize_slack_dump()