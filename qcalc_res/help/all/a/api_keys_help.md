# API Keys

## Purpose

Use `api_keys()` to manage your personal API keys for supported providers.

This calculator lets you:

- activate or inactivate use of all personal API keys
- set or replace one provider key at a time
- delete a provider key
- check status for personal and system fallback keys

## Security and Storage

- Personal API keys are encrypted before storage.
- qCalc shows only masked key status, never the full key.
- When available, qCalc shows only the last 4 characters as:
  `Configured (…A1b2)`.

## Input Fields

### Action

Choose what you want to do:

- **Show status**
- **Activate personal keys**
- **Inactivate personal keys**
- **Set / Replace key**
- **Delete key**

### Provider

Choose the provider key to manage (shown for provider-specific actions).

### API Key

Enter a new key only for **Set / Replace key**.

## Global Active Switch

`api_keys()` also controls a single user preference:

Behavior:

- **Yes**: qCalc may use your personal key for the selected provider.
- **No**: qCalc ignores personal keys and uses system fallback keys only.

## Runtime Key Resolution

When a provider call needs a key:

1. If personal keys are active, qCalc tries your personal key first.
2. If unavailable, qCalc uses the system key configured in settings.
3. If neither exists, the action fails with a clear missing-key error.


## Notes

- This calculator manages one provider key per action for safer handling.
- Inactivating personal keys does not delete stored keys; it only disables use.
- Inactivating is a good choice when you are not actively using qCalc and want an extra
  protection layer so your personal keys are not used until you activate them again.
