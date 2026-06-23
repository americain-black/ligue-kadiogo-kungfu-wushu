from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Role, Permission, RolePermission, UtilisateurRole


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display  = ('code', 'nom_permission', 'module')
    list_filter   = ('module',)
    search_fields = ('code', 'nom_permission')


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('nom_role', 'description', 'nb_permissions')
    inlines      = [RolePermissionInline]

    def nb_permissions(self, obj):
        return obj.permissions.count()
    nb_permissions.short_description = "Permissions"


class UtilisateurRoleInline(admin.TabularInline):
    model = UtilisateurRole
    extra = 1


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display  = ('username', 'email', 'get_roles', 'statut_compte', 'is_active')
    list_filter   = ('statut_compte', 'is_active', 'roles')
    inlines       = [UtilisateurRoleInline]
    fieldsets     = UserAdmin.fieldsets + (
        ('Informations complémentaires', {
            'fields': ('telephone', 'photo', 'statut_compte')
        }),
    )

    def get_roles(self, obj):
        return ", ".join(obj.get_roles_display())
    get_roles.short_description = "Rôles"