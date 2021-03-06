import arrow
from dateutil import tz


def arrow_parse_datetime(value):
    date = arrow.get(value, ['YYYY-MM-DD HH:mm:ss', 'YYYY-MM-DD HH:mm'])
    # When we parse a date, we want to parse it in the timezone
    # expected by the user, so that midnight is midnight in the local
    # timezone, not in UTC. Watson Cf issue #16.
    date.tzinfo = tz.tzlocal()
    return date


def beautify_tags(tag_list):
    if len(tag_list) > 0:
        return " [{}]".format(','.join(tag_list))
    else:
        return ""
