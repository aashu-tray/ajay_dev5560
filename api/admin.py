from django.contrib import admin

from .models import BlockedKeyword, ChildDevice, DeviceLocation, PairingCode, SiteVisit


@admin.register(BlockedKeyword)
class BlockedKeywordAdmin(admin.ModelAdmin):
    list_display = ("keyword", "parent_id", "created_at")
    search_fields = ("keyword", "parent_id")
    list_filter = ("created_at",)


@admin.register(PairingCode)
class PairingCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "parent", "expires_at", "used_at", "created_at")
    search_fields = ("code", "parent__username")
    list_filter = ("created_at", "expires_at", "used_at")


@admin.register(ChildDevice)
class ChildDeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "device_identifier", "parent", "paired_at")
    search_fields = ("name", "device_identifier", "parent__username")
    list_filter = ("paired_at",)


@admin.register(DeviceLocation)
class DeviceLocationAdmin(admin.ModelAdmin):
    list_display = ("device", "latitude", "longitude", "timestamp")
    search_fields = ("device__name", "device__device_identifier")
    list_filter = ("timestamp",)


@admin.register(SiteVisit)
class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ("domain", "device", "matched_keyword", "visited_at")
    search_fields = ("url", "title", "domain", "device__name", "device__device_identifier")
    list_filter = ("visited_at", "matched_keyword")
