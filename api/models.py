from django.db import models
from django.conf import settings
import uuid


class BlockedKeyword(models.Model):
    parent_id = models.CharField(max_length=50)
    keyword = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["keyword"]
        unique_together = ("parent_id", "keyword")

    def __str__(self):
        return self.keyword


class PairingCode(models.Model):
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=8, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.code


class ChildDevice(models.Model):
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True)
    device_identifier = models.CharField(max_length=150, unique=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    paired_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "device_identifier"]

    def __str__(self):
        return self.name or self.device_identifier


class DeviceLocation(models.Model):
    device = models.ForeignKey(
        ChildDevice,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="locations",
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]


class SiteVisit(models.Model):
    device = models.ForeignKey(
        ChildDevice,
        on_delete=models.CASCADE,
        related_name="site_visits",
    )
    url = models.URLField(max_length=2000)
    title = models.CharField(max_length=300, blank=True)
    domain = models.CharField(max_length=255, blank=True)
    matched_keyword = models.CharField(max_length=100, blank=True)
    visited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-visited_at"]

    def __str__(self):
        return self.domain or self.url
