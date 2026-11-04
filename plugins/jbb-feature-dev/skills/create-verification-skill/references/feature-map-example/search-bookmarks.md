# Search bookmarks

A caller finds stored bookmarks by a word in the title or a tag.

## Sub-features

- `search-title` returns bookmarks whose title contains the query.
- `search-tag` returns bookmarks that carry the tag.
- `search-empty` returns an empty list, not an error, when nothing matches.

## How to get to it (caller POV)

- `GET /v1/bookmarks?q=<word>` or `GET /v1/bookmarks?tag=<tag>`.

## Driving it with curl

Preconditions: Doctor passes and the store holds at least one bookmark with a tag.

1. `curl -s "http://127.0.0.1:$PORT/v1/bookmarks?tag=reading"`. Expect only the bookmarks with that tag.
2. `curl -s "http://127.0.0.1:$PORT/v1/bookmarks?q=zzzz"`. Expect `200` and `[]`.

Evidence: the response body of each step.

## Gotchas

- The seed data has no tagged bookmarks, so step 1 fails with an empty list. The journey stays failing until the seed data has a tag. Do not change the expected result.
