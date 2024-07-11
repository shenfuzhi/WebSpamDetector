import re
import datetime
import uuid

def is_valid_time_format(_time):
    pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$'
    if not re.match(pattern, _time):
        return False
    
    # Try to parse the timestamp using ISO 8601 format, which is compatible with RFC3339.
    try:
        parsed_time = datetime.datetime.fromisoformat(_time.replace("Z", "+00:00"))
        return True  # The timestamp is valid
    except ValueError:
        return False

def is_valid_email_format(_email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    
    if re.match(pattern, _email):
        return True
    else:
        return False

def is_valid_UUID4_format(_uuid):
    try:
        uuid_obj = uuid.UUID(_uuid, version=4)
        return True
    except ValueError:
        return False