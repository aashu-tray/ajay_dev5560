from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import redirect, render


def home(request):
    return JsonResponse(
        {
            "message": "PodarGuard backend is running.",
            "available_endpoints": ["/api/analyze/"],
        }
    )


def favicon(request):
    return HttpResponse(status=204)


def manifest(request):
    return JsonResponse(
        {
            "name": "PodarGuard Parent Dashboard",
            "short_name": "PodarGuard",
            "description": "Installable parent dashboard for child device tracking and safety controls.",
            "start_url": "/api/dashboard/",
            "scope": "/",
            "display": "standalone",
            "background_color": "#f6f7fb",
            "theme_color": "#1769e0",
            "orientation": "portrait-primary",
            "icons": [
                {
                    "src": "/static/pwa/icon.svg",
                    "sizes": "any",
                    "type": "image/svg+xml",
                    "purpose": "any maskable",
                }
            ],
        }
    )


def service_worker(request):
    response = FileResponse(
        open(settings.BASE_DIR / "static" / "pwa" / "service-worker.js", "rb"),
        content_type="application/javascript",
    )
    response["Service-Worker-Allowed"] = "/"
    return response


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard_view")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard_view")
    else:
        form = UserCreationForm()

    return render(request, "registration/signup.html", {"form": form})
