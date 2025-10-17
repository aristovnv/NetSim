from dataclasses import dataclass
import datetime
from enum import Enum
from typing import Self

class Season(Enum):
    SPRING = "Spring"
    SUMMER = "Summer"
    AUTUMN = "Autumn"
    WINTER = "Winter"

class DayOfWeek(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

@dataclass
class Day:
    day: int
    month: int
    year: int
    
    def __post_init__(self):
        # Validate the date and create a datetime object for calculations
        self._date = datetime.date(self.year, self.month, self.day)
        self._validate_date()
    
    def _validate_date(self):
        """Ensure the date is valid"""
        if not (1 <= self.month <= 12):
            raise ValueError("Month must be between 1 and 12")
        if not (1 <= self.day <= self.days_in_month):
            raise ValueError(f"Day must be between 1 and {self.days_in_month} for month {self.month}")
    
    @property
    def days_in_month(self) -> int:
        """Get number of days in the current month"""
        if self.month in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        elif self.month in [4, 6, 9, 11]:
            return 30
        else:  # February
            if self._is_leap_year():
                return 29
            else:
                return 28
    
    def _is_leap_year(self) -> bool:
        """Check if current year is a leap year"""
        return (self.year % 4 == 0 and self.year % 100 != 0) or (self.year % 400 == 0)
    
    @property
    def season(self) -> Season:
        """Get the season based on month"""
        if self.month in [12, 1, 2]:
            return Season.WINTER
        elif self.month in [3, 4, 5]:
            return Season.SPRING
        elif self.month in [6, 7, 8]:
            return Season.SUMMER
        else:  # 9, 10, 11
            return Season.AUTUMN
    
    @property
    def day_of_week(self) -> DayOfWeek:
        """Get day of the week (0=Monday, 6=Sunday)"""
        # datetime.weekday() returns 0=Monday, 6=Sunday
        return DayOfWeek(self._date.weekday())
    
    @property
    def day_of_year(self) -> int:
        """Get day of the year (1-365/366)"""
        return self._date.timetuple().tm_yday
    
    @property
    def week_of_year(self) -> int:
        """Get week number of the year (ISO 8601)"""
        return self._date.isocalendar()[1]
    
    @property
    def week_of_month(self) -> int:
        """Get week number within the month (1-5)"""
        first_day = datetime.date(self.year, self.month, 1)
        # Calculate how many days from the first day, then convert to weeks
        days_from_start = self.day - 1
        # Week starts from Monday (ISO 8601)
        first_day_weekday = first_day.weekday()  # 0=Monday, 6=Sunday
        
        # Calculate the week number in month
        week_in_month = (days_from_start + first_day_weekday) // 7 + 1
        return week_in_month
    
    def add_day(self) -> Self:
        """Move to the next day, updating all properties"""
        next_date = self._date + datetime.timedelta(days=1)
        return Day(day=next_date.day, month=next_date.month, year=next_date.year)
    
    def __str__(self) -> str:
        return f"{self.day:02d}/{self.month:02d}/{self.year} ({self.day_of_week.name})"
    
    def __repr__(self) -> str:
        return f"Day(day={self.day}, month={self.month}, year={self.year})"
