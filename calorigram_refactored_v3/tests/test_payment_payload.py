
from handlers.payments import validate_payment_payload

def test_validate_payload_ok():
    payload = "uid=123;plan=premium;amount=499;cur=EUR"
    assert validate_payment_payload(payload, 123, "premium", 499, "EUR") is True

def test_validate_payload_fail_uid():
    payload = "uid=999;plan=premium;amount=499;cur=EUR"
    assert validate_payment_payload(payload, 123, "premium", 499, "EUR") is False
