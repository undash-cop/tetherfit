from app.core.deps import extract_roles
from app.core.permissions import PermissionContext, permission_service
from app.domain.models import User


def test_extract_roles_from_realm_access():
    payload = {
        "realm_access": {"roles": ["business_owner", "offline_access"]},
        "resource_access": {"tetherfit-api": {"roles": ["trainer"]}},
    }
    roles = extract_roles(payload)
    assert "business_owner" in roles
    assert "trainer" in roles


def test_normalize_owner_alias():
    roles = extract_roles({"realm_access": {"roles": ["owner"]}})
    assert "business_owner" in roles


def test_permission_service_owner_role():
    user = User(keycloak_user_id="kc-2", full_name="Owner")
    ctx = PermissionContext(user=user, roles={"business_owner"})
    assert permission_service.can(ctx, "settings:update")
    assert permission_service.can(ctx, "client:delete")


def test_permission_service_baseline():
    user = User(keycloak_user_id="kc-1", full_name="Test")
    assert permission_service.can(user, "client:view")
    assert permission_service.can(user, "ai:use")
    assert permission_service.can(user, "settings:update")


def test_trainer_cannot_settings():
    user = User(keycloak_user_id="kc-3", full_name="Trainer")
    ctx = PermissionContext(user=user, roles={"trainer"})
    assert permission_service.can(ctx, "session:start")
    assert not permission_service.can(ctx, "settings:update")
