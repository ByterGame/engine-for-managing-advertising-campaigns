from enum import Enum

class Statuses(Enum):
    ACTIVE = "active"
    PAUSED = "paused"

    def __str__(self):
        return self.value