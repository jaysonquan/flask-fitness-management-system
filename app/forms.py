from datetime import datetime


def parse_int(value):
    value = (value or "").strip()
    return int(value) if value else None


def parse_float(value):
    value = (value or "").strip()
    return float(value) if value else None


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()
