import pickle
body = pickle.load(open("test/test_inputs/body.pkl", "rb"))
import pprint
pprint.pprint(body, indent=1)

def change_channel_value(body, new_channel_name):
    body['event']['channel'] = new_channel_name

def change_text(body, new_text):
    body['event']['text'] = new_text

change_channel_value(body, "C05S06YFL3X")
change_text(body, "<someuser> what is the workload of ML4T course? --set-channel=C08LKC5CL")

pickle.dump(body, open("test/test_inputs/body.pkl", "wb"))
