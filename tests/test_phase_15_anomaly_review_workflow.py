"""
Tests for Phase 15E: District Anomaly Review & Governance Workflow.
Tests status transitions, role-based authorization, immutable audit trail, and validation logic.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.db.models.anomaly_review import (
    DistrictAnomalyReview,
    DistrictAnomalyReviewAction,
    AnomalyReviewStatus,
    AnomalyReviewActionType,
)
from backend.app.db.models.user import User
from backend.app.services.analytics.anomaly_review_service import DistrictAnomalyReviewService


@pytest.fixture
def test_users(db_session: Session):
    """Provides test users with different RBAC roles."""
    admin = db_session.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(username="admin_test", role="ADMIN", hashed_password="pw", is_active=True)
        db_session.add(admin)

    analyst = User(username="analyst_test", role="ANALYST", hashed_password="pw", is_active=True)
    viewer = User(username="viewer_test", role="VIEWER", hashed_password="pw", is_active=True)
    db_session.add(analyst)
    db_session.add(viewer)
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(analyst)
    db_session.refresh(viewer)
    return {"admin": admin, "analyst": analyst, "viewer": viewer}


def test_anomaly_review_workflow_lifecycle(db_session: Session, test_users):
    """Tests the full lifecycle of an anomaly review: OPEN -> ACKNOWLEDGED -> UNDER_REVIEW -> RESOLVED -> REOPENED."""
    sig_id = "SIG_TEST_ARIYALUR_1.1_2016-03"
    analyst = test_users["analyst"]
    admin = test_users["admin"]

    # 1. Create or get initial review
    review = DistrictAnomalyReviewService.get_or_create_review(
        db=db_session,
        signal_id=sig_id,
        district="Ariyalur",
        indicator_id="1.1",
        reporting_month="2016-03",
        signal_type="HISTORICAL_OUTLIER_MAD",
        severity="WARNING",
        trigger_reason="Observed value exceeds 4.0x historical MAD.",
        metric_value=4500.0,
        expected_range="[800.0 - 1200.0]"
    )
    assert review.current_status == AnomalyReviewStatus.OPEN
    assert review.signal_id == sig_id

    # 2. Acknowledge the signal
    review = DistrictAnomalyReviewService.apply_review_action(
        db=db_session,
        signal_id=sig_id,
        action=AnomalyReviewActionType.ACKNOWLEDGE,
        notes="Signal acknowledged by district reporting team.",
        current_user=analyst
    )
    assert review.current_status == AnomalyReviewStatus.ACKNOWLEDGED
    assert review.last_reviewed_by_username == analyst.username

    # 3. Mark as under review
    review = DistrictAnomalyReviewService.apply_review_action(
        db=db_session,
        signal_id=sig_id,
        action=AnomalyReviewActionType.SET_UNDER_REVIEW,
        notes="Field team verifying PHC registers.",
        current_user=analyst
    )
    assert review.current_status == AnomalyReviewStatus.UNDER_REVIEW

    # 4. Resolve the signal
    review = DistrictAnomalyReviewService.apply_review_action(
        db=db_session,
        signal_id=sig_id,
        action=AnomalyReviewActionType.RESOLVE,
        notes="Confirmed catch-up reporting from primary healthcare center following flood delay.",
        current_user=admin
    )
    assert review.current_status == AnomalyReviewStatus.RESOLVED
    assert review.resolution_reason == "Confirmed catch-up reporting from primary healthcare center following flood delay."

    # 5. Reopen the signal
    review = DistrictAnomalyReviewService.apply_review_action(
        db=db_session,
        signal_id=sig_id,
        action=AnomalyReviewActionType.REOPEN,
        notes="Secondary audit requested by state directorate.",
        current_user=admin
    )
    assert review.current_status == AnomalyReviewStatus.REOPENED
    assert review.resolution_reason is None

    # 6. Verify immutable audit trail actions
    actions = db_session.query(DistrictAnomalyReviewAction).filter(
        DistrictAnomalyReviewAction.review_id == review.id
    ).order_by(DistrictAnomalyReviewAction.created_at.asc()).all()

    assert len(actions) == 4
    assert actions[0].action == "ACKNOWLEDGE"
    assert actions[0].from_status == "OPEN"
    assert actions[0].to_status == "ACKNOWLEDGED"

    assert actions[1].action == "SET_UNDER_REVIEW"
    assert actions[1].from_status == "ACKNOWLEDGED"
    assert actions[1].to_status == "UNDER_REVIEW"

    assert actions[2].action == "RESOLVE"
    assert actions[2].from_status == "UNDER_REVIEW"
    assert actions[2].to_status == "RESOLVED"

    assert actions[3].action == "REOPEN"
    assert actions[3].from_status == "RESOLVED"
    assert actions[3].to_status == "REOPENED"


def test_anomaly_review_rbac_enforcement(db_session: Session, test_users):
    """Verifies that VIEWER role is blocked with HTTP 403 from executing state transitions."""
    sig_id = "SIG_RBAC_TEST_01"
    viewer = test_users["viewer"]

    # Pre-create review
    DistrictAnomalyReviewService.get_or_create_review(
        db=db_session,
        signal_id=sig_id,
        district="Ariyalur",
        indicator_id="1.1",
        reporting_month="2016-03",
        signal_type="MOM_SHIFT",
        severity="WARNING",
        trigger_reason="Test reason"
    )

    with pytest.raises(HTTPException) as exc_info:
        DistrictAnomalyReviewService.apply_review_action(
            db=db_session,
            signal_id=sig_id,
            action=AnomalyReviewActionType.ACKNOWLEDGE,
            notes="Attempt by viewer",
            current_user=viewer
        )
    assert exc_info.value.status_code == 403
    assert "not authorized" in exc_info.value.detail.lower()


def test_anomaly_review_invalid_transition(db_session: Session, test_users):
    """Verifies that invalid status transitions (e.g. RESOLVED -> ACKNOWLEDGED directly) raise HTTP 400."""
    sig_id = "SIG_INVALID_TRANSITION_TEST"
    admin = test_users["admin"]

    review = DistrictAnomalyReviewService.get_or_create_review(
        db=db_session,
        signal_id=sig_id,
        district="Chennai",
        indicator_id="1.1",
        reporting_month="2016-01",
        signal_type="MOM_SHIFT",
        severity="WARNING",
        trigger_reason="Test reason"
    )

    # Transition to RESOLVED directly from OPEN is valid
    DistrictAnomalyReviewService.apply_review_action(
        db=db_session,
        signal_id=sig_id,
        action=AnomalyReviewActionType.RESOLVE,
        notes="Resolved directly",
        current_user=admin
    )

    # Attempting to directly ACKNOWLEDGE an already RESOLVED review without reopening is invalid
    with pytest.raises(HTTPException) as exc_info:
        DistrictAnomalyReviewService.apply_review_action(
            db=db_session,
            signal_id=sig_id,
            action=AnomalyReviewActionType.ACKNOWLEDGE,
            notes="Should fail",
            current_user=admin
        )
    assert exc_info.value.status_code == 400
    assert "invalid transition" in exc_info.value.detail.lower()
