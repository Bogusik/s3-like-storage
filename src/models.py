import awssig

import logging

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database.db import Base


logger = logging.getLogger(__name__)


class Bucket(Base):
    __tablename__ = "buckets"

    name = Column(String, primary_key=True, index=True)
    access_key = Column(String, nullable=True)
    secret_key = Column(String, nullable=True)
    blobs = relationship("Blob", back_populates="bucket")

    async def verify_request(self, request):
        v = awssig.AWSSigV4Verifier(
            request_method=request.method,
            uri_path=request.url.path,
            query_string=request.url.query,
            headers=dict(request.headers),
            body=await request.body(),
            region="us-east-1",
            service="s3",
            key_mapping={self.access_key: self.secret_key},
            timestamp_mismatch=None
        )

        try:
            v.verify()
            return True
        except awssig.InvalidSignatureError as e:
            logger.warning('Invalid signature: %s', e)
        except Exception as e:
            logger.error('Unable to verify request: %s', e)

        return False

    def __repr__(self) -> str:
        return self.name


class Blob(Base):
    __tablename__ = "blobs"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String)
    bucket_id = Column(Integer, ForeignKey('buckets.name'))
    bucket = relationship("Bucket", back_populates="blobs")

    content_type = Column(String, default='')
    size = Column(Integer, default=0)

    created_on = Column(DateTime, server_default=func.now())
    updated_on = Column(DateTime, onupdate=func.now())

    def __repr__(self) -> str:
        return self.path
