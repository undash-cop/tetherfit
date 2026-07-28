from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.deps import AuthPrincipal, extract_roles
from app.core.permissions import PermissionContext, permission_service
from app.domain.models import SessionStatus, User
from app.features.sessions.schemas import SessionCreate


def test_session_create_requires_end_after_start():
    start = datetime.now(UTC)
    with pytest.raises(ValueError):
        SessionCreate(
            client_id=uuid4(),
            starts_at=start,
            ends_at=start,
        )


def test_session_create_ok():
    start = datetime.now(UTC)
    data = SessionCreate(
        client_id=uuid4(),
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        location="Studio A",
    )
    assert data.location == "Studio A"


def test_session_status_values():
    assert SessionStatus.SCHEDULED == "scheduled"
    assert SessionStatus.COMPLETED == "completed"
    assert SessionStatus.NO_SHOW == "no_show"


def test_allowed_transitions_matrix():
    """Document valid session transitions for regression clarity."""
    allowed = {
        SessionStatus.SCHEDULED: {
            SessionStatus.CHECKED_IN,
            SessionStatus.IN_PROGRESS,
            SessionStatus.COMPLETED,
            SessionStatus.CANCELLED,
            SessionStatus.NO_SHOW,
        },
        SessionStatus.CHECKED_IN: {
            SessionStatus.IN_PROGRESS,
            SessionStatus.COMPLETED,
            SessionStatus.CANCELLED,
            SessionStatus.NO_SHOW,
        },
        SessionStatus.IN_PROGRESS: {
            SessionStatus.PAUSED,
            SessionStatus.COMPLETED,
            SessionStatus.CANCELLED,
        },
        SessionStatus.PAUSED: {
            SessionStatus.IN_PROGRESS,
            SessionStatus.COMPLETED,
            SessionStatus.CANCELLED,
        },
    }
    assert SessionStatus.NO_SHOW in allowed[SessionStatus.SCHEDULED]
    assert SessionStatus.PAUSED in allowed[SessionStatus.IN_PROGRESS]
    assert SessionStatus.IN_PROGRESS in allowed[SessionStatus.PAUSED]


def test_onboarded_user_defaults_to_owner_permissions():
    user = User(
        keycloak_user_id="kc-owner",
        full_name="Solo",
        organization_id=uuid4(),
        onboarding_completed=True,
    )
    principal = AuthPrincipal(user=user, roles=set())
    ctx = principal.permission_context()
    assert permission_service.can(ctx, "client:create")
    assert permission_service.can(ctx, "settings:update")


def test_extract_roles_empty_payload():
    assert extract_roles({}) == set()


def test_client_permission_denied_for_client_role():
    user = User(keycloak_user_id="kc-client", full_name="Athlete")
    ctx = PermissionContext(user=user, roles={"client"})
    assert not permission_service.can(ctx, "client:delete")
    assert permission_service.can(ctx, "client:view")
