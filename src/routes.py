import os
from typing import Dict
from fastapi import Depends
from sqlalchemy.orm import Session
from .models import Base, Blob, Bucket
from .schemes import BucketScheme
from .utils import md5
from src.database.db import engine, get_db
from secrets import token_hex
from fastapi import (
    APIRouter, Request, HTTPException, Response
)

router = APIRouter()

Base.metadata.create_all(bind=engine)


@router.get('/{bucket_name}/{path:path}')
async def get(
    bucket_name: str,
    path: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    blob = db.query(Blob).join(Bucket).filter(
        Blob.name == bucket_name and Blob.path == path).first()
    if not blob:
        raise HTTPException(404)
    with open(f'media/{blob.bucket.name}/{blob.path}', 'r') as f:
        return Response(content=f.read(), content_type=blob.content_type)


@router.head('/{bucket_name}/{path:path}')
async def head(
    bucket_name: str,
    path: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    blob = db.query(Blob).join(Bucket).filter(
        Bucket.name == bucket_name and Blob.path == path).first()
    if blob:
        return Response()
    else:
        raise HTTPException(404)


@router.put('/{bucket_name}/{path:path}')
async def put(
    bucket_name: str,
    path: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    bucket = db.query(Bucket).filter(Bucket.name == bucket_name).first()
    if not await bucket.verify_request(request):
        raise HTTPException(403)

    blob = db.query(Blob).join(Bucket).filter(
        Bucket.name == bucket_name and Blob.path == path).first()
    if not blob:
        blob = Blob(
            bucket=bucket,
            path=path
        )
    blob.content_type = request.headers.get('content-type', '')
    blob.size = request.headers.get('content-length', '0')
    db.add(blob)
    body = await request.body()
    if not os.path.exists(os.path.dirname(f'media/{bucket_name}/{path}')):
        try:
            os.makedirs(os.path.dirname(f'media/{bucket_name}/{path}'))
        except OSError:
            raise HTTPException(409)
        except NotADirectoryError:
            raise HTTPException(409)
        except IsADirectoryError:
            raise HTTPException(409)

    file_name = f'media/{bucket_name}/{path}'
    try:
        with open(file_name, 'wb') as f:
            f.write(body)
    except IsADirectoryError:
        raise HTTPException(409)
    return Response(headers={'ETag': md5(file_name)})


@router.post('/')
async def post(
    bucket_info: BucketScheme,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    exists = db.query(Bucket).filter(Bucket.name == bucket_info.name).first()
    if exists:
        raise HTTPException(409)
    access_token = token_hex(16)
    secret_token = token_hex(32)
    bucket = Bucket(
        name=bucket_info.name,
        access_key=access_token,
        secret_key=secret_token
    )
    db.add(bucket)
    db.commit()
    db.refresh(bucket)
    return bucket
