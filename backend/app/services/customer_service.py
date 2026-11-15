from typing import Any, Dict, List, Optional, Tuple

from backend.app.models.customer import Customer
from backend.app.utils.validators import validate_email, validate_required_fields, sanitize_string
from backend.app.utils.logger import app_logger


def get_customers(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    return Customer.get_all(limit=limit, offset=offset)


def get_customer(customer_id: int) -> Optional[Dict[str, Any]]:
    return Customer.get_by_id(customer_id)


def create_customer(data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
    error = validate_required_fields(data, ["first_name", "last_name", "email"])
    if error:
        return False, error, None

    if not validate_email(data["email"]):
        return False, "Invalid email address", None

    data["first_name"] = sanitize_string(data["first_name"])
    data["last_name"] = sanitize_string(data["last_name"])
    data["email"] = sanitize_string(data["email"]).lower()

    customer_id = Customer.create(data)
    app_logger.info("Customer created: id=%s email=%s", customer_id, data["email"])
    return True, "Customer created", customer_id


def update_customer(customer_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
    if not Customer.get_by_id(customer_id):
        return False, "Customer not found"

    if "email" in data and not validate_email(data["email"]):
        return False, "Invalid email address"

    Customer.update(customer_id, data)
    app_logger.info("Customer updated: id=%s", customer_id)
    return True, "Customer updated"


def delete_customer(customer_id: int) -> Tuple[bool, str]:
    if not Customer.get_by_id(customer_id):
        return False, "Customer not found"
    Customer.delete(customer_id)
    app_logger.info("Customer deleted: id=%s", customer_id)
    return True, "Customer deleted"
