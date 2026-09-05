# Targeting Patterns

Configuring experiment audience targeting.

## Available Targeting Options

| Targeting | Description | Use Case |
|-----------|-------------|----------|
| Country | Geographic markets | Market-specific features |
| Platform | iOS, Android, Web | Platform-specific changes |
| App Version | Minimum version | New API requirements |
| User Segment | Custom BigQuery segment | Specific user groups |

## Country Targeting

```
Markets: US, GB, DE
```

**Considerations:**
- Larger markets = faster experiment
- Consider cultural differences
- Check metric availability per market

## Platform Targeting

```
Platforms: iOS, Android
```

**Considerations:**
- Platform-specific features only
- Mobile property propagation delay
- Consider cross-platform analysis

## App Version Targeting

```
iOS >= 8.7.0
Android >= 8.7.0.1000
```

**When Required:**
- New SDK features
- API changes
- Bug fixes in specific versions

## User Segment Targeting

Custom BigQuery-based segments:

```sql
SELECT user_id
FROM user_segments
WHERE segment = 'power_users'
```

**Considerations:**
- Requires BigQuery targeting setup
- May have bloom filter false positives (offline)
- Use online resolution for accuracy
- **Does not work when resolving via `exp-planner-lib`'s offline resolver** — if your service uses that offline resolver, BigQuery custom-dataset targeting won't apply; you'll need online resolution instead
- Not currently supported for ad-serving/GAM targeting

## Exclusivity Groups

Prevent users from being in multiple experiments:

```
Exclusivity Group: search_ranking_experiments
```

**When to Use:**
- Experiments affect same user journey
- Properties could interact
- Need clean measurement

## Holdback Groups

A related but distinct mechanic from exclusivity groups: holdback groups keep a subset of users out of a shipped feature (post-launch) for longer-term impact measurement, rather than preventing overlap between concurrently-running experiments. Use when you need to measure a feature's ongoing effect after it's shipped to everyone else, not just during the initial experiment window.

## Targeting Validation

1. Check targeting covers sufficient users
2. Verify no unintended exclusions
3. Test with specific user IDs
4. Monitor early SRM for targeting issues
