import calendar
from datetime import datetime, timedelta

MACHINE = "DISCOVER"

DURATION_UNIT_FIELD_MAX = {
    "days": 99,
    "months": 99,
    "years": 9999,
}


class DurationHelper:
    """Utility class for formatting and manipulating experiment duration and dates."""

    @staticmethod
    def build_duration_string(value: int, unit: str, time_str: str = "000000") -> str:
        if unit not in DURATION_UNIT_FIELD_MAX:
            raise ValueError(f"Unknown duration unit '{unit}'. Valid: {', '.join(DURATION_UNIT_FIELD_MAX)}")
        if value > DURATION_UNIT_FIELD_MAX[unit]:
            raise ValueError(f"Duration value {value} exceeds field limit for {unit}")

        if unit == "years":
            yyyymmdd = f"{value:04d}0000"
        elif unit == "months":
            yyyymmdd = f"0000{value:02d}00"
        else:
            yyyymmdd = f"000000{value:02d}"

        return f"{yyyymmdd} {time_str}"

    @staticmethod
    def add_duration(dt: datetime, value: int, unit: str) -> datetime:
        if unit == "days":
            return dt + timedelta(days=value)
        elif unit == "months":
            total_months = dt.month - 1 + value
            year = dt.year + total_months // 12
            month = total_months % 12 + 1
            day = min(dt.day, calendar.monthrange(year, month)[1])
            return dt.replace(year=year, month=month, day=day)
        elif unit == "years":
            try:
                return dt.replace(year=dt.year + value)
            except ValueError:
                return dt.replace(year=dt.year + value, day=28)
        else:
            raise ValueError(f"Unknown duration unit '{unit}'")
