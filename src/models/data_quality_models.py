"""
Data Quality Models
===================

Models for tracking data quality, sources, and validation in the enhanced context API.
"""

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from src.common.time_utils import now_ist_naive


class DataSource(str, Enum):
    """Source of data."""

    REAL_API = "real_api"  # Real data from API
    CALCULATED = "calculated"  # Calculated from real data
    APPROXIMATED = "approximated"  # Approximated due to data limitations
    FALLBACK = "fallback"  # Fallback/default data
    CACHED = "cached"  # Cached data
    CONFIG = "config"  # From configuration


class DataQualityLevel(str, Enum):
    """Quality level of data."""

    HIGH = "high"  # Real data from API, fresh
    GOOD = "good"  # Calculated/approximated from real data
    MEDIUM = "medium"  # Mixed real + approximated
    LOW = "low"  # Mostly fallback data
    FALLBACK = "fallback"  # All fallback data


class DataSourceInfo(BaseModel):
    """Information about data source and quality."""

    source: DataSource
    quality: DataQualityLevel
    timestamp: datetime = Field(default_factory=now_ist_naive)
    api_name: Optional[str] = None
    is_real: bool = Field(..., description="Is this real data (not fallback)?")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in data")
    notes: Optional[str] = None


class ContextDataQuality(BaseModel):
    """
    Data quality report for enhanced market context.

    Clearly indicates what data is real vs approximated vs fallback.
    """

    # Overall quality
    overall_quality: DataQualityLevel
    overall_confidence: float = Field(..., ge=0.0, le=1.0)

    # Primary context quality
    global_markets_source: DataSourceInfo
    indian_markets_source: DataSourceInfo

    # Detailed context quality
    technicals_source: Optional[DataSourceInfo] = None
    sectors_source: Optional[DataSourceInfo] = None
    market_breadth_source: Optional[DataSourceInfo] = None

    # Style-specific quality
    intraday_data_source: Optional[DataSourceInfo] = None
    swing_data_source: Optional[DataSourceInfo] = None
    longterm_data_source: Optional[DataSourceInfo] = None

    # API health
    yahoo_finance_available: bool
    kite_connect_available: bool

    # Warnings and issues
    warnings: List[str] = Field(default_factory=list)
    approximations: List[str] = Field(default_factory=list)
    fallbacks: List[str] = Field(default_factory=list)

    # Timestamps
    data_age_seconds: int = Field(..., description="Age of oldest data point")
    generated_at: datetime = Field(default_factory=now_ist_naive)


class ValidationResult(BaseModel):
    """Result of data validation."""

    is_valid: bool
    field_name: str
    value: Any
    source: DataSource
    quality: DataQualityLevel
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class DataQualityReport(BaseModel):
    """
    Comprehensive data quality report.

    Use this to understand exactly what data is real and what is approximated.
    """

    # Summary
    total_fields: int
    real_data_fields: int
    approximated_fields: int
    fallback_fields: int

    # Percentages
    real_data_percentage: float
    approximated_percentage: float
    fallback_percentage: float

    # Quality metrics
    overall_quality_score: float = Field(..., ge=0.0, le=1.0)
    data_completeness: float = Field(..., ge=0.0, le=1.0)

    # Detailed validation results
    validation_results: List[ValidationResult] = Field(default_factory=list)

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)

    # Timestamp
    generated_at: datetime = Field(default_factory=now_ist_naive)
