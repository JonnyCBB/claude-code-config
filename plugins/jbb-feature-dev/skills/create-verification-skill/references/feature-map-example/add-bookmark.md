# Add a bookmark

A caller stores a URL with a title and receives an id.

## Sub-features

- `add-valid` stores a bookmark and returns 201 with an id.
- `add-duplicate` returns 409 for a URL that is already stored.
- `add-invalid-url` returns 400 and stores nothing.

## How to get to it (caller POV)

- `POST /v1/bookmarks` with a JSON body that has `url` and `title`.
- No authentication on a local run.

## Driving it with curl

Preconditions: Doctor passes and the store is empty.

1. `curl -s -i -X POST http://127.0.0.1:$PORT/v1/bookmarks -d '{"url":"https://example.org","title":"Example"}'`. Expect `201` and an `id` in the body.
2. `curl -s http://127.0.0.1:$PORT/v1/bookmarks/<id>`. Expect the same `url` and `title`.
3. Repeat step 1. Expect `409`, and the stored count is still 1.

Evidence: the status line and body of each step, written to the evidence directory.

## Gotchas

- The store persists between runs unless Cleanup resets it. A leftover row turns step 1 into a 409.
