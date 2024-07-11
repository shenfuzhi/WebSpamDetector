# SpamOverflow Software Architecture



This project was developed for the course CSSE6400 - Software Architecture. It uses a AWS to provide a API that can be used to scan and filter emails for spam using the spamhammer binary (this binary was provided by the course and was just a placeholder). The API supports autoscaling and instant deployment with terraform. See the spec for the exact details.

## Context



mail filtering software can filter email as it arrives or after. SpamOverflow will implement a service that does not impede the flow of traffic (i.e. does not prevent the email arriving). It will receive an API call when the mail server receives an email message. The service then pulls the email from the user’s inbox as fast as it can to prevent the user from seeing the malicious email or clicking any links. Commercial email providers send an API request for each email received. For optimal performance this service needs to be able to handle a large number of requests in a short period of time, so as to not miss any emails. Since these emails can be dangerous, the service must be able to report that it is bad or good in a timely manner. Though genuine emails that are incorrectly marked as dangerous should be returned to the user as quickly as possible. Persistence is an important characteristic of the platform. Customers will want to analyse why emails were flagged after the fact. Upon receiving an email scan request, and after filtering, the system must guarantee that the data has been saved to persistent storage before returning a success response.

## Project Overview



The application supports:

- Scanning emails via API requests.
- Providing access to a REST API for front-end interfaces and internal teams.
- Maintaining responsiveness while scanning emails.

The service is deployed to AWS and undergoes automated correctness and load-testing to ensure all requirements are met.

## Usage



### Running Locally



To build and run the service locally, use the provided `local.sh` script:

```
./local.sh
```



### Deployment to AWS



To deploy the service to AWS, use the `deploy.sh` script:

```
./deploy.sh
```



Ensure that AWS credentials are correctly set up and included in the repository's top-level directory as `credentials`.