import os 
import requests
 
from celery import Celery 
from kombu import Queue
from flask import current_app
from spamoverflow import create_app
from spamoverflow.models.customer import Customers
from spamoverflow.models.email_domains import EmailDomains
from spamoverflow.models.emails import Emails
from spamoverflow.models import db
from sqlalchemy import func
from spamoverflow.controller.scan_email import scan_spam, extract_urls
from requests.exceptions import Timeout, ConnectTimeout, ReadTimeout
 
celery = Celery(__name__) 
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL") 
celery.conf.result_backend = 'db+' + os.environ.get("SQLALCHEMY_DATABASE_URI", "sqlite:///db.sqlite")

celery.conf.update(
   task_default_queue=os.environ.get("CELERY_DEFAULT_QUEUE", "low-priority"),  # 设置默认队列为低优先级队列
   task_queues=[
      Queue('low-priority', routing_key='low.#'),    # 默认（低优先级）队列
      Queue('high-priority', routing_key='high.#'),  # 高优先级队列
   ],
   task_default_exchange='tasks',
   task_default_routing_key='low.priority',
   task_routes={
      'myapp.tasks.high_priority_task': {'queue': 'high-priority', 'routing_key': 'high.priority'},
   },
   worker_pool='threads',  # 指定使用线程作为工作池
   worker_concurrency=9   # 设置并发线程数，根据您的系统资源和需求调整此值
)


@celery.task(soft_time_limit=120, time_limit=180, autoretry_for=(requests.Timeout,), retry_backoff=True, max_retries=3)
def get_emails_by_cId(customer_id, query):

   app = create_app()  # 获取 Flask 应用实例
   with app.app_context():  # 显式设置应用上下文
   
      emails_data = query.all()

      response_data = []
      for email in emails_data:

         domains = EmailDomains.query.filter_by(EmailID = email.EmailID).all()
         domain_list = [domain.Domain for domain in domains]

         email_data = {
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
         response_data.append(email_data)

      return response_data

@celery.task(soft_time_limit=120, time_limit=180, autoretry_for=(requests.Timeout,), retry_backoff=True, max_retries=3)
def get_email_by_eId(customer_id, id):
   app = create_app()  # 获取 Flask 应用实例
   with app.app_context():  # 显式设置应用上下文
      customer = Customers.query.filter_by(CustomerID=str(customer_id)).first()
      if customer is None:
         return False, None, None
      email = Emails.query.filter_by(CustomerID=str(customer_id), EmailID=id).first()
      if email is None:
         return True, None, None
      domains = EmailDomains.query.filter_by(EmailID=id).all()
      domain_list = [domain.Domain for domain in domains]
      return True, email.to_dict(), domain_list


@celery.task(soft_time_limit=120, time_limit=180, autoretry_for=(requests.Timeout,), retry_backoff=True, max_retries=3)
def process_email_scan(customer_id, priority):
   app = create_app()  # 获取 Flask 应用实例
   with app.app_context():  # 显式设置应用上下文
      customer = Customers.query.filter_by(CustomerID=str(customer_id)).first()

      if customer is None:
         customer = Customers(CustomerID=customer_id,
                        Priority=priority,
                        )

         db.session.add(customer)
         db.session.commit()

@celery.task(soft_time_limit=120, time_limit=180, autoretry_for=(requests.Timeout,), retry_backoff=True, max_retries=3)
def submit_emails_task(scan_json, email_data):
   app = create_app()  # 获取 Flask 应用实例
   with app.app_context():  # 显式设置应用上下文
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
         Body=email_data.get('Body'),
         SpamHammer=email_data.get('SpamHammer')
      )
      result_json = scan_spam(scan_json)
      malicious = result_json.get('malicious')
      email.Malicious = malicious
      db.session.add(email)
      db.session.commit()

      domains = extract_urls(email.Body)
      if malicious:
         for domain in domains:
            new_domain = EmailDomains(EmailID = str(email.EmailID), Domain = domain)
            db.session.add(new_domain)
            db.session.commit()

      return malicious, domains


@celery.task(soft_time_limit=120, time_limit=180, autoretry_for=(requests.Timeout,), retry_backoff=True, max_retries=3)
def get_actors_sql(customer_id):
   app = create_app()  # 获取 Flask 应用实例
   with app.app_context():  # 显式设置应用上下文
      actors = (
        db.session.query(Emails.From, func.count(Emails.From).label('count'))
        .filter(Emails.CustomerID == customer_id, Emails.Malicious == True)
        .group_by(Emails.From)
        .all()
    )
      return actors


@celery.task(soft_time_limit=120, time_limit=180, autoretry_for=(requests.Timeout,), retry_backoff=True, max_retries=3)
def get_domains_sql(customer_id):
   app = create_app()  # 获取 Flask 应用实例
   with app.app_context():  # 显式设置应用上下文
      result = db.session.query(EmailDomains.Domain, func.count(EmailDomains.Domain).label('count')) \
            .join(Emails, EmailDomains.EmailID == Emails.EmailID) \
            .filter(Emails.CustomerID == customer_id, Emails.Malicious == True) \
            .group_by(EmailDomains.Domain) \
            .all()
      return result

@celery.task(soft_time_limit=120, time_limit=180, autoretry_for=(requests.Timeout,), retry_backoff=True, max_retries=3)
def get_recipients_sql(customer_id):
   app = create_app()  # 获取 Flask 应用实例
   with app.app_context():  # 显式设置应用上下文
      result = db.session.query(Emails.To, func.count(Emails.To).label('count')) \
        .filter(Emails.CustomerID == customer_id, Emails.Malicious == True) \
        .group_by(Emails.To) \
        .all()
      return result