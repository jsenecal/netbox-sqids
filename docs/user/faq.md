# FAQ

## Are SQIDs secure? Can I use them as access tokens?

**No.** SQIDs are obfuscation, not security. The encoding is reversible by
anyone with the algorithm, alphabet, and parameters -- all of which are
public information in this open-source plugin. Anyone who sees a SQID can
decode it back to the content type id and primary key.

Use SQIDs as user-friendly identifiers for things you already expose
(detail pages, API endpoints). NetBox's normal authentication and
permission framework remains the only thing protecting the underlying
objects.

## How do SQIDs compare to UUIDs?

| Property | SQID | UUID |
|----------|------|------|
| Length (typical) | 4-7 chars | 36 chars (with dashes) |
| URL-safe | Yes | Yes |
| Reversible to PK | Yes | No |
| Globally unique within NetBox | Yes | Yes |
| Stable across instances | No | Yes |
| Requires schema change | No | Yes (UUIDField column) |

UUIDs are better when you need cross-instance identity or
cryptographic-grade uniqueness. SQIDs are better when you want short,
human-friendly identifiers without any database changes.

## Are SQIDs deterministic?

Yes, given the same `(content_type_id, pk)`, alphabet, `min_length`, and
blocklist, the encoder always produces the same SQID. This is why the
plugin can compute SQIDs on the fly without storing them.

## Will SQIDs change if I rename a model or move it between apps?

If renaming or moving the model causes Django to allocate a new
`ContentType` row (different `app_label` or `model` name), the SQIDs for
all objects of that model will change. The underlying primary keys do
not, but the encoded pair `(content_type_id, pk)` will use the new
content type id.

Plan for this if you have shared SQIDs externally and you are about to
rename or move a model.

## What happens to SQIDs when an object is deleted?

The SQID itself remains a valid string -- it can still be decoded to a
`(content_type_id, pk)` pair. But `resolve_sqid()` will raise
`ObjectDoesNotExist`, and the redirect view returns 404. SQIDs do not
"reuse" themselves: the next object inserted with the same primary key
(if any) will share the same SQID, just like NetBox itself reuses
primary keys after deletion.

## Can I store SQIDs in a column for indexing?

You can, but you usually should not. The point of the plugin is that
SQIDs are computed on demand from existing data. If you store SQIDs in a
column, you take on the responsibility of refreshing that column whenever
the encoding parameters change. If you really need indexable SQIDs (for
example, a chat bot that wants to look up by SQID), prefer indexing the
content type id and primary key directly and decoding on input.

## Will SQIDs always be 4 characters?

No. The default `min_length` is 4, but the encoder produces longer SQIDs
when the encoded numbers are larger or when the blocklist forces a
re-roll. As your NetBox grows past a few thousand objects, expect 5-6
character SQIDs to dominate.

## Can I customize the alphabet?

Not via configuration. The alphabet is hardcoded in `netbox_sqids/sqids.py`
because changing it would invalidate every existing SQID. If you want to
experiment, fork the plugin or open an issue describing your use case.

## Does the plugin add load to my NetBox install?

Negligible. The descriptor is read-only and lazy: it costs nothing until
something accesses `obj.sqid`. When accessed, the cost is one
`ContentType.objects.get_for_model()` call (cached) and one `sqids.encode`
call (a few microseconds for short ids). Decoding is similarly cheap.

The plugin registers no signals, no middleware, and no background tasks.

## Do SQIDs work for objects in plugins, not just NetBox core?

Yes. The plugin attaches the descriptor to *every* model registered in
the Django application registry, including those from other NetBox
plugins. As long as the plugin's models use integer primary keys, they
get a working `sqid`.

## Can I use the same SQID across multiple NetBox instances?

No. SQIDs are stable per database, not across databases. See
[Troubleshooting](troubleshooting.md#same-object-yields-different-sqids-on-two-netbox-instances)
for details.

## Does the plugin work with NetBox's GraphQL API?

The descriptor works wherever Python attribute access works -- but
NetBox's GraphQL schema is generated from declared fields and does not
auto-discover descriptors. Adding `sqid` to the GraphQL schema would
require a schema-extension hook that this plugin does not currently
provide. Contributions welcome.
