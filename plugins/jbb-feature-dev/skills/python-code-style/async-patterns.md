# Async Patterns

Comprehensive async/await patterns for Python, particularly important for LLM/AI integrations.

## HTTP Client Selection

### When to Use aiohttp
- High-concurrency scenarios (many simultaneous requests)
- Performance-critical applications
- 10x+ faster than httpx for concurrent requests

### When to Use httpx
- Need HTTP/2 support
- Want sync/async flexibility in same codebase
- Simpler API similar to requests

## Basic Async Patterns

### Pattern: Async Context Manager for HTTP

Before:
```python
import requests

def fetch_data(url: str) -> dict:
    response = requests.get(url)
    return response.json()
```

After:
```python
import aiohttp

async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### Pattern: Concurrent Requests with gather()

Before:
```python
def fetch_all(urls: list[str]) -> list[dict]:
    results = []
    for url in urls:
        response = requests.get(url)
        results.append(response.json())
    return results
```

After:
```python
async def fetch_all(urls: list[str]) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_one(session, url) for url in urls]
        return await asyncio.gather(*tasks)

async def fetch_one(session: aiohttp.ClientSession, url: str) -> dict:
    async with session.get(url) as response:
        return await response.json()
```

## Structured Concurrency (Python 3.11+)

### Pattern: TaskGroup (Preferred over gather)

Before (gather):
```python
async def process_all(items: list[str]) -> list[Result]:
    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks)
```

After (TaskGroup - safer):
```python
async def process_all(items: list[str]) -> list[Result]:
    results = []
    async with asyncio.TaskGroup() as tg:
        for item in items:
            tg.create_task(process_and_collect(item, results))
    return results

async def process_and_collect(item: str, results: list) -> None:
    result = await process_item(item)
    results.append(result)
```

**Why TaskGroup is safer**:
- Automatically cancels remaining tasks if one fails
- Proper exception handling with ExceptionGroup
- Enforces structured concurrency

## Rate Limiting with Semaphores

### Pattern: Limit Concurrent API Calls

```python
# Essential for LLM APIs with rate limits
async def fetch_with_limit(
    urls: list[str],
    max_concurrent: int = 10
) -> list[dict]:
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_one(url: str) -> dict:
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.json()

    return await asyncio.gather(*[fetch_one(url) for url in urls])
```

## LLM SDK Patterns

### Pattern: Anthropic Async Client

Before (sync):
```python
from anthropic import Anthropic

client = Anthropic()
message = client.messages.create(
    model="claude-sonnet-4-6-20250620",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}]
)
```

After (async):
```python
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def get_completion(prompt: str) -> str:
    message = await client.messages.create(
        model="claude-sonnet-4-6-20250620",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text
```

### Pattern: Streaming with Async

```python
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

async def stream_completion(prompt: str) -> AsyncIterator[str]:
    async with client.messages.stream(
        model="claude-sonnet-4-6-20250620",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        async for text in stream.text_stream:
            yield text
```

### Pattern: Concurrent LLM Calls with Rate Limiting

```python
async def batch_completions(
    prompts: list[str],
    max_concurrent: int = 5  # Respect API rate limits
) -> list[str]:
    semaphore = asyncio.Semaphore(max_concurrent)

    async def get_one(prompt: str) -> str:
        async with semaphore:
            return await get_completion(prompt)

    return await asyncio.gather(*[get_one(p) for p in prompts])
```

## Error Handling

### Pattern: Proper Exception Handling

Before:
```python
async def fetch_data(url: str) -> dict | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()
    except:  # BAD - catches everything
        return None
```

After:
```python
async def fetch_data(url: str) -> dict | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as e:
        logger.warning(f"HTTP error fetching {url}: {e}")
        return None
    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching {url}")
        return None
```

### Pattern: Cleanup with try/finally

```python
async def process_with_cleanup() -> None:
    resource = await acquire_resource()
    try:
        await do_work(resource)
    finally:
        await resource.close()  # Always cleanup
```

### Pattern: gather with return_exceptions

```python
async def fetch_all_safe(urls: list[str]) -> list[dict | Exception]:
    tasks = [fetch_one(url) for url in urls]
    # Returns exceptions instead of raising
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Failed to fetch {urls[i]}: {result}")

    return [r for r in results if not isinstance(r, Exception)]
```

## Queue Shutdown (Python 3.13+)

### Pattern: Clean Queue Shutdown

Before:
```python
# Sentinel value pattern — error-prone and verbose
STOP = object()

async def producer(q: asyncio.Queue) -> None:
    for i in range(10):
        await q.put(i)
    await q.put(STOP)  # Must remember the sentinel

async def consumer(q: asyncio.Queue) -> None:
    while True:
        item = await q.get()
        if item is STOP:
            break
        process(item)
        q.task_done()
```

After:
```python
from asyncio import Queue, QueueShutDown

async def producer(q: Queue[int]) -> None:
    for i in range(10):
        await q.put(i)
    q.shutdown()  # Clean signal to all consumers

async def consumer(q: Queue[int]) -> None:
    try:
        while True:
            item = await q.get()
            process(item)
            q.task_done()
    except QueueShutDown:
        return  # Clean exit
```

**Note**: TaskGroup cancellation improved in 3.13 -- better handling of simultaneous internal and external cancellations. No syntax change but more robust behavior.

## Anti-Patterns to Avoid

### Anti-Pattern: Blocking Calls in Async

```python
# BAD - blocks event loop
async def bad_example():
    time.sleep(1)  # WRONG
    requests.get(url)  # WRONG

# GOOD - non-blocking
async def good_example():
    await asyncio.sleep(1)
    async with aiohttp.ClientSession() as session:
        await session.get(url)
```

### Anti-Pattern: Fire-and-Forget Tasks

```python
# BAD - task may fail silently
async def bad_example():
    asyncio.create_task(some_work())  # No await, no error handling
    return "done"

# GOOD - track the task
async def good_example():
    task = asyncio.create_task(some_work())
    try:
        await task
    except Exception as e:
        logger.error(f"Background task failed: {e}")
```

### Anti-Pattern: Missing Session Reuse

```python
# BAD - creates new session per request
async def bad_fetch_all(urls: list[str]) -> list[dict]:
    results = []
    for url in urls:
        async with aiohttp.ClientSession() as session:  # New session each time!
            async with session.get(url) as response:
                results.append(await response.json())
    return results

# GOOD - reuse session
async def good_fetch_all(urls: list[str]) -> list[dict]:
    async with aiohttp.ClientSession() as session:  # One session
        tasks = [fetch_one(session, url) for url in urls]
        return await asyncio.gather(*tasks)
```

## Type Hints for Async

### Pattern: Async Function Return Types

```python
# Return the actual type, not Coroutine[...]
async def get_user(id: int) -> User:
    ...

async def get_users() -> list[User]:
    ...

async def find_user(id: int) -> User | None:
    ...
```

### Pattern: Async Generator

```python
from collections.abc import AsyncIterator

async def stream_results() -> AsyncIterator[Result]:
    async for item in source:
        yield process(item)
```

### Pattern: Async Callback Type

```python
from collections.abc import Awaitable, Callable

OnComplete = Callable[[Result], Awaitable[None]]

async def process_with_callback(
    data: Data,
    on_complete: OnComplete
) -> None:
    result = await process(data)
    await on_complete(result)
```

## Entry Point Pattern

### Pattern: asyncio.run() at Entry Point Only

```python
async def main() -> None:
    results = await fetch_all(urls)
    await process_results(results)

if __name__ == "__main__":
    asyncio.run(main())
```

**Note**: Never call `asyncio.run()` from within async code - it creates a new event loop.
