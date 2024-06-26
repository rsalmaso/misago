from hashlib import md5

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import pgettext_lazy


def get_data_upload_to(instance, filename):
    user_id_hexdigest = md5(str(instance.user_id).encode()).hexdigest()
    return "data-downloads/%s/%s/%s.zip" % (
        user_id_hexdigest,
        get_random_string(64),
        instance.user.slug,
    )


class DataDownload(models.Model):
    STATUS_PENDING = 0
    STATUS_PROCESSING = 1
    STATUS_READY = 2
    STATUS_EXPIRED = 3

    STATUS_CHOICES = [
        (
            STATUS_PENDING,
            pgettext_lazy("user data download status", "Pending"),
        ),
        (
            STATUS_PROCESSING,
            pgettext_lazy("user data download status", "Processing"),
        ),
        (
            STATUS_READY,
            pgettext_lazy("user data download status", "Ready"),
        ),
        (
            STATUS_EXPIRED,
            pgettext_lazy("user data download status", "Expired"),
        ),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.PositiveIntegerField(
        default=STATUS_PENDING, choices=STATUS_CHOICES, db_index=True
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    requester_name = models.CharField(max_length=255)
    requested_on = models.DateTimeField(default=timezone.now, db_index=True)
    expires_on = models.DateTimeField(default=timezone.now)
    file = models.FileField(
        upload_to=get_data_upload_to, max_length=255, null=True, blank=True
    )

    class Meta:
        ordering = ["-pk"]

    @property
    def is_ready(self):
        return self.status == DataDownload.STATUS_READY

    @property
    def is_expired(self):
        return self.status == DataDownload.STATUS_EXPIRED

    def delete(self, *args, **kwargs):
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)
