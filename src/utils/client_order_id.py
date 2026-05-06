import re
from datetime import UTC, datetime

CLIENT_ORDER_ID_MAX_LENGTH = 36
CLIENT_ORDER_ID_DATETIME_FORMAT = "%Y%m%d%H%M%S"
CLIENT_ORDER_ID_DATETIME_LENGTH = 14
# GMO Coin FX limits client_order_id to 36 characters. Reserve the final
# 14 characters for the yyyyMMddHHmmss timestamp suffix used for uniqueness.
CLIENT_ORDER_ID_PREFIX_MAX_LENGTH = (
    CLIENT_ORDER_ID_MAX_LENGTH - CLIENT_ORDER_ID_DATETIME_LENGTH
)
CLIENT_ORDER_ID_PREFIX_PATTERN = re.compile(r"^[A-Za-z0-9]+$")


class ClientOrderIdGenerator:
    def __init__(self, prefix: str):
        self._validate_prefix(prefix)
        self.prefix = prefix

    @staticmethod
    def _validate_prefix(prefix: str) -> None:
        if len(prefix) > CLIENT_ORDER_ID_PREFIX_MAX_LENGTH:
            raise ValueError(
                "client_order_id_prefix must be less than or equal to "
                f"{CLIENT_ORDER_ID_PREFIX_MAX_LENGTH} characters"
            )
        if not CLIENT_ORDER_ID_PREFIX_PATTERN.fullmatch(prefix):
            raise ValueError(
                "client_order_id_prefix must contain only ASCII letters and numbers"
            )

    def generate(self) -> str:
        now = datetime.now(UTC)

        return f"{self.prefix}{now.strftime(CLIENT_ORDER_ID_DATETIME_FORMAT)}"
