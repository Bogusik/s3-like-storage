# Simple S3like storage

## Installation

```bash
    python -m venv venv                 # Create venv
    source venv/bin/activate            # Activate venv
    pip3 install -r requirements.txt    # Install dependencies
    uvicorn main:app                    # Run server
```

## Create bucket

To create bucket:

```HTTP
POST / HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Content-Length: 24

{
    "name": "bucket"
}
```

You will get back 

```json
{
    "access_key": "<generated_access_key>",
    "name": "bucket",
    "secret_key": "<generated_secret_key>"
}
```