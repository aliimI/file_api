# Secure File Vault API

Backend service built with **FastAPI**, **SQLAlchemy (async)**, **PostgreSQL**, and **AWS S3** integration.  
It provides secure file upload, download, and management with background thumbnail generation using **Celery + RabbitMQ**

## Features
- User authentication and RBAC
- Upload files directly to S3 with presigned URLs
- Background thumbnail creation for images(for previews)
- List, download, and delete user files
- PostgreSQL database with Alembic migrations
