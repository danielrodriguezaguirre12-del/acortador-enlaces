"""Acceso a DynamoDB.

Boto3 toma las credenciales automáticamente del rol IAM asociado a la
instancia EC2 (credenciales temporales). No se usan claves en el código.
"""
from __future__ import annotations  # compatibilidad con Python 3.9 (Amazon Linux 2023)

from functools import lru_cache

import boto3

from .config import settings


@lru_cache
def get_table():
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    return dynamodb.Table(settings.table_name)


def save_link(short_code: str, original_url: str, created_at: str) -> None:
    get_table().put_item(
        Item={
            "short_code": short_code,
            "original_url": original_url,
            "created_at": created_at,
        },
        # Evita sobrescribir un registro existente con el mismo UUID
        ConditionExpression="attribute_not_exists(short_code)",
    )


def get_link(short_code: str) -> dict | None:
    response = get_table().get_item(Key={"short_code": short_code})
    return response.get("Item")
