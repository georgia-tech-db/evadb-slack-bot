def change_channel_value(body, new_channel_name):
    body['event']['channel'] = new_channel_name

def change_text(body, new_text):
    body['event']['text'] = new_text