"""SQID encoding, decoding, and descriptor for NetBox models.

This module provides the core SQID logic: a factory for creating Sqids
encoder instances, a Python descriptor for computed sqid properties,
and a resolver function for decoding SQIDs back to model instances.
"""

from django.contrib.contenttypes.models import ContentType
from sqids import Sqids

ALPHABET = "0123456789ACDEFGHJKLMNPQRSTUVWXYZ"
"""33-character alphabet excluding B, I, O to avoid visual ambiguity."""


def get_sqids_instance(
    min_length: int = 4,
    blocklist: list[str] | None = None,
    extra_blocklist: list[str] | None = None,
) -> Sqids:
    """Create a configured Sqids encoder/decoder instance.

    Args:
        min_length: Minimum output string length.
        blocklist: Words to filter from generated SQIDs. None uses the
            extended default blocklist.
        extra_blocklist: Additional values to filter, appended to ``blocklist``.
            Used to skip a specific SQID that collided with a stored value;
            the library then emits an equivalent SQID instead.

    Returns:
        A Sqids instance configured with the custom alphabet.
    """
    if blocklist is None:
        from sqids.constants import DEFAULT_BLOCKLIST

        blocklist = list(DEFAULT_BLOCKLIST) + ["ck", "sex", "butt"]
    if extra_blocklist:
        blocklist = list(blocklist) + list(extra_blocklist)
    return Sqids(alphabet=ALPHABET, min_length=min_length, blocklist=blocklist)


_sqids_instance = None


def _get_instance() -> Sqids:
    """Return the module-level Sqids singleton, creating it on first use."""
    global _sqids_instance
    if _sqids_instance is None:
        from django.conf import settings

        plugin_settings = settings.PLUGINS_CONFIG.get("netbox_sqids", {})
        _sqids_instance = get_sqids_instance(
            min_length=plugin_settings.get("min_length", 4),
            blocklist=plugin_settings.get("blocklist", None),
        )
    return _sqids_instance


def encode_object(obj, extra_blocklist: list[str] | None = None) -> str | None:
    """Return ``obj``'s SQID, optionally skipping values in ``extra_blocklist``.

    With no ``extra_blocklist`` this returns the same value as ``obj.sqid``.
    When a caller finds that the canonical SQID collides with a stored value,
    passing that value (and any further collisions) makes the sqids library
    emit an equivalent SQID -- a different string that still decodes back to
    the same object -- rather than failing. Returns None for unsaved objects
    and non-integer primary keys, mirroring ``SqidDescriptor``.

    Args:
        obj: The model instance to encode.
        extra_blocklist: SQID values to skip.

    Returns:
        The SQID string, or None if ``obj`` has no integer primary key.
    """
    if obj.pk is None or not isinstance(obj.pk, int):
        return None
    ct_id = ContentType.objects.get_for_model(obj).pk
    if not extra_blocklist:
        return _get_instance().encode([ct_id, obj.pk])

    from django.conf import settings

    plugin_settings = settings.PLUGINS_CONFIG.get("netbox_sqids", {})
    instance = get_sqids_instance(
        min_length=plugin_settings.get("min_length", 4),
        blocklist=plugin_settings.get("blocklist", None),
        extra_blocklist=extra_blocklist,
    )
    return instance.encode([ct_id, obj.pk])


class SqidDescriptor:
    """Read-only descriptor that computes a SQID from an object's content type and PK.

    Attached to models via ``add_to_class('sqid', SqidDescriptor())`` in
    ``PluginConfig.ready()``. Returns None for unsaved objects and non-integer PKs.
    """

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if obj.pk is None:
            return None
        if not isinstance(obj.pk, int):
            return None
        ct_id = ContentType.objects.get_for_model(obj).pk
        return _get_instance().encode([ct_id, obj.pk])

    def __set__(self, obj, value):
        raise AttributeError("sqid is read-only")


def resolve_sqid(sqid_str: str):
    """Decode a SQID string and return the corresponding model instance.

    Raises:
        ValueError: if sqid_str is empty or decodes to unexpected length
        ObjectDoesNotExist: if the content type or object doesn't exist
    """
    ids = _get_instance().decode(sqid_str)
    if len(ids) != 2:
        raise ValueError(f"Invalid SQID: {sqid_str}")
    ct_id, obj_id = ids
    ct = ContentType.objects.get_for_id(ct_id)
    return ct.get_object_for_this_type(pk=obj_id)
