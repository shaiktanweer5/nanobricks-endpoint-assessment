import json
import os
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker
)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./nanobricks_endpoint.db"
)


connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False
    }


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


class EndpointRecord(Base):
    __tablename__ = "endpoints"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    hostname = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    operating_system = Column(
        String(255)
    )

    os_version = Column(
        String(255)
    )

    architecture = Column(
        String(100)
    )

    processor = Column(
        Text
    )

    ram_gb = Column(
        String(50)
    )

    disk_total_gb = Column(
        String(50)
    )

    disk_free_gb = Column(
        String(50)
    )

    disk_used_percent = Column(
        String(50)
    )

    pass_count = Column(
        Integer,
        default=0
    )

    review_count = Column(
        Integer,
        default=0
    )

    fail_count = Column(
        Integer,
        default=0
    )

    total_count = Column(
        Integer,
        default=0
    )

    findings_json = Column(
        Text
    )

    agent_json = Column(
        Text
    )

    last_seen_utc = Column(
        DateTime,
        default=lambda: datetime.now(
            timezone.utc
        )
    )


def initialize_database():
    Base.metadata.create_all(
        bind=engine
    )


def save_endpoint(package):
    session = SessionLocal()

    try:
        endpoint = package.get(
            "endpoint",
            {}
        )

        summary = package.get(
            "summary",
            {}
        )

        hostname = endpoint.get(
            "hostname"
        )

        if not hostname:
            raise ValueError(
                "Hostname is required."
            )

        record = (
            session.query(
                EndpointRecord
            )
            .filter(
                EndpointRecord.hostname
                == hostname
            )
            .first()
        )

        if not record:
            record = EndpointRecord(
                hostname=hostname
            )

            session.add(
                record
            )

        record.operating_system = (
            endpoint.get(
                "operating_system"
            )
        )

        record.os_version = (
            endpoint.get(
                "os_version"
            )
        )

        record.architecture = (
            endpoint.get(
                "architecture"
            )
        )

        record.processor = (
            endpoint.get(
                "processor"
            )
        )

        record.ram_gb = str(
            endpoint.get(
                "ram_gb",
                ""
            )
        )

        record.disk_total_gb = str(
            endpoint.get(
                "disk_total_gb",
                ""
            )
        )

        record.disk_free_gb = str(
            endpoint.get(
                "disk_free_gb",
                ""
            )
        )

        record.disk_used_percent = str(
            endpoint.get(
                "disk_used_percent",
                ""
            )
        )

        record.pass_count = (
            summary.get(
                "pass",
                0
            )
        )

        record.review_count = (
            summary.get(
                "review",
                0
            )
        )

        record.fail_count = (
            summary.get(
                "fail",
                0
            )
        )

        record.total_count = (
            summary.get(
                "total",
                0
            )
        )

        record.findings_json = json.dumps(
            package.get(
                "findings",
                []
            )
        )

        record.agent_json = json.dumps(
            package.get(
                "agent",
                {}
            )
        )

        record.last_seen_utc = (
            datetime.now(
                timezone.utc
            )
        )

        session.commit()

        return record

    finally:
        session.close()


def get_all_endpoints():
    session = SessionLocal()

    try:
        records = (
            session.query(
                EndpointRecord
            )
            .order_by(
                EndpointRecord.hostname
            )
            .all()
        )

        endpoints = []

        for record in records:
            endpoints.append(
                {
                    "endpoint": {
                        "hostname":
                            record.hostname,

                        "operating_system":
                            record.operating_system,

                        "os_version":
                            record.os_version,

                        "architecture":
                            record.architecture,

                        "processor":
                            record.processor,

                        "ram_gb":
                            record.ram_gb,

                        "disk_total_gb":
                            record.disk_total_gb,

                        "disk_free_gb":
                            record.disk_free_gb,

                        "disk_used_percent":
                            record.disk_used_percent
                    },

                    "summary": {
                        "pass":
                            record.pass_count,

                        "review":
                            record.review_count,

                        "fail":
                            record.fail_count,

                        "total":
                            record.total_count
                    },

                    "findings":
                        json.loads(
                            record.findings_json
                            or "[]"
                        ),

                    "agent":
                        json.loads(
                            record.agent_json
                            or "{}"
                        ),

                    "_source_type":
                        "Database"
                }
            )

        return endpoints

    finally:
        session.close()


initialize_database()