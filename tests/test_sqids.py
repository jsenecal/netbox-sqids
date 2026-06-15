from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ObjectDoesNotExist

from netbox_sqids.sqids import (
    SqidDescriptor,
    encode_object,
    get_sqids_instance,
    resolve_sqid,
)

ALPHABET = "0123456789ACDEFGHJKLMNPQRSTUVWXYZ"


class TestSqidsInstance:
    def test_encodes_two_integers(self):
        instance = get_sqids_instance(min_length=4, blocklist=[])
        result = instance.encode([1, 1])
        assert isinstance(result, str)
        assert len(result) >= 4

    def test_roundtrip(self):
        instance = get_sqids_instance(min_length=4, blocklist=[])
        encoded = instance.encode([42, 100])
        decoded = instance.decode(encoded)
        assert decoded == [42, 100]

    def test_uses_custom_alphabet(self):
        instance = get_sqids_instance(min_length=4, blocklist=[])
        encoded = instance.encode([1, 1])
        for char in encoded:
            assert char in ALPHABET

    def test_min_length_respected(self):
        instance = get_sqids_instance(min_length=8, blocklist=[])
        encoded = instance.encode([1, 1])
        assert len(encoded) >= 8

    def test_blocklist_filters_words(self):
        instance = get_sqids_instance(min_length=1, blocklist=["sex"])
        encoded = instance.encode([1, 1])
        assert "sex" not in encoded.lower()

    def test_extra_blocklist_skips_value_but_stays_decodable(self):
        canonical = get_sqids_instance().encode([5, 42])
        alt = get_sqids_instance(extra_blocklist=[canonical]).encode([5, 42])
        assert alt != canonical
        # The equivalent SQID still decodes back to the same numbers.
        assert get_sqids_instance().decode(alt) == [5, 42]

    def test_extra_blocklist_none_matches_default(self):
        assert get_sqids_instance(extra_blocklist=None).encode([5, 42]) == get_sqids_instance().encode([5, 42])


class TestEncodeObject:
    def test_unsaved_object_returns_none(self):
        class FakeModel:
            pk = None

        assert encode_object(FakeModel()) is None

    def test_non_integer_pk_returns_none(self):
        class FakeModel:
            pk = "uuid-string"

        assert encode_object(FakeModel()) is None

    @patch("netbox_sqids.sqids.ContentType")
    def test_no_extras_roundtrips_to_content_type_and_pk(self, mock_ct_class):
        mock_ct = MagicMock()
        mock_ct.pk = 5
        mock_ct_class.objects.get_for_model.return_value = mock_ct

        class FakeModel:
            pk = 42

        result = encode_object(FakeModel())
        assert get_sqids_instance().decode(result) == [5, 42]

    @patch("netbox_sqids.sqids.ContentType")
    def test_extra_blocklist_yields_equivalent_sqid(self, mock_ct_class):
        mock_ct = MagicMock()
        mock_ct.pk = 5
        mock_ct_class.objects.get_for_model.return_value = mock_ct

        class FakeModel:
            pk = 42

        obj = FakeModel()
        canonical = encode_object(obj)
        alt = encode_object(obj, extra_blocklist=[canonical])
        assert alt != canonical
        # Different string, same object.
        assert get_sqids_instance().decode(alt) == [5, 42]


class TestSqidDescriptor:
    def test_class_access_returns_descriptor(self):
        class FakeModel:
            sqid = SqidDescriptor()

        assert isinstance(FakeModel.sqid, SqidDescriptor)

    def test_unsaved_object_returns_none(self):
        class FakeModel:
            pk = None
            sqid = SqidDescriptor()

        obj = FakeModel()
        assert obj.sqid is None

    @patch("netbox_sqids.sqids.ContentType")
    def test_returns_encoded_sqid(self, mock_ct_class):
        mock_ct = MagicMock()
        mock_ct.pk = 5
        mock_ct_class.objects.get_for_model.return_value = mock_ct

        class FakeModel:
            pk = 42
            sqid = SqidDescriptor()

        obj = FakeModel()

        result = obj.sqid
        assert isinstance(result, str)
        assert len(result) >= 4

        # Verify roundtrip
        instance = get_sqids_instance()
        decoded = instance.decode(result)
        assert decoded == [5, 42]

    @patch("netbox_sqids.sqids.ContentType")
    def test_read_only(self, mock_ct_class):
        class FakeModel:
            pk = 1
            sqid = SqidDescriptor()

        obj = FakeModel()
        with pytest.raises(AttributeError, match="read-only"):
            obj.sqid = "something"

    def test_non_integer_pk_returns_none(self):
        class FakeModel:
            pk = "uuid-string"
            sqid = SqidDescriptor()

        obj = FakeModel()
        assert obj.sqid is None


class TestResolveSqid:
    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid SQID"):
            resolve_sqid("")

    def test_invalid_sqid_raises_value_error(self):
        # encode a single integer — should fail the len!=2 check
        instance = get_sqids_instance()
        bad_sqid = instance.encode([1])
        with pytest.raises(ValueError, match="Invalid SQID"):
            resolve_sqid(bad_sqid)

    @patch("netbox_sqids.sqids.ContentType")
    def test_resolves_valid_sqid(self, mock_ct_class):
        instance = get_sqids_instance()
        sqid_str = instance.encode([5, 42])

        mock_obj = MagicMock()
        mock_ct = MagicMock()
        mock_ct_class.objects.get_for_id.return_value = mock_ct
        mock_ct.get_object_for_this_type.return_value = mock_obj

        result = resolve_sqid(sqid_str)

        assert result is mock_obj
        mock_ct_class.objects.get_for_id.assert_called_once_with(5)
        mock_ct.get_object_for_this_type.assert_called_once_with(pk=42)

    @patch("netbox_sqids.sqids.ContentType")
    def test_nonexistent_content_type_raises(self, mock_ct_class):
        instance = get_sqids_instance()
        sqid_str = instance.encode([9999, 1])

        mock_ct_class.objects.get_for_id.side_effect = ObjectDoesNotExist()

        with pytest.raises(ObjectDoesNotExist):
            resolve_sqid(sqid_str)
