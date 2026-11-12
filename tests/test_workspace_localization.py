from django.test import TestCase
from django.urls import reverse
from django.utils import timezone, translation

from apps.accounts.models import User
from apps.members.models import WorkspaceMembership
from apps.social_accounts.models import SocialAccount
from apps.workspaces.models import Workspace


class WorkspaceLocalizationTests(TestCase):
    def test_settings_pages_render_chinese_and_preserve_customer_name(self):
        user = User.objects.create_user(email="locale@example.com", tos_accepted_at=timezone.now())
        membership = WorkspaceMembership.objects.select_related("workspace").get(user=user)
        workspace = membership.workspace
        workspace.name = "RRR Lighting"
        workspace.save(update_fields=["name"])
        Workspace.objects.create(organization=workspace.organization, name="Second workspace")
        self.client.force_login(user)
        with translation.override("zh-hans"):
            settings = self.client.get(reverse("workspaces:settings", args=[workspace.pk]))
            for text in ("RRR Lighting", "工作区名称", "保存修改", "归档工作区", "删除工作区"):
                self.assertContains(settings, text)
            self.assertNotContains(settings, "Save Changes")
            approvals = self.client.get(reverse("workspaces:approvals_settings", args=[workspace.pk]))
            self.assertContains(approvals, "必须内部审核")
            self.assertNotContains(approvals, "Internal review required")
            empty = self.client.get(reverse("calendar:publish_tab_drafts", args=[workspace.pk]))
            self.assertContains(empty, "连接渠道")
            SocialAccount.objects.create(
                workspace=workspace,
                platform="linkedin_personal",
                account_platform_id="locale-test-account",
                account_name="Locale Test",
                connection_status="connected",
            )
            for route, label in (
                ("social_accounts:connect", "连接社媒平台"),
                ("calendar:publish_tab_drafts", "暂无草稿"),
                ("calendar:publish_tab_approvals", "暂无待审核帖子"),
                ("calendar:publish_tab_sent", "暂无发送记录"),
            ):
                with self.subTest(route=route):
                    response = self.client.get(reverse(route, args=[workspace.pk]))
                    self.assertContains(response, label)
        with translation.override("en"):
            settings = self.client.get(reverse("workspaces:settings", args=[workspace.pk]))
            self.assertContains(settings, "Workspace Name")
