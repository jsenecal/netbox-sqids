# netbox-sqids Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a NetBox plugin that adds a computed `sqid` property to every Django model and provides redirect views for resolving SQIDs back to objects.

**Architecture:** A Python descriptor (`SqidDescriptor`) is attached to all models via `add_to_class` in `PluginConfig.ready()`. A module-level `Sqids` instance handles encoding/decoding. Two view layers (browser + API) resolve SQIDs to object URLs via 302 redirects. Monkey-patched short URLs are optionally injected into NetBox's root urlconfs.

**Tech Stack:** Python 3.12+, Django, NetBox >=4.4.0, sqids>=0.4.1, pytest-django

**Spec:** `docs/superpowers/specs/2026-04-03-netbox-sqids-design.md`

---

## File Map

| File | Responsibility |
|------|----------------|
| `pyproject.toml` | Package metadata, dependencies, ruff + pytest config |
| `.gitignore` | Standard Python/Django ignores |
| `netbox_sqids/__init__.py` | `PluginConfig` with `ready()` — auto-discovery + monkey-patch URLs |
| `netbox_sqids/sqids.py` | `Sqids` instance, `SqidDescriptor`, `resolve_sqid()` |
| `netbox_sqids/urls.py` | Browser redirect URL pattern |
| `netbox_sqids/views.py` | Browser redirect view |
| `netbox_sqids/api/__init__.py` | Empty |
| `netbox_sqids/api/urls.py` | API redirect URL pattern |
| `netbox_sqids/api/views.py` | API redirect view |
| `tests/__init__.py` | Empty |
| `tests/test_sqids.py` | Unit tests for descriptor, encode/decode, resolve |
| `tests/test_views.py` | Integration tests for redirect views |
| `.devcontainer/devcontainer.json` | Dev container config |
| `.devcontainer/docker-compose.yml` | Services: netbox, postgres, redis |
| `.devcontainer/Dockerfile-plugin_dev` | NetBox image + dev tools |
| `.devcontainer/entrypoint-dev.sh` | UID/GID fixup entrypoint |
| `.devcontainer/requirements-dev.txt` | Dev Python dependencies |
| `.devcontainer/.gitignore` | Ignore local overrides, keep structure |
| `.devcontainer/configuration/configuration.py` | NetBox config (standard PostgreSQL) |
| `.devcontainer/configuration/logging.py` | Logging config |
| `.devcontainer/env/netbox.env` | NetBox env vars |
| `.devcontainer/env/postgres.env` | Postgres credentials |
| `.devcontainer/env/redis.env` | Redis password |
| `.devcontainer/home/` | Fish shell, omf, VS Code keybindings, Claude Code dirs |

---

## Chunk 1: Project Scaffolding

### Task 1: Create pyproject.toml and .gitignore

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
include = ["netbox_sqids", "netbox_sqids.*"]

[project]
name = "netbox-sqids"
version = "0.1.0"
description = "NetBox plugin that adds short, URL-safe, globally unique SQID identifiers to every model"
readme = "README.md"
authors = [
    { name = "Jonathan Senecal", email = "contact@jonathansenecal.com" },
]
license-files = ["LICENSE"]
requires-python = ">=3.12"

classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Natural Language :: English',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.12',
    'Programming Language :: Python :: 3.13',
]

dependencies = [
    "sqids>=0.4.1",
]

[project.optional-dependencies]
dev = [
    "bumpver",
    "pre-commit>=4.0.0",
    "pytest",
    "pytest-django>=4.5.0",
    "pytest-cov>=3.0.0",
    "ruff",
]

[project.urls]
Homepage = "https://github.com/jsenecal/netbox-sqids"
Source = "https://github.com/jsenecal/netbox-sqids"
Tracker = "https://github.com/jsenecal/netbox-sqids/issues"

[tool.bumpver]
current_version = "0.1.0"
version_pattern = "MAJOR.MINOR.PATCH"
commit_message = "chore: bump version {old_version} -> {new_version}"
tag_pattern = "vMAJOR.MINOR.PATCH"
commit = true
tag = true
push = true

[tool.bumpver.file_patterns]
"pyproject.toml" = [
    'current_version = "{version}"',
    'version = "{version}"',
]
"netbox_sqids/__init__.py" = [
    '__version__ = "{version}"',
]

[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "S", "B", "A", "C4", "DJ", "PIE"]
ignore = ["E501", "S101", "DJ01"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "S105"]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "netbox.settings"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=netbox_sqids --cov-report=term-missing --reuse-db"
```

- [ ] **Step 2: Create .gitignore**

Standard Python/Django .gitignore (same as netbox-pathways — remove TypeScript-specific entries).

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml .gitignore
git commit -m "feat: add pyproject.toml and .gitignore"
```

### Task 2: Create devcontainer

**Files:**
- Create: `.devcontainer/devcontainer.json`
- Create: `.devcontainer/docker-compose.yml`
- Create: `.devcontainer/Dockerfile-plugin_dev`
- Create: `.devcontainer/entrypoint-dev.sh`
- Create: `.devcontainer/requirements-dev.txt`
- Create: `.devcontainer/.gitignore`
- Create: `.devcontainer/configuration/configuration.py`
- Create: `.devcontainer/configuration/logging.py`
- Create: `.devcontainer/env/netbox.env`
- Create: `.devcontainer/env/postgres.env`
- Create: `.devcontainer/env/redis.env`
- Create: `.devcontainer/home/.config/.gitkeep`
- Create: `.devcontainer/home/.claude/.gitkeep`
- Create: `.devcontainer/home/.config/fish/conf.d/npm.fish`
- Create: `.devcontainer/home/.config/fish/conf.d/venv.fish`
- Create: `.devcontainer/home/.config/fish/conf.d/omf.fish`
- Create: `.devcontainer/home/.config/fish/fish_variables`
- Create: `.devcontainer/home/.config/omf/bundle`
- Create: `.devcontainer/home/.config/omf/channel`
- Create: `.devcontainer/home/.config/omf/theme`
- Create: `.devcontainer/home/.config/Code/User/keybindings.json`

Adapted from `netbox-pathways/.devcontainer/` with these changes:

- **devcontainer.json**: Change name to "NetBox SQIDs Plugin Development", workspaceFolder to "/opt/netbox-sqids", remove python analysis extra paths for GIS
- **docker-compose.yml**: Change container names to `netbox-sqids-*`, volume mount to `/opt/netbox-sqids`, use `postgres:16` instead of `postgis/postgis:16-3.4`, remove worker service
- **Dockerfile-plugin_dev**: Remove GIS apt packages (`gdal-bin libgdal-dev libgeos-dev libproj-dev`), change plugin path to `/opt/netbox-sqids`
- **configuration.py**: Use `django.db.backends.postgresql` engine instead of PostGIS, remove GIS-specific options
- **env files, entrypoint, requirements-dev.txt, home/**: Copy as-is from netbox-pathways

- [ ] **Step 1: Create all devcontainer files**

- [ ] **Step 2: Commit**

```bash
git add .devcontainer/
git commit -m "feat: add devcontainer configuration"
```

---

## Chunk 2: Core SQID Logic (TDD)

### Task 3: Create empty plugin package + test skeleton

**Files:**
- Create: `netbox_sqids/__init__.py`
- Create: `netbox_sqids/sqids.py`
- Create: `netbox_sqids/api/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_sqids.py`

- [ ] **Step 1: Create netbox_sqids/__init__.py with minimal PluginConfig**

```python
from netbox.plugins import PluginConfig

__version__ = '0.1.0'


class NetBoxSqidsConfig(PluginConfig):
    name = 'netbox_sqids'
    verbose_name = 'NetBox SQIDs'
    description = 'Short, URL-safe, globally unique identifiers for every NetBox object'
    version = __version__
    author = 'Jonathan Senecal'
    author_email = 'contact@jonathansenecal.com'
    base_url = 'sqids'
    default_settings = {
        'min_length': 4,
        'blocklist': None,
        'monkeypatched_url_prefix': 's',
    }


config = NetBoxSqidsConfig
```

- [ ] **Step 2: Create empty netbox_sqids/sqids.py**

```python
# SQID encoding/decoding logic — will be populated via TDD
```

- [ ] **Step 3: Create empty netbox_sqids/api/__init__.py and tests/__init__.py**

- [ ] **Step 4: Commit**

```bash
git add netbox_sqids/ tests/
git commit -m "feat: add empty plugin package skeleton"
```

### Task 4: TDD — Sqids instance and SqidDescriptor

**Files:**
- Modify: `tests/test_sqids.py`
- Modify: `netbox_sqids/sqids.py`

- [ ] **Step 1: Write failing tests for get_sqids_instance()**

```python
import pytest
from netbox_sqids.sqids import get_sqids_instance

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_sqids.py -v`
Expected: FAIL — `ImportError: cannot import name 'get_sqids_instance'`

- [ ] **Step 3: Implement get_sqids_instance()**

```python
from sqids import Sqids

ALPHABET = "0123456789ACDEFGHJKLMNPQRSTUVWXYZ"


def get_sqids_instance(min_length: int = 4, blocklist: list[str] | None = None) -> Sqids:
    if blocklist is None:
        from sqids.constants import DEFAULT_BLOCKLIST
        blocklist = list(DEFAULT_BLOCKLIST) + ["ck", "sex", "butt"]
    return Sqids(alphabet=ALPHABET, min_length=min_length, blocklist=blocklist)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_sqids.py::TestSqidsInstance -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add netbox_sqids/sqids.py tests/test_sqids.py
git commit -m "feat: add Sqids instance factory with custom alphabet"
```

### Task 5: TDD — SqidDescriptor

**Files:**
- Modify: `tests/test_sqids.py`
- Modify: `netbox_sqids/sqids.py`

- [ ] **Step 1: Write failing tests for SqidDescriptor**

```python
from unittest.mock import patch, MagicMock
from netbox_sqids.sqids import SqidDescriptor, get_sqids_instance


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_sqids.py::TestSqidDescriptor -v`
Expected: FAIL — `ImportError: cannot import name 'SqidDescriptor'`

- [ ] **Step 3: Implement SqidDescriptor**

Add to `netbox_sqids/sqids.py`:

```python
from django.contrib.contenttypes.models import ContentType


class SqidDescriptor:
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
```

Also add a module-level lazy singleton:

```python
_sqids_instance = None


def _get_instance() -> Sqids:
    global _sqids_instance
    if _sqids_instance is None:
        from django.conf import settings
        plugin_settings = settings.PLUGINS_CONFIG.get('netbox_sqids', {})
        _sqids_instance = get_sqids_instance(
            min_length=plugin_settings.get('min_length', 4),
            blocklist=plugin_settings.get('blocklist', None),
        )
    return _sqids_instance
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_sqids.py::TestSqidDescriptor -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add netbox_sqids/sqids.py tests/test_sqids.py
git commit -m "feat: add SqidDescriptor with lazy singleton"
```

### Task 6: TDD — resolve_sqid()

**Files:**
- Modify: `tests/test_sqids.py`
- Modify: `netbox_sqids/sqids.py`

- [ ] **Step 1: Write failing tests for resolve_sqid()**

```python
from django.core.exceptions import ObjectDoesNotExist
from netbox_sqids.sqids import resolve_sqid, get_sqids_instance


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_sqids.py::TestResolveSqid -v`
Expected: FAIL — `ImportError: cannot import name 'resolve_sqid'`

- [ ] **Step 3: Implement resolve_sqid()**

Add to `netbox_sqids/sqids.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_sqids.py::TestResolveSqid -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add netbox_sqids/sqids.py tests/test_sqids.py
git commit -m "feat: add resolve_sqid() function"
```

---

## Chunk 3: Views (TDD)

### Task 7: TDD — Browser redirect view

**Files:**
- Create: `netbox_sqids/views.py`
- Create: `netbox_sqids/urls.py`
- Create: `tests/test_views.py`

- [ ] **Step 1: Write failing tests for browser redirect**

```python
import pytest
from unittest.mock import patch, MagicMock
from django.test import RequestFactory

from netbox_sqids.views import SqidRedirectView
from netbox_sqids.sqids import get_sqids_instance


class TestSqidRedirectView:
    def setup_method(self):
        self.factory = RequestFactory()

    @patch("netbox_sqids.views.resolve_sqid")
    def test_redirects_to_absolute_url(self, mock_resolve):
        mock_obj = MagicMock()
        mock_obj.get_absolute_url.return_value = "/dcim/devices/42/"
        mock_resolve.return_value = mock_obj

        request = self.factory.get("/plugins/sqids/ABCD/")
        response = SqidRedirectView.as_view()(request, sqid="ABCD")

        assert response.status_code == 302
        assert response.url == "/dcim/devices/42/"

    @patch("netbox_sqids.views.resolve_sqid")
    def test_invalid_sqid_returns_404(self, mock_resolve):
        mock_resolve.side_effect = ValueError("Invalid SQID")

        request = self.factory.get("/plugins/sqids/XXXX/")
        response = SqidRedirectView.as_view()(request, sqid="XXXX")

        assert response.status_code == 404

    @patch("netbox_sqids.views.resolve_sqid")
    def test_object_not_found_returns_404(self, mock_resolve):
        from django.core.exceptions import ObjectDoesNotExist
        mock_resolve.side_effect = ObjectDoesNotExist()

        request = self.factory.get("/plugins/sqids/ABCD/")
        response = SqidRedirectView.as_view()(request, sqid="ABCD")

        assert response.status_code == 404

    @patch("netbox_sqids.views.resolve_sqid")
    def test_no_get_absolute_url_returns_404(self, mock_resolve):
        mock_obj = MagicMock(spec=[])  # no get_absolute_url
        mock_resolve.return_value = mock_obj

        request = self.factory.get("/plugins/sqids/ABCD/")
        response = SqidRedirectView.as_view()(request, sqid="ABCD")

        assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_views.py::TestSqidRedirectView -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement browser redirect view**

`netbox_sqids/views.py`:

```python
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect
from django.views import View

from netbox_sqids.sqids import resolve_sqid


class SqidRedirectView(View):
    def get(self, request, sqid):
        try:
            obj = resolve_sqid(sqid)
        except (ValueError, ObjectDoesNotExist):
            raise Http404

        if not hasattr(obj, 'get_absolute_url'):
            raise Http404

        return HttpResponseRedirect(obj.get_absolute_url())
```

- [ ] **Step 4: Create netbox_sqids/urls.py**

```python
from django.urls import path

from netbox_sqids.views import SqidRedirectView

urlpatterns = [
    path('<str:sqid>/', SqidRedirectView.as_view(), name='sqid_redirect'),
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_views.py::TestSqidRedirectView -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add netbox_sqids/views.py netbox_sqids/urls.py tests/test_views.py
git commit -m "feat: add browser redirect view"
```

### Task 8: TDD — API redirect view

**Files:**
- Create: `netbox_sqids/api/views.py`
- Create: `netbox_sqids/api/urls.py`
- Modify: `tests/test_views.py`

- [ ] **Step 1: Write failing tests for API redirect**

Add to `tests/test_views.py`:

```python
from netbox_sqids.api.views import SqidApiRedirectView


class TestSqidApiRedirectView:
    def setup_method(self):
        self.factory = RequestFactory()

    @patch("netbox_sqids.api.views.reverse")
    @patch("netbox_sqids.api.views.get_viewname")
    @patch("netbox_sqids.api.views.resolve_sqid")
    def test_redirects_to_api_url(self, mock_resolve, mock_get_viewname, mock_reverse):
        mock_obj = MagicMock()
        mock_obj.pk = 42
        mock_resolve.return_value = mock_obj
        mock_get_viewname.return_value = "dcim-api:device-detail"
        mock_reverse.return_value = "/api/dcim/devices/42/"

        request = self.factory.get("/api/plugins/sqids/ABCD/")
        response = SqidApiRedirectView.as_view()(request, sqid="ABCD")

        assert response.status_code == 302
        assert response.url == "/api/dcim/devices/42/"
        mock_get_viewname.assert_called_once_with(mock_obj, action='detail', rest_api=True)
        mock_reverse.assert_called_once_with("dcim-api:device-detail", kwargs={"pk": 42})

    @patch("netbox_sqids.api.views.resolve_sqid")
    def test_invalid_sqid_returns_404(self, mock_resolve):
        mock_resolve.side_effect = ValueError("Invalid SQID")

        request = self.factory.get("/api/plugins/sqids/XXXX/")
        response = SqidApiRedirectView.as_view()(request, sqid="XXXX")

        assert response.status_code == 404

    @patch("netbox_sqids.api.views.resolve_sqid")
    def test_object_not_found_returns_404(self, mock_resolve):
        from django.core.exceptions import ObjectDoesNotExist
        mock_resolve.side_effect = ObjectDoesNotExist()

        request = self.factory.get("/api/plugins/sqids/ABCD/")
        response = SqidApiRedirectView.as_view()(request, sqid="ABCD")

        assert response.status_code == 404

    @patch("netbox_sqids.api.views.get_viewname")
    @patch("netbox_sqids.api.views.resolve_sqid")
    def test_no_api_viewname_returns_404(self, mock_resolve, mock_get_viewname):
        mock_obj = MagicMock()
        mock_resolve.return_value = mock_obj
        mock_get_viewname.side_effect = AttributeError()

        request = self.factory.get("/api/plugins/sqids/ABCD/")
        response = SqidApiRedirectView.as_view()(request, sqid="ABCD")

        assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_views.py::TestSqidApiRedirectView -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement API redirect view**

`netbox_sqids/api/views.py`:

```python
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from netbox.api.viewsets import get_viewname
from netbox_sqids.sqids import resolve_sqid


class SqidApiRedirectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, sqid):
        try:
            obj = resolve_sqid(sqid)
        except (ValueError, ObjectDoesNotExist):
            raise Http404

        try:
            viewname = get_viewname(obj, action='detail', rest_api=True)
            url = reverse(viewname, kwargs={'pk': obj.pk})
        except (AttributeError, Exception):
            raise Http404

        return HttpResponseRedirect(url)
```

- [ ] **Step 4: Create netbox_sqids/api/urls.py**

```python
from django.urls import path

from netbox_sqids.api.views import SqidApiRedirectView

urlpatterns = [
    path('<str:sqid>/', SqidApiRedirectView.as_view(), name='sqid_api_redirect'),
]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_views.py::TestSqidApiRedirectView -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add netbox_sqids/api/views.py netbox_sqids/api/urls.py tests/test_views.py
git commit -m "feat: add API redirect view"
```

---

## Chunk 4: Auto-Discovery and Monkey-Patch URLs

### Task 9: Implement ready() — auto-discovery + monkey-patch

**Files:**
- Modify: `netbox_sqids/__init__.py`

- [ ] **Step 1: Add ready() method to PluginConfig**

```python
import logging

from netbox.plugins import PluginConfig

__version__ = '0.1.0'

logger = logging.getLogger(__name__)


class NetBoxSqidsConfig(PluginConfig):
    name = 'netbox_sqids'
    verbose_name = 'NetBox SQIDs'
    description = 'Short, URL-safe, globally unique identifiers for every NetBox object'
    version = __version__
    author = 'Jonathan Senecal'
    author_email = 'contact@jonathansenecal.com'
    base_url = 'sqids'
    default_settings = {
        'min_length': 4,
        'blocklist': None,
        'monkeypatched_url_prefix': 's',
    }

    def ready(self):
        super().ready()
        self._patch_models()
        self._patch_urls()

    def _patch_models(self):
        from django.apps import apps
        from netbox_sqids.sqids import SqidDescriptor

        for model in apps.get_models():
            model.add_to_class('sqid', SqidDescriptor())

    def _patch_urls(self):
        from django.conf import settings

        plugin_settings = settings.PLUGINS_CONFIG.get('netbox_sqids', {})
        prefix = plugin_settings.get('monkeypatched_url_prefix',
                                     self.default_settings['monkeypatched_url_prefix'])
        if prefix is None:
            return

        try:
            from django.urls import path
            import netbox.urls
            import netbox.api.urls
            from netbox_sqids.views import SqidRedirectView
            from netbox_sqids.api.views import SqidApiRedirectView

            netbox.urls.urlpatterns.append(
                path(f'{prefix}/<str:sqid>/', SqidRedirectView.as_view(), name='sqid_short_redirect')
            )
            netbox.api.urls.urlpatterns.append(
                path(f'{prefix}/<str:sqid>/', SqidApiRedirectView.as_view(), name='sqid_short_api_redirect')
            )
        except Exception:
            logger.warning("Failed to monkey-patch short SQID URLs. "
                           "The standard /plugins/sqids/ routes still work.", exc_info=True)


config = NetBoxSqidsConfig
```

- [ ] **Step 2: Commit**

```bash
git add netbox_sqids/__init__.py
git commit -m "feat: add auto-discovery and monkey-patched short URLs in ready()"
```

### Task 10: Run full test suite

- [ ] **Step 1: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 2: Run ruff**

Run: `ruff check netbox_sqids/ tests/`
Expected: No errors

- [ ] **Step 3: Fix any issues found and commit**

```bash
git add -A
git commit -m "fix: address lint/test issues"
```
