import pickle
body = pickle.load(open("test/test_inputs/body3.pkl", "rb"))
import pprint
pprint.pprint(body, indent=1)

def change_channel_value(body, new_channel_name):
    body['event']['channel'] = new_channel_name

def change_text(body, new_text):
    body['event']['text'] = new_text

change_text(body, "<someuser> tell about the exam1")

pickle.dump(body, open("test/test_inputs/body3.pkl", "wb"))