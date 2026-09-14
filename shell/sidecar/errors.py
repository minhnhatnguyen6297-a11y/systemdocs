"""Structured error objects theo desktopcommand.v1 §4.

Flat snake_case codes khớp contract examples (file_scope_not_supported, ...).
"""


class CommandError(Exception):
    """Lỗi nghiệp vụ có cấu trúc — raise trong command handler."""

    def __init__(self, code, message, retryable=False, next_action=None,
                 details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.next_action = next_action
        self.details = details


def error_object(code, message, retryable=False, next_action=None,
                 job_id=None, details=None):
    return {
        "code": code,
        "message": message,
        "retryable": bool(retryable),
        "next_action": next_action,
        "job_id": job_id,
        "details": details,
    }
