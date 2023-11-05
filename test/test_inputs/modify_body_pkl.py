import pickle
body = pickle.load(open("test/test_inputs/body.pkl", "rb"))
import pprint
pprint.pprint(body, indent=1)

def change_channel_value(body, new_channel_name):
    body['event']['channel'] = new_channel_name

def change_text(body, new_text):
    body['event']['text'] = new_text

change_channel_value(body, "C08LKC5CL")
change_text(body, "<someuser> ML4T")

pickle.dump(body, open("test/test_inputs/body.pkl", "wb"))