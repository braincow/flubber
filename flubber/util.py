import arrow
from dateutil import tz

def arrow_parse_datetime(value):
    date = arrow.get(value)
    # When we parse a date, we want to parse it in the timezone
    # expected by the user, so that midnight is midnight in the local
    # timezone, not in UTC. Watson Cf issue #16.
    date.tzinfo = tz.tzlocal()
    return date