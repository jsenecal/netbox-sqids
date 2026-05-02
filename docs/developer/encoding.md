# Encoding deep dive

This page goes deeper than [Architecture](architecture.md) on how SQIDs
are produced, why the alphabet looks the way it does, and what kinds of
changes invalidate previously generated identifiers.

## The sqids algorithm in one paragraph

[Sqids](https://sqids.org/) is a small library that converts a list of
non-negative integers into a short alphanumeric string and back. It is
not a hash and not a cipher. The encoding uses a position-dependent
permutation of a configurable alphabet plus a check character, and it
respects two parameters that affect the output for a given input:

- **`alphabet`** -- the set of characters used in the output. Permuted
  internally per encode call.
- **`min_length`** -- the encoder pads the output with extra alphabet
  characters until the result is at least this long.
- **`blocklist`** -- if the encoded string contains a blocked substring,
  the encoder rotates internal state and re-encodes until the output is
  clean.

There is no salt or secret. The mapping from `(numbers, alphabet, min_length, blocklist)`
to the encoded string is fully deterministic and reversible by anyone
with the same parameters.

## What this plugin encodes

For every NetBox object the plugin encodes a two-element list:

```python
sqids.encode([content_type_id, primary_key])
```

`content_type_id` is the Django `ContentType` framework's id for the
model class (one row in `django_content_type`). `primary_key` is the
object's integer PK. Both come from a single Django app, so within a
NetBox database the pair is unique.

Decoding inverts the process:

```python
[ct_id, pk] = sqids.decode(token)
ct = ContentType.objects.get_for_id(ct_id)
obj = ct.get_object_for_this_type(pk=pk)
```

If the token decodes to a list of length other than 2, `resolve_sqid()`
raises `ValueError`. If the content type or primary key no longer exist,
the underlying ORM raises `ObjectDoesNotExist`.

## The alphabet

```python
ALPHABET = "0123456789ACDEFGHJKLMNPQRSTUVWXYZ"
```

That is 33 characters: 10 digits and 23 letters. The full uppercase Latin
alphabet has 26 letters; we drop three:

| Excluded | Reason |
|----------|--------|
| **B**    | Looks like **8** in many fonts and on labels printed at small sizes. |
| **I**    | Looks like **1** and like a lowercase **l**. |
| **O**    | Looks like **0**. |

The alphabet is uppercase-only. Lowercase `l` is excluded because we
have no lowercase letters at all, and `1` is preserved separately. This
is the same family of choices that Crockford's base32 makes for
human-readable identifiers, with one extra exclusion (`B`).

### Why uppercase only?

Uppercase letters are easier to read out loud, type from a printed
label, or copy from a screenshot. The cost is a slightly less compact
encoding (33 characters vs 62 for full alphanumeric mixed-case), which
is still well within the budget for short ids.

### Why hardcoded?

The alphabet is part of the encoding -- changing it produces different
SQIDs for the same `(content_type_id, pk)`. Treating it as a constant
makes it impossible to flip by accident from configuration. If you have
a strong reason to change the alphabet (for example, you want lowercase
or you want to allow Cyrillic letters), fork the plugin or open an issue.

## `min_length`

The default minimum length is 4. The encoder pads shorter outputs by
producing extra alphabet characters that still decode back to the same
input. With a 33-character alphabet and four characters, the address
space is 33^4 = 1_185_921. The encoder never produces colliding outputs
for distinct inputs, so practical capacity is bounded by the
`(content_type_id, pk)` space rather than the alphabet space.

In a typical NetBox install, expect:

- 4-character SQIDs for the first few thousand objects.
- 5-character SQIDs as content types and primary keys grow.
- Occasional re-rolls to 5 characters when the blocklist filters a
  shorter form.

Increasing `min_length` to 6 or 8 produces uniform-looking IDs at the
cost of length. It is encoding-affecting -- pick a value at deployment
time and stick with it.

## The blocklist

```python
DEFAULT_BLOCKLIST + ["ck", "sex", "butt"]
```

The library ships with an English blocklist of a few hundred substrings
considered offensive or trademarked. The plugin extends it with three
additional terms common in network labels.

When an encoded string contains a blocked substring, the encoder rotates
internal state and re-encodes the same input, repeating until the output
is clean. This means:

- Blocking a word never changes the underlying mapping for unaffected
  inputs.
- Blocking a word *does* change the SQID for any input that previously
  produced that word, and any input whose new output happens to match a
  different blocklist entry.

In practice, with 4-character SQIDs and the default blocklist, almost no
inputs collide with the blocklist. As `min_length` grows or the
blocklist expands, more inputs may shift.

## What "encoding-affecting" means

A change is "encoding-affecting" if it makes the encoder produce a
different output for the same `(content_type_id, pk)` pair. The
following changes are encoding-affecting:

- Changing the alphabet (currently hardcoded -- only matters if you fork).
- Changing `min_length`.
- Changing `blocklist` (only for inputs that match a now-blocked or
  now-unblocked word).
- Plugin upgrades that touch the encoding pipeline -- for example,
  switching from `[ct_id, pk]` to a different tuple shape, or adding a
  salt.

The plugin is in alpha. Any of the above can happen between releases and
will be flagged in the [changelog](../changelog.md). Once the plugin
hits 1.0, the encoding becomes a versioned, stable contract.

## Collisions

By construction, two distinct `(content_type_id, pk)` pairs always
produce two distinct SQIDs (the algorithm is invertible). Two pairs with
the same `pk` but different `content_type_id` produce different SQIDs.

Tokens that are not produced by the encoder may still happen to decode
into a list of two integers -- they are simply random-looking
combinations within the alphabet. `resolve_sqid()` catches the case
where the decoded length is not exactly 2 (`ValueError`), and the
content type or object lookups catch unknown ids (`ObjectDoesNotExist`).

## Why no salt?

The sqids library accepts an alphabet but no separate salt: it derives
all internal state from the alphabet permutation. Because we use a
fixed alphabet, the encoding is a public, deterministic mapping. That is
intentional -- SQIDs are *not* a security feature. See the
[FAQ on SQID security](../user/faq.md#are-sqids-secure-can-i-use-them-as-access-tokens).

If you need unguessable identifiers, layer on top of SQIDs (sign them,
add a HMAC, use a session token), or pick a different abstraction
entirely.
