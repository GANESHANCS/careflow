"""
CAREFlow District Anomaly Review & Audit Workflow Models (Phase 15E).
Tracks administrative governance, review status transitions, and immutable audit logs
for statistical anomaly signals without mutating underlying HMIS observations.
"""

from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Float, Integer, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.db.models.user import User


class AnomalyReviewStatus:
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    REOPENED = "REOPENED"

    ALL = {OPEN, ACKNOWLEDGED, UNDER_REVIEW, RESOLVED, REOPENED}
    ACTIVE_STATUSES = {OPEN, ACKNOWLEDGED, UNDER_REVIEW, REOPENED}


class AnomalyReviewActionType:
    ACKNOWLEDGE = "ACKNOWLEDGE"
    SET_UNDER_REVIEW = "SET_UNDER_REVIEW"
    RESOLVE = "RESOLVE"
    REOPEN = "REOPEN"
    ADD_NOTE = "ADD_NOTE"

    ALL = {ACKNOWLEDGE, SET_UNDER_REVIEW, RESOLVE, REOPEN, ADD_NOTE}


class DistrictAnomalyReview(Base, TimestampMixin):
    """
    Administrative review entity tracking governance status of a statistical anomaly signal.
    Preserves mathematical signal provenance while maintaining mutable review state.
    """
    __tablename__ = "district_anomaly_reviews"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    signal_id: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    indicator_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    reporting_month: Mapped[str] = mapped_column(String(7), index=True, nullable=False)
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="WARNING", nullable=False)

    # Review status workflow: OPEN -> ACKNOWLEDGED -> UNDER_REVIEW -> RESOLVED -> REOPENED
    current_status: Mapped[str] = mapped_column(
        String(32), default=AnomalyReviewStatus.OPEN, index=True, nullable=False
    )

    trigger_reason: Mapped[str] = mapped_column(String(512), nullable=False)
    metric_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expected_range: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    assigned_to_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    last_reviewed_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    last_reviewed_by_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_reason: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Relationships
    actions: Mapped[List["DistrictAnomalyReviewAction"]] = relationship(
        "DistrictAnomalyReviewAction",
        back_populates="review",
        cascade="all, delete-orphan",
        order_by="DistrictAnomalyReviewAction.created_at.desc()"
    )

    __table_args__ = (
        Index("idx_anom_review_dist_month", "district", "reporting_month"),
        Index("idx_anom_review_status", "current_status"),
        Index("idx_anom_review_indicator", "indicator_id"),
    )


class DistrictAnomalyReviewAction(Base):
    """
    Immutable audit trail recording every state transition, note, or resolution decision.
    Ensures regulatory compliance and transparent administrative history.
    """
    __tablename__ = "district_anomaly_review_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(
        String(160), ForeignKey("district_anomaly_reviews.id", ondelete="CASCADE"), index=True, nullable=False
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    review: Mapped["DistrictAnomalyReview"] = relationship("DistrictAnomalyReview", back_populates="actions")

    __table_args__ = (
        Index("idx_anom_action_review_id", "review_id"),
        Index("idx_anom_action_created_at", "created_at"),
    )
