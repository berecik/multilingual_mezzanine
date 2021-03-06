from __future__ import unicode_literals

from django.db import models

from mezzanine.core.models import Slugged, Orderable


class Titled(models.Model):
    """
    Inline model with a title.
    """

    title = models.CharField("Title", max_length=100)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


class TitledInline(Orderable, Titled):
    """
    Inline model with a title and manual sorting.
    """

    class Meta:
        abstract = True


class SluggedInline(Orderable, Slugged):
    """
    Inline model with a title, a slug and manual sorting.
    """

    class Meta:
        abstract = True
