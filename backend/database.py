import json
import re
from datetime import datetime
from threading import RLock
from typing import Any

import boto3
from botocore.exceptions import ClientError

from backend.config import settings


class _NoopMetaData:
    def create_all(self, bind=None):
        return None


class _NoopBase:
    metadata = _NoopMetaData()


# Backward compatibility for modules not yet migrated from SQLAlchemy.
Base = _NoopBase
engine = None
SessionLocal = None


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return {"__datetime__": value.isoformat()}
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    return value


def _deserialize_value(value: Any) -> Any:
    if isinstance(value, dict):
        if "__datetime__" in value:
            try:
                return datetime.fromisoformat(value["__datetime__"])
            except ValueError:
                return value["__datetime__"]
        return {k: _deserialize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_deserialize_value(v) for v in value]
    return value


class S3Cursor:
    def __init__(self, documents: list[dict]):
        self._documents = documents

    def skip(self, value: int):
        self._documents = self._documents[value:]
        return self

    def limit(self, value: int):
        self._documents = self._documents[:value]
        return self

    def __iter__(self):
        return iter(self._documents)


class S3Collection:
    def __init__(self, store: "S3DocumentStore", name: str):
        self._store = store
        self._name = name

    def create_index(self, *_args, **_kwargs):
        return None

    def find(self, filter_query: dict | None = None, projection: dict | None = None):
        docs = self._store._load_collection(self._name)
        matched = [
            self._store._apply_projection(doc, projection)
            for doc in docs
            if self._store._matches_filter(doc, filter_query or {})
        ]
        return S3Cursor(matched)

    def find_one(self, filter_query: dict | None = None, projection: dict | None = None):
        docs = self._store._load_collection(self._name)
        for doc in docs:
            if self._store._matches_filter(doc, filter_query or {}):
                return self._store._apply_projection(doc, projection)
        return None

    def insert_one(self, document: dict):
        docs = self._store._load_collection(self._name)
        docs.append(dict(document))
        self._store._save_collection(self._name, docs)
        return {"inserted_id": document.get("id")}

    def update_one(self, filter_query: dict, update_query: dict):
        docs = self._store._load_collection(self._name)
        updated = 0
        set_values = update_query.get("$set", {})

        for idx, doc in enumerate(docs):
            if self._store._matches_filter(doc, filter_query):
                docs[idx] = {**doc, **set_values}
                updated = 1
                break

        if updated:
            self._store._save_collection(self._name, docs)
        return {"matched_count": updated, "modified_count": updated}

    def count_documents(self, filter_query: dict | None = None):
        docs = self._store._load_collection(self._name)
        return sum(1 for doc in docs if self._store._matches_filter(doc, filter_query or {}))

    def aggregate(self, pipeline: list[dict]):
        docs = self._store._load_collection(self._name)
        result = docs

        for stage in pipeline:
            if "$match" in stage:
                match_filter = stage["$match"]
                result = [doc for doc in result if self._store._matches_filter(doc, match_filter)]
            elif "$group" in stage:
                result = self._store._aggregate_group(result, stage["$group"])
            elif "$sort" in stage:
                sort_by = stage["$sort"]
                for field, direction in reversed(list(sort_by.items())):
                    reverse = direction == -1
                    result = sorted(result, key=lambda d: d.get(field), reverse=reverse)

        return S3Cursor(result)


class S3DocumentStore:
    def __init__(self):
        self._bucket = settings.AWS_S3_BUCKET
        self._prefix = settings.AWS_S3_PREFIX.strip("/")
        self._client = boto3.client("s3", region_name=settings.AWS_REGION)
        self._lock = RLock()

        self.users = S3Collection(self, "users")
        self.companies = S3Collection(self, "companies")
        self.placements = S3Collection(self, "placements")
        self.counters = S3Collection(self, "counters")

    def _collection_key(self, name: str) -> str:
        base = f"{self._prefix}/" if self._prefix else ""
        return f"{base}{name}.json"

    def _load_collection(self, name: str) -> list[dict]:
        key = self._collection_key(name)
        with self._lock:
            try:
                obj = self._client.get_object(Bucket=self._bucket, Key=key)
                payload = obj["Body"].read().decode("utf-8")
                data = json.loads(payload)
                return [_deserialize_value(item) for item in data]
            except ClientError as exc:
                code = exc.response.get("Error", {}).get("Code")
                if code in {"NoSuchKey", "404"}:
                    return []
                raise

    def _save_collection(self, name: str, documents: list[dict]):
        key = self._collection_key(name)
        with self._lock:
            payload = json.dumps([_serialize_value(item) for item in documents], default=str)
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=payload.encode("utf-8"),
                ContentType="application/json",
            )

    @staticmethod
    def _apply_projection(document: dict, projection: dict | None) -> dict:
        output = dict(document)
        if not projection:
            return output

        include_fields = {k for k, v in projection.items() if v == 1}
        exclude_fields = {k for k, v in projection.items() if v == 0}

        if include_fields:
            projected = {k: output.get(k) for k in include_fields if k in output}
            if projection.get("_id", 1) == 1 and "_id" in output:
                projected["_id"] = output["_id"]
            return projected

        for field in exclude_fields:
            output.pop(field, None)
        return output

    @staticmethod
    def _matches_filter(document: dict, filter_query: dict) -> bool:
        if not filter_query:
            return True

        for key, condition in filter_query.items():
            if key == "$or":
                if not any(S3DocumentStore._matches_filter(document, sub) for sub in condition):
                    return False
                continue

            value = document.get(key)

            if isinstance(condition, dict):
                if "$regex" in condition:
                    options = condition.get("$options", "")
                    flags = re.IGNORECASE if "i" in options else 0
                    pattern = condition["$regex"]
                    if value is None or re.search(pattern, str(value), flags=flags) is None:
                        return False
                if "$gte" in condition and (value is None or value < condition["$gte"]):
                    return False
                if "$in" in condition and value not in condition["$in"]:
                    return False
                if "$nin" in condition and value in condition["$nin"]:
                    return False
                if "$ne" in condition and value == condition["$ne"]:
                    return False
            else:
                if value != condition:
                    return False

        return True

    @staticmethod
    def _aggregate_group(documents: list[dict], group_spec: dict) -> list[dict]:
        group_field = (group_spec.get("_id") or "").lstrip("$")
        grouped: dict[Any, list[dict]] = {}

        for doc in documents:
            group_value = doc.get(group_field)
            grouped.setdefault(group_value, []).append(doc)

        output = []
        for group_value, group_docs in grouped.items():
            row = {"_id": group_value}
            for out_field, expr in group_spec.items():
                if out_field == "_id":
                    continue

                if "$sum" in expr and expr["$sum"] == 1:
                    row[out_field] = len(group_docs)
                elif "$avg" in expr:
                    avg_field = expr["$avg"].lstrip("$")
                    values = [doc.get(avg_field) for doc in group_docs if doc.get(avg_field) is not None]
                    row[out_field] = (sum(values) / len(values)) if values else None
                elif "$max" in expr:
                    max_field = expr["$max"].lstrip("$")
                    values = [doc.get(max_field) for doc in group_docs if doc.get(max_field) is not None]
                    row[out_field] = max(values) if values else None

            output.append(row)

        return output


mongo_db = S3DocumentStore()


def init_database():
    """Initialize S3 collection objects used by the application."""
    mongo_db.users.create_index("id", unique=True)
    mongo_db.users.create_index("email", unique=True)
    mongo_db.users.create_index("username", unique=True)
    mongo_db.users.create_index("phone_number", sparse=True)

    mongo_db.companies.create_index("id", unique=True)
    mongo_db.companies.create_index("name", unique=True)

    mongo_db.placements.create_index("id", unique=True)
    mongo_db.placements.create_index("company_id")
    mongo_db.placements.create_index("student_name")
    mongo_db.placements.create_index("graduation_year")


def get_next_sequence(sequence_name: str) -> int:
    """Auto-increment IDs using counters stored in S3."""
    counter = mongo_db.counters.find_one({"_id": sequence_name})
    current = int(counter.get("seq", 0)) if counter else 0
    next_value = current + 1

    if counter:
        mongo_db.counters.update_one({"_id": sequence_name}, {"$set": {"seq": next_value}})
    else:
        mongo_db.counters.insert_one({"_id": sequence_name, "seq": next_value})

    return next_value


def clean_mongo_doc(document: dict) -> dict:
    """Remove Mongo internal keys to keep API responses stable."""
    if not document:
        return document
    output = dict(document)
    output.pop("_id", None)
    return output


# Dependency
def get_db():
    yield mongo_db
