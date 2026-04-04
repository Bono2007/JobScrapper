from enum import Enum


class JobStatus(str, Enum):
    NEW = "new"
    SEEN = "seen"
    INTERESTED = "interested"
    REJECTED = "rejected"
