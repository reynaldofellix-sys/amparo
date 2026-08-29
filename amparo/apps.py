from django.contrib.admin.apps import AdminConfig


class AmparoAdminConfig(AdminConfig):
    default_site = "amparo.admin.AmparoAdminSite"
