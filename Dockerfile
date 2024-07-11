FROM ubuntu:22.04

ENV CELERY_BROKER_URL=sqs://
ENV AWS_SHARED_CREDENTIALS_FILE=/root/.aws/credentials
# Installing dependencies for running a python application
RUN apt-get update && apt-get install -y python3 python3-pip wget 
# Install pipenv
RUN pip3 install poetry
# Setting the working directory
WORKDIR /app
# Install pipenv dependencies
COPY pyproject.toml ./
RUN poetry install --no-root
# Copying our application into the container
COPY spamoverflow spamoverflow
COPY credentials /root/.aws/credentials
RUN chmod 600 /root/.aws/credentials
# Get the version of spamhammer that matches the architecture of the container
RUN dpkg --print-architecture | grep -q "amd64" && export SPAMHAMMER_ARCH="amd64" || export SPAMHAMMER_ARCH="arm64" && wget https://github.com/CSSE6400/SpamHammer/releases/download/v1.0.0/spamhammer-v1.0.0-linux-${SPAMHAMMER_ARCH} -O spamoverflow/spamhammer && chmod +x spamoverflow/spamhammer
# Running our application
CMD ["bash", "-c", "sleep 10 && poetry run celery --app spamoverflow.tasks.emails worker --loglevel=info & poetry run flask --app spamoverflow run --host 0.0.0.0 --port 8080"]
# CMD ["bash", "-c", "sleep 10 && poetry run flask --app spamoverflow run --host 0.0.0.0 --port 8080"]
# CMD ["poetry", "run", "flask", "--app", "spamoverflow", "run", "--host", "0.0.0.0", "--port", "8080"]