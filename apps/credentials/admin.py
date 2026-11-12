from django.contrib import admin
from django.shortcuts import redirect

from apps.members.models import WorkspaceMembership

from .forms import PlatformCredentialAdminForm
from .models import PlatformCredential


@admin.register(PlatformCredential)
class PlatformCredentialAdmin(admin.ModelAdmin):
    form = PlatformCredentialAdminForm
    list_display = ("organization", "platform", "is_configured", "test_result", "tested_at")
    list_filter = ("platform", "is_configured", "test_result")
    search_fields = ("organization__name",)
    # is_configured is derived from the credentials on save (see model); the test
    # fields have no flow yet — keep them read-only so they can't be hand-set.
    readonly_fields = ("id", "is_configured", "test_result", "tested_at", "created_at", "updated_at")

    # Editing credentials necessarily reveals decrypted secrets on the change
    # page, so restrict the whole model to superusers (admin already requires
    # is_staff).
    def changelist_view(self, request, extra_context=None):
        if request.method == "GET" and request.user.is_superuser and request.user.last_workspace_id:
            membership = WorkspaceMembership.objects.filter(
                user=request.user, workspace_id=request.user.last_workspace_id
            ).first()
            if membership and membership.effective_permissions.get("manage_social_accounts"):
                return redirect("social_accounts:connect", workspace_id=membership.workspace_id)
        return super().changelist_view(request, extra_context)

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
