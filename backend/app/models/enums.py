# Enum Definitions
# All enum types used across the application

import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    PUBLIC = "public" 
    GUEST = "guest"

class SubscriptionPlan(enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class AssetType(enum.Enum):
    CRYPTO = "crypto"
    STABLECOIN = "stablecoin"
    MACRO = "macro"
    INDEX = "index"

class TimeframeEnum(enum.Enum):
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"

class Regime(enum.Enum):
    BULL = "Bull"
    BEAR = "Bear"
    SIDEWAYS = "Sideways"
    TRANSITION = "Transition"
    ACCUMULATION = "Accumulation"
    DISTRIBUTION = "Distribution"

class JobStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class JobCategory(enum.Enum):
    TRAINING = "training"
    PREDICTION = "prediction"
    EVALUATION = "evaluation"
    OPTIMIZATION = "optimization"
    DEPLOYMENT = "deployment"

class Priority(enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class EvaluationTrigger(enum.Enum):
    JOB_COMPLETION = "job_completion"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    API_REQUEST = "api_request"

class EvaluationStatus(enum.Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    INVALIDATED = "invalidated"

class PerformanceGrade(enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"

class ModelType(enum.Enum):
    MACRO = "macro"
    SECTOR = "sector"
    ASSET = "asset"
    TIMING = "timing"

class ModelStatus(enum.Enum):
    ACTIVE = "active"
    TRAINING = "training"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPRECATED = "deprecated"