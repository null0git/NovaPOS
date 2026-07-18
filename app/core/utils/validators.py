"""Reusable validation helpers, mostly for use inside marshmallow schemas."""
import re

from marshmallow import ValidationError

PHONE_REGEX = re.compile(r"^\+?[0-9\-\s()]{7,20}$")
SKU_REGEX = re.compile(r"^[A-Za-z0-9\-_]{2,50}$")


def validate_positive_number(value):
    if value is None or value < 0:
        raise ValidationError("Value must be a positive number.")


def validate_non_empty_string(value):
    if value is None or not str(value).strip():
        raise ValidationError("This field cannot be empty.")


def validate_phone(value):
    if value and not PHONE_REGEX.match(value):
        raise ValidationError("Invalid phone number format.")


def validate_sku(value):
    if value and not SKU_REGEX.match(value):
        raise ValidationError("SKU may only contain letters, numbers, hyphens and underscores.")
