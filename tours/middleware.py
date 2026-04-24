from django.shortcuts import redirect


class BlockNonStaffAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.path.startswith("/admin")
            and request.user.is_authenticated
            and not request.user.is_staff
        ):
            return redirect("profile")
        return self.get_response(request)
