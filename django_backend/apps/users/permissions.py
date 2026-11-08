from rest_framework.permissions import BasePermission

STAFF_ROLES = (
    0,1,2
)

class IsAdminStaff(BasePermission):
    """后台角色放行;匿名(未带 token)一律拒绝。"""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and getattr(user, 'role', None) in STAFF_ROLES)


class IsSuperAdminStaff(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        return bool(user and getattr(user, 'role', None) == 0)

class IsReviewer(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and getattr(user, 'role', None) in (0,2))
