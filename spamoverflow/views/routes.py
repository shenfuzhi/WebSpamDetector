from flask import Blueprint, jsonify, request, current_app
from spamoverflow.models.customer import Customers
from spamoverflow.models.email_domains import EmailDomains
from spamoverflow.models.emails import Emails
from spamoverflow.models import db
import json, uuid
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
import spamoverflow.controller.detect_invalid_paras as detect
import traceback
from celery.result import AsyncResult 
from spamoverflow.tasks import emails as c_emails
from spamoverflow.controller.priority import identify_priority

# datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

api = Blueprint('api', __name__, url_prefix = '/api/v1')

# @api.errorhandler(500)
# def internal_error(error):
#     tb = traceback.format_exc()
#     # 返回包含堆栈跟踪的JSON响应
#     return jsonify({"error": "内部服务器错误", "traceback": tb}), 500

# @api.errorhandler(503)
# def internal_error(error):
#     tb = traceback.format_exc()
#     # 返回包含堆栈跟踪的JSON响应
#     return jsonify({"error": "内部服务器错误", "traceback": tb}), 503


@api.route('/health')
def health():

    return jsonify('Service is healthy.'),200

@api.route('/customers/<string:customer_id>/emails')
def get_emails(customer_id):

    if not customer_id:
        return jsonify("Invalid customer_id or query parameters."), 400
    if not detect.is_valid_UUID4_format(customer_id):
        return jsonify("Invalid customer_id or query parameters."), 400
    
    limit = request.args.get('limit', default = 100, type = int)
    if not (0<limit and limit<=1000):
        return jsonify("Invalid customer_id or query parameters."), 400
    
    offset = request.args.get('offset', default = 0, type = int)
    if offset<0:
        return jsonify("Invalid customer_id or query parameters."), 400
    
    start = request.args.get('start')
    end = request.args.get('end')

    if start:
        if not detect.is_valid_time_format(start):
                return jsonify("Invalid customer_id or query parameters."), 400

    if end:
        if not detect.is_valid_time_format(end):
            return jsonify("Invalid customer_id or query parameters."), 400
    
    From = request.args.get('from')
    to = request.args.get('to')
    if From:
        if not detect.is_valid_email_format(From):
            return jsonify("Invalid customer_id or query parameters."), 400
    if to:
        if not detect.is_valid_email_format(to):
            return jsonify("Invalid customer_id or query parameters."), 400
    
    state = request.args.get('state')
    states = ['pending', 'scanned', 'failed']
    if state:
        if state not in states:
            return jsonify("Invalid customer_id or query parameters."), 400
        
    only_malicious = request.args.get('only_malicious')
    if only_malicious:
        if only_malicious == "true":
            only_malicious = True
        elif only_malicious == "false":
            only_malicious = False
        else:
            return jsonify("Invalid customer_id or query parameters."), 400
    
    query = Emails.query.filter_by(CustomerID = customer_id)

    if start:
        start = start.replace('T', ' ').split('+')[0]
        query = query.filter(Emails.CreatedAt>=start)
    if end:
        end = end.replace('T', ' ').split('+')[0]
        query = query.filter(Emails.CreatedAt<=end)
    if From:
        query = query.filter(Emails.From == From)
    if to:
        query = query.filter(Emails.To == to)
    if state:
        query = query.filter(Emails.Status == state)
    if only_malicious:
        query = query.filter(Emails.Malicious == only_malicious)

    query = query.limit(limit).offset(offset)

    result = c_emails.get_emails_by_cId(customer_id, query)
    response_data = result

    return jsonify(response_data), 200

@api.route('/customers/<string:customer_id>/emails/<string:id>')
def get_email(customer_id, id):
    if not customer_id:
        return jsonify("Body/Path parameter was malformed or invalid."), 400
    if not detect.is_valid_UUID4_format(customer_id):
        return jsonify("Invalid customer_id or query parameters."), 400
    
    if not id:
        return jsonify("Body/Path parameter was malformed or invalid."), 400

    result = c_emails.get_email_by_eId.delay(customer_id, id)
    customer, email_data, domain_list = result.get()
    if customer is None:
        return jsonify('The requested email for the customer does not exist.'), 404

    if email_data:
        email = Emails(
            ID=email_data.get('ID'),
            EmailID=email_data.get('EmailID'),
            CustomerID=email_data.get('CustomerID'),
            CreatedAt=email_data.get('CreatedAt'),
            UpdatedAt=email_data.get('UpdatedAt'),
            To=email_data.get('To'),
            From=email_data.get('From'),
            Subject=email_data.get('Subject'),
            Status=email_data.get('Status'),
            Malicious=email_data.get('Malicious'),
            Body=email_data.get('Body'),
            SpamHammer=email_data.get('SpamHammer')
        )
    else:
        return jsonify('The requested email for the customer does not exist.'), 404

    response_data = {
        'id': email.EmailID,
        'created_at': email.CreatedAt.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'updated_at': email.UpdatedAt.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'contents': {
            'to': email.To,
            'from': email.From,
            'subject': email.Subject,
        },
        'status': email.Status,
        'malicious': email.Malicious,
        'domains': domain_list,
        'metadata': {
            'spamhammer': email.SpamHammer
        } 
    }
    return jsonify(response_data), 200

@api.route('/customers/<string:customer_id>/emails', methods=['POST'])
def submit_emails(customer_id):
    # if not customer_id:
    #     return jsonify("Body/Path parameter was malformed or invalid."), 400
    created_at = datetime.now(timezone.utc)

    if not detect.is_valid_UUID4_format(customer_id):
        return jsonify("Invalid customer_id or query parameters."), 400
        
    priority = identify_priority(customer_id=customer_id)

    if priority:
        c_emails.process_email_scan.apply_async(args=[customer_id, priority], queue='high-priority')
    else:
        c_emails.process_email_scan.apply_async(args=[customer_id, priority], queue='low-priority')
    

    request_json = request.json
    email_id = uuid.uuid4()

    if request_json.get('contents',{}).get('body') is None:
        return jsonify("Body/Path parameter was malformed or invalid."), 400
    if request_json.get('metadata',{}).get('spamhammer') is None:
        return jsonify("Body/Path parameter was malformed or invalid."), 400

    scan_json = {'id': str(email_id),
                 'content': request_json.get('contents',{}).get('body'),
                 'metadata': request_json.get('metadata',{}).get('spamhammer')
                }

    To = request_json.get('contents',{}).get('to')
    From = request_json.get('contents',{}).get('from')
    Subject = request_json.get('contents',{}).get('subject')
    Body = request_json.get('contents',{}).get('body')

    if To is None:
        return jsonify("Body/Path parameter was malformed or invalid."), 400
    if From is None:
        return jsonify("Body/Path parameter was malformed or invalid."), 400
    if Subject is None:
        return jsonify("Body/Path parameter was malformed or invalid."), 400
    if not detect.is_valid_email_format(To):
        return jsonify("Body/Path parameter was malformed or invalid."), 400
    if not detect.is_valid_email_format(From):
        return jsonify("Body/Path parameter was malformed or invalid."), 400

    spamhammer = request_json.get('metadata',{}).get('spamhammer')

    updated_at = datetime.now(timezone.utc)
    email = Emails(
                    EmailID = str(email_id),
                    CustomerID = str(customer_id),
                    CreatedAt = created_at,
                    UpdatedAt = updated_at,
                    To = To,
                    From = From,
                    Subject = Subject,
                    Status = "scanned",
                    SpamHammer = spamhammer,
                    Body = Body,
                    )
    email_data = email.to_dict()

    if priority:
        result = c_emails.submit_emails_task.apply_async(args=[scan_json, email_data], queue='high-priority')
    else:
        result = c_emails.submit_emails_task.apply_async(args=[scan_json, email_data], queue='low-priority')

    malicious, domains = result.get()

    response_data = {
        'id': email_id,
        'created_at': created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        'updated_at': updated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        'contents': {
            'to': To,
            'from': From,
            'subject': Subject,
        },
        'status': "scanned",
        'malicious': malicious,
        'domains': list(dict.fromkeys(domains)),
        'metadata': {
            'spamhammer': spamhammer
        } 
    }
    return jsonify(response_data), 201


@api.route('/customers/<string:customer_id>/reports/actors')
def get_actors(customer_id):

    result = c_emails.get_actors_sql.delay(customer_id)
    actors = result.get()

    data = [{'id': actor, 'count': count} for actor, count in actors]
    generated_at = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    total = len(data)
    response_data = {
        'generated_at': generated_at,
        'total': total,
        'data': data
    }

    return jsonify(response_data)

@api.route('/customers/<string:customer_id>/reports/domains')
def get_domains(customer_id):
    
    results = c_emails.get_domains_sql(customer_id)
    result = results

    generated_at = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    total_unique_domains = len(result)
    domain_datas = [{"id": domain, "count": count} for domain, count in result]

    response_data = {
        "generated_at": generated_at,
        "total": total_unique_domains,
        "data": domain_datas
    }

    return jsonify(response_data)

@api.route('/customers/<string:customer_id>/reports/recipients')
def get_recipients(customer_id):

    generated_at = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

    results = c_emails.get_recipients_sql.delay(customer_id)
    result = results.get()

    total_recipients = len(result)

    recipients_data = []
    for recipient, count in result:
        recipient_data = {"id": recipient, "count": count}
        recipients_data.append(recipient_data)

    response_data = {
        "generated_at": generated_at,
        "total": total_recipients,
        "data": recipients_data
    }

    return jsonify(response_data)