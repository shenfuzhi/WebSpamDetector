def identify_priority(customer_id):
    priority_code = str(customer_id)[:4]
    if priority_code == '1111':
        return True
    else:
        return False
