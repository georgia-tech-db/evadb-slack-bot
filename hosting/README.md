# Introduction

We go over how to host slack client in this document.

# Infrasturcture

We use Flask + Gunicorn + Nginx infrastucture to host this application. Flask is a single thread application. Gunicorn makes it production-ready by running it behind multiple threads, but the service is only exposed internally. We expose the `HTTP` and `HTTPS` service to outside (ports `80` and `443`) through Nginx. Nginx serves as a proxy to direct traffic to internal Gunicorn.

# Step-by-step Instruction for Azure

We deploy our service on Azure, but the same should apply for any other cloud services.

## Open Port

Allow inbound traffic from any IP range to port `80` (`HTTP`) and to port `443` (`HTTPS`).

## Setup DNS (Optional)

It would be easier to let others to access serviecs through a DNS name than directly allowing others to access our services through IP address. Check [Azure tutorial](https://learn.microsoft.com/en-us/azure/virtual-machines/create-fqdn) about how to create a DNS name for VM.

## Install Required Services

```bash
sudo apt install nginx
pip install gunicorn
```

## Generate SSL for HTTPS Service

Generate SSL certificate for our VM. The path is compatible to the `exmaple.conf` of Nginx. If you generate SSL at different paths, please update the SSL path in the configuration file.

> :warning: During SSL generation, the common name should be the same as the VM DNS name.

```bash
sudo mkdir /etc/nginx/ssl
cd /etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx.key -out nginx.crt
```

## Add Nginx Configuration

First, you need to update the `server_name` field to your VM DNS name.

Then, move the configuration file to default Nginx configuration path.
```bash
mv example.conf /etc/nginx/conf.d/flask.conf
```

Verify the configuration is correct and restart nginx service.
```bash
sudo nginx -t
sudo systemctl restart nginx
```

Verify the Nginx is running.
```bash
sudo systemctl status nginx
```

## Start Flask Service
```bash
gunicorn --bind 127.0.0.1 slack_client:flask_app --log-level DEBUG
```