from collections import defaultdict
from utils.logging import APP_LOGGER
from math import ceil
from utils.formatted_messages.wait import MSG as WAIT_MSG
import time

time_tracker = defaultdict(lambda: 0)
credit_tracker = defaultdict(lambda: 2)

def time_user(user, event_id):
    """
    takes in the event_id and user's username to calculate the wait time
    """
    cooldown_time = time.time() - time_tracker[user]
    if cooldown_time < 300:
        APP_LOGGER.info(f"{event_id} - needs cooldown {cooldown_time}")
        return WAIT_MSG.format(ceil((5 - cooldown_time / 60)))
    else:
        time_tracker[user] = time.time()