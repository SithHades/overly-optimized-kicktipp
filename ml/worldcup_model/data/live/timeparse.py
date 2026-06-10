import re
from datetime import UTC, datetime, timezone, timedelta

TIME_WITH_UTC_OFFSET = re.compile(r"^(?P<hour>\d{1,2}):(?P<minute>\d{2}) UTC(?P<offset>[+-]\d{1,2})$")


def parse_openfootball_datetime(date_value: str, time_value: str | None) -> datetime:
    if not time_value:
        return datetime.fromisoformat(date_value).replace(tzinfo=UTC)

    match = TIME_WITH_UTC_OFFSET.match(time_value.strip())
    if not match:
        return datetime.fromisoformat(date_value).replace(tzinfo=UTC)

    offset_hours = int(match.group("offset"))
    tz = timezone(timedelta(hours=offset_hours))
    local_dt = datetime.fromisoformat(date_value).replace(
        hour=int(match.group("hour")),
        minute=int(match.group("minute")),
        tzinfo=tz,
    )
    return local_dt.astimezone(UTC)
