import pytest
from django.urls import reverse

from apps.credentials.models import PlatformCredential
from apps.members.models import WorkspaceMembership


@pytest.mark.django_db
def test_setup_only_accepts_authorized_updates(client, user, settings):
    settings.PLATFORM_CREDENTIALS_FROM_ENV = {}
    member = WorkspaceMembership.objects.get(user=user)
    url = reverse("social_accounts:platform_setup", args=[member.workspace_id, "facebook"])
    grid = reverse("social_accounts:connect", args=[member.workspace_id])
    client.force_login(user)
    payload = {"client_id": "demonstration-id", "client_secret": "demonstration-value"}
    assert client.post(url, payload).status_code == 403
    assert not PlatformCredential.objects.exists()
    user.is_superuser = True
    user.is_staff = True
    user.save()
    assert client.get(reverse("admin:credentials_platformcredential_changelist")).url == grid
    assert url in client.get(grid).content.decode()
    page = client.get(url)
    assert "回调地址" in page.content.decode()
    assert "/social-accounts/callback/facebook/" in page.content.decode()
    assert client.post(url, {"client_id": "incomplete"}).status_code == 200
    assert not PlatformCredential.objects.exists()
    assert client.post(url, payload).url == grid
    row = PlatformCredential.objects.get(organization=member.workspace.organization, platform="facebook")
    assert row.is_configured
    assert payload["client_secret"] not in client.get(url).content.decode()
    settings.PLATFORM_CREDENTIALS_FROM_ENV = {"facebook": payload}
    assert client.post(url, {"client_id": "different", "client_secret": "different"}).status_code == 403
    row.refresh_from_db()
    assert row.credentials == payload
