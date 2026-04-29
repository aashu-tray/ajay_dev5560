from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from fuzzywuzzy import fuzz
import random
import string
from urllib.parse import urlparse

from .models import BlockedKeyword, ChildDevice, DeviceLocation, PairingCode, SiteVisit

# Your High-Value Target List
PROTECTED_DOMAINS = [
    "facebook.com", "instagram.com", "google.com", 
    "microsoft.com", "apple.com", "paypal.com",
    "linkedin.com", "twitter.com", "x.com",
    "chase.com", "bankofamerica.com", "wellsfargo.com",
    "amazon.com", "netflix.com", "github.com",
    "indeed.com", "glassdoor.com", "naukri.com",
    "binance.com", "coinbase.com", "hdfcbank.com",
    "icicibank.com", "sbi.co.in"
]


def generate_pairing_code():
    while True:
        code = "".join(random.choices(string.digits, k=6))
        if not PairingCode.objects.filter(code=code).exists():
            return code


def get_dashboard_pairing_code(parent):
    pairing_code = PairingCode.objects.filter(parent=parent).first()

    if pairing_code:
        return pairing_code

    now = timezone.now()
    return PairingCode.objects.create(
        parent=parent,
        code=generate_pairing_code(),
        expires_at=now + timezone.timedelta(minutes=15),
    )


def create_fresh_pairing_code(parent):
    now = timezone.now()
    PairingCode.objects.filter(
        parent=parent,
        used_at__isnull=True,
        expires_at__gt=now,
    ).update(expires_at=now)

    return PairingCode.objects.create(
        parent=parent,
        code=generate_pairing_code(),
        expires_at=now + timezone.timedelta(minutes=15),
    )

@api_view(['POST'])
def analyze_domain(request):
    current_domain = request.data.get('currentDomain')

    if not current_domain:
        return Response({"error": "No domain provided"}, status=400)

    # Exact match check
    if current_domain in PROTECTED_DOMAINS:
        return Response({"score": 100, "status": "SECURE", "message": "Verified authentic domain."})

    threat_score = 100
    is_safe = True
    alert_message = "Domain looks safe."

    # Typosquatting check using FuzzyWuzzy
    for protected in PROTECTED_DOMAINS:
        similarity = fuzz.ratio(current_domain, protected)
        
        # If similarity is 85% or higher, it's a clone/trap!
        if similarity >= 85:
            threat_score -= 40
            is_safe = False
            alert_message = f"CRITICAL ALERT: Typosquatting detected! This site is mimicking {protected}"
            break 
            
    return Response({
        "score": threat_score,
        "status": "SECURE" if is_safe else "CRITICAL_THREAT",
        "message": alert_message
    })


@api_view(['GET'])
def get_blocked_keywords(request):
    device_token = request.GET.get('device_token')
    queryset = BlockedKeyword.objects.all()

    if device_token:
        try:
            device = ChildDevice.objects.get(token=device_token)
        except ChildDevice.DoesNotExist:
            return Response({'error': 'Invalid device token'}, status=404)

        queryset = queryset.filter(parent_id=str(device.parent_id))

    keywords = list(queryset.values_list('keyword', flat=True))
    return Response({'blocked_keywords': keywords})


@api_view(['POST'])
def create_pairing_code(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=403)

    pairing_code = create_fresh_pairing_code(request.user)

    return Response({
        'pairing_code': pairing_code.code,
        'expires_at': pairing_code.expires_at,
    })


@login_required
def regenerate_pairing_code(request):
    if request.method == 'POST':
        create_fresh_pairing_code(request.user)

    return redirect('dashboard_view')


@api_view(['POST'])
def pair_child_device(request):
    code = request.data.get('code')
    device_identifier = request.data.get('device_identifier')
    device_name = request.data.get('device_name', '')

    if not code or not device_identifier:
        return Response(
            {'error': 'code and device_identifier are required'},
            status=400,
        )

    try:
        pairing_code = PairingCode.objects.get(
            code=code,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
    except PairingCode.DoesNotExist:
        return Response({'error': 'Invalid or expired pairing code'}, status=400)

    device, _created = ChildDevice.objects.update_or_create(
        device_identifier=device_identifier,
        defaults={
            'parent': pairing_code.parent,
            'name': device_name,
        },
    )
    pairing_code.used_at = timezone.now()
    pairing_code.save(update_fields=['used_at'])

    return Response({
        'device_token': str(device.token),
        'parent_id': device.parent_id,
        'device_id': device.id,
    })


@api_view(['POST'])
def submit_device_location(request):
    device_token = request.data.get('device_token')
    raw_latitude = request.data.get('latitude')
    raw_longitude = request.data.get('longitude')

    if not device_token or raw_latitude is None or raw_longitude is None:
        return Response(
            {'error': 'device_token, latitude and longitude are required'},
            status=400,
        )

    try:
        latitude = float(raw_latitude)
        longitude = float(raw_longitude)
    except (TypeError, ValueError):
        return Response(
            {'error': 'latitude and longitude must be valid numbers'},
            status=400,
        )

    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return Response(
            {'error': 'latitude or longitude is outside the valid range'},
            status=400,
        )

    try:
        device = ChildDevice.objects.get(token=device_token)
    except ChildDevice.DoesNotExist:
        return Response({'error': 'Invalid device token'}, status=404)

    location = DeviceLocation.objects.create(
        device=device,
        latitude=latitude,
        longitude=longitude,
    )

    return Response({
        'status': 'saved',
        'location_id': location.id,
        'latitude': location.latitude,
        'longitude': location.longitude,
        'timestamp': location.timestamp,
    })


@api_view(['POST'])
def report_site_visit(request):
    device_token = request.data.get('device_token')
    url = request.data.get('url', '').strip()
    title = request.data.get('title', '').strip()
    matched_keyword = request.data.get('matched_keyword', '').strip().lower()

    if not device_token or not url:
        return Response(
            {'error': 'device_token and url are required'},
            status=400,
        )

    try:
        device = ChildDevice.objects.get(token=device_token)
    except ChildDevice.DoesNotExist:
        return Response({'error': 'Invalid device token'}, status=404)

    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()

    visit = SiteVisit.objects.create(
        device=device,
        url=url,
        title=title[:300],
        domain=domain,
        matched_keyword=matched_keyword[:100],
    )

    return Response({
        'status': 'saved',
        'visit_id': visit.id,
        'visited_at': visit.visited_at,
    })


@login_required
def dashboard_view(request):
    pairing_code = get_dashboard_pairing_code(request.user)
    now = timezone.now()

    if pairing_code.used_at:
        pairing_code_status = "used"
    elif pairing_code.expires_at <= now:
        pairing_code_status = "expired"
    else:
        pairing_code_status = "active"

    devices = ChildDevice.objects.filter(parent=request.user)
    latest_pos = DeviceLocation.objects.filter(device__parent=request.user).order_by('-timestamp').first()
    seven_days_ago = timezone.now() - timezone.timedelta(days=7)
    recent_visits = SiteVisit.objects.filter(
        device__parent=request.user,
        visited_at__gte=seven_days_ago,
    ).select_related("device")[:100]
    
    blocked_list = BlockedKeyword.objects.filter(parent_id=str(request.user.id))
    
    return render(request, 'parent_dashboard.html', {
        'location': latest_pos,
        'keywords': blocked_list,
        'recent_visits': recent_visits,
        'pairing_code': pairing_code,
        'pairing_code_status': pairing_code_status,
        'devices': devices,
    })


@login_required
def add_blocked_keyword(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '').strip().lower()

        if keyword:
            BlockedKeyword.objects.get_or_create(
                parent_id=str(request.user.id),
                keyword=keyword,
            )

    return redirect('dashboard_view')


@login_required
def delete_blocked_keyword(request, keyword_id):
    if request.method == 'POST':
        keyword = get_object_or_404(
            BlockedKeyword,
            id=keyword_id,
            parent_id=str(request.user.id),
        )
        keyword.delete()

    return redirect('dashboard_view')
