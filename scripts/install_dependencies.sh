#!/bin/bash
set -e

dnf install -y httpd
mkdir -p /var/www/html
