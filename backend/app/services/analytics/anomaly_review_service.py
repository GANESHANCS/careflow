"""
CAREFlow District Anomaly Review & Governance Service (Phase 15E).
Coordinates administrative review workflows, role-based authorization,
status transition validation, and immutable audit logs for early-warning signals.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.db.models.anomaly_review import (
    DistrictAnomalyReview,
    DistrictAnomalyReviewAction,
    AnomalyReviewStatus,
    AnomalyReviewActionType,
)
from backend.app.db.models.user import User


class DistrictAnomalyReviewService:
    """Service managing anomaly review status transitions, RBAC, and audit logs."""

    # Valid State Transition Matrix: source_status -> set of allowed target statuses
    VALID_TRANSITIONS = {
        AnomalyReviewStatus.OPEN: {
            AnomalyReviewStatus.ACKNOWLEDGED,
            AnomalyReviewStatus.UNDER_REVIEW,
            AnomalyReviewStatus.RESOLVED,
        },
        AnomalyReviewStatus.ACKNOWLEDGED: {
            AnomalyReviewStatus.UNDER_REVIEW,
            AnomalyReviewStatus.RESOLVED,
            AnomalyReviewStatus.OPEN,
        },
        AnomalyReviewStatus.UNDER_REVIEW: {
            AnomalyReviewStatus.RESOLVED,
            AnomalyReviewStatus.OPEN,
            AnomalyReviewStatus.ACKNOWLEDGED,
        },
        AnomalyReviewStatus.RESOLVED: {
            AnomalyReviewStatus.REOPENED,
        },
        AnomalyReviewStatus.REOPENED: {
            AnomalyReviewStatus.ACKNOWLEDGED,
            AnomalyReviewStatus.UNDER_REVIEW,
            AnomalyReviewStatus.RESOLVED,
        },
    }

    # Action to target status mapping
    ACTION_TO_STATUS = {
        AnomalyReviewActionType.ACKNOWLEDGE: AnomalyReviewStatus.ACKNOWLEDGED,
        AnomalyReviewActionType.SET_UNDER_REVIEW: AnomalyReviewStatus.UNDER_REVIEW,
        AnomalyReviewActionType.RESOLVE: AnomalyReviewStatus.RESOLVED,
        AnomalyReviewActionType.REOPEN: AnomalyReviewStatus.REOPENED,
    }

    @classmethod
    def get_or_create_review(
        cls,
        db: Session,
        signal_id: str,
        district: str,
        indicator_id: str,
        reporting_month: str,
        signal_type: str,
        severity: str,
        trigger_reason: str,
        metric_value: Optional[float] = None,
        expected_range: Optional[str] = None
    ) -> DistrictAnomalyReview:
        """Finds or initializes a persistent review record for a mathematical signal."""
        existing = db.query(DistrictAnomalyReview).filter(
            DistrictAnomalyReview.signal_id == signal_id
        ).first()

        if existing:
            return existing

        now = datetime.now(timezone.utc)
        review = DistrictAnomalyReview(
            id=signal_id,
            signal_id=signal_id,
            district=district,
            indicator_id=indicator_id,
            reporting_month=reporting_month,
            signal_type=signal_type,
            severity=severity,
            current_status=AnomalyReviewStatus.OPEN,
            trigger_reason=trigger_reason,
            metric_value=metric_value,
            expected_range=expected_range,
            created_at=now,
            updated_at=now
        )
        db.add(review)
        db.flush()
        return review

    @classmethod
    def get_review(cls, db: Session, signal_id: str) -> Optional[DistrictAnomalyReview]:
        """Retrieves a review by signal_id."""
        return db.query(DistrictAnomalyReview).filter(
            DistrictAnomalyReview.signal_id == signal_id
        ).first()

    @classmethod
    def list_reviews(
        cls,
        db: Session,
        district: Optional[str] = None,
        indicator_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DistrictAnomalyReview]:
        """Lists anomaly reviews matching optional filters."""
        query = db.query(DistrictAnomalyReview)
        if district:
            query = query.filter(DistrictAnomalyReview.district == district)
        if indicator_id:
            query = query.filter(DistrictAnomalyReview.indicator_id == indicator_id)
        if status_filter:
            query = query.filter(DistrictAnomalyReview.current_status == status_filter)

        return query.order_by(desc(DistrictAnomalyReview.updated_at)).offset(offset).limit(limit).all()

    @classmethod
    def apply_review_action(
        cls,
        db: Session,
        signal_id: str,
        action: str,
        notes: Optional[str],
        current_user: User,
        district: Optional[str] = None,
        indicator_id: Optional[str] = None,
        reporting_month: Optional[str] = None,
        signal_type: Optional[str] = None,
        trigger_reason: Optional[str] = None,
        metric_value: Optional[float] = None,
        expected_range: Optional[str] = None
    ) -> DistrictAnomalyReview:
        """
        Executes a validated administrative review transition, persisting an immutable audit action.
        Enforces role-based authorization (ADMIN or ANALYST required; VIEWER rejected).
        """
        # 1. Enforce RBAC
        user_role = (getattr(current_user, "role", "") or "").upper()
        if user_role not in ("ADMIN", "ANALYST"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user_role}' is not authorized to transition anomaly review status. ADMIN or ANALYST required."
            )

        # 2. Validate Action
        clean_action = str(action).strip().upper()
        if clean_action not in AnomalyReviewActionType.ALL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action '{clean_action}'. Must be one of: {sorted(list(AnomalyReviewActionType.ALL))}"
            )

        # 3. Retrieve or create review
        review = cls.get_review(db, signal_id)
        if not review:
            if not (district and indicator_id and reporting_month and signal_type and trigger_reason):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Anomaly review for signal '{signal_id}' not found and insufficient metadata provided to initialize."
                )
            review = cls.get_or_create_review(
                db=db,
                signal_id=signal_id,
                district=district,
                indicator_id=indicator_id,
                reporting_month=reporting_month,
                signal_type=signal_type,
                severity="WARNING",
                trigger_reason=trigger_reason,
                metric_value=metric_value,
                expected_range=expected_range
            )

        from_status = review.current_status
        now = datetime.now(timezone.utc)

        # 4. Resolve target status and validate transition
        if clean_action == AnomalyReviewActionType.ADD_NOTE:
            to_status = from_status
            if not notes or not notes.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Notes content is required when performing 'ADD_NOTE'."
                )
        else:
            to_status = cls.ACTION_TO_STATUS[clean_action]
            if to_status == from_status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Signal is already in status '{to_status}'."
                )

            allowed_targets = cls.VALID_TRANSITIONS.get(from_status, set())
            if to_status not in allowed_targets:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid transition from '{from_status}' to '{to_status}'. Allowed transitions: {sorted(list(allowed_targets))}"
                )

        # 5. Create immutable audit action
        action_log = DistrictAnomalyReviewAction(
            review_id=review.id,
            action=clean_action,
            from_status=from_status,
            to_status=to_status,
            notes=notes.strip() if notes else None,
            user_id=current_user.id,
            username=current_user.username,
            created_at=now
        )
        db.add(action_log)

        # 6. Mutate review status
        review.current_status = to_status
        review.last_reviewed_by_user_id = current_user.id
        review.last_reviewed_by_username = current_user.username
        review.last_reviewed_at = now
        review.updated_at = now

        if clean_action == AnomalyReviewActionType.RESOLVE:
            review.resolution_reason = notes.strip() if notes else "Resolved by reviewer"
        elif clean_action == AnomalyReviewActionType.REOPEN:
            review.resolution_reason = None

        db.commit()
        db.refresh(review)
        return review
