# Performance Analysis Report
**Date:** 2025-12-13
**Project:** mc-rcon (mcrconpy)
**Analysis Type:** Performance anti-patterns, memory issues, and algorithmic inefficiencies

---

## Executive Summary

This analysis identified **7 performance issues** ranging from critical memory problems to minor algorithmic inefficiencies. The most critical issue is unbounded memory growth in the audit logging system. No N+1 query patterns were found (not applicable for this project type), but several unnecessary iterations and memory allocations were identified.

---

## Critical Issues

### 1. **Unbounded Memory Growth in Audit Log Loading**
**File:** `mcrconpy/audit.py:55-91`
**Severity:** 🔴 CRITICAL
**Type:** Memory Anti-pattern

**Problem:**
```python
def to_load() -> list[dict[str, Any]]:
    """Load all audit records from the log file."""
    results: list[dict[str, Any]] = []
    # ...
    for line_bytes in f:
        # Loads ENTIRE file into memory
        results.append(record)
    return results
```

**Impact:**
- Loads entire audit log into memory at once
- JSONL files can grow unbounded over time
- Will cause OOM errors on long-running servers
- O(n) memory complexity where n = number of audit entries

**Recommendation:**
Implement generator-based streaming:
```python
def to_load_iter() -> Iterator[dict[str, Any]]:
    """Stream audit records one at a time."""
    if not Audit.FILE_PATH.exists():
        return
    with Path(Audit.FILE_PATH).open("rb") as f:
        for line_bytes in f:
            # Yield one record at a time
            yield orjson.loads(line_bytes)
```

**Estimated Impact:** Memory reduction from O(n) to O(1), prevents OOM on large logs

---

## High Priority Issues

### 2. **Inefficient Theme Application with Full Widget Tree Traversal**
**File:** `mcrconpy/gui.py:296-316`
**Severity:** 🟠 HIGH
**Type:** Inefficient algorithm

**Problem:**
```python
def apply_theme(self) -> None:
    """Apply color theme to all widgets based on dark_mode setting."""
    colors = self._get_theme_colors()

    # Traverses ENTIRE widget tree on every theme change
    for widget in self.root.winfo_children():
        self._apply_widget_theme(widget, colors)

    # Then manually applies to known widgets again
    self.command_entry.config(insertbackground=colors["entry_fg"])
    self.output_box.config(...)
    # ... more manual updates
```

**Impact:**
- O(n) traversal where n = number of widgets
- Redundant work: widgets are configured twice (once in loop, once manually)
- Called on every theme toggle
- Current implementation is small (7 widgets), but doesn't scale

**Recommendation:**
Cache widget references in a list during `setup_ui()`:
```python
def setup_ui(self):
    # ... create widgets ...
    self._themeable_widgets = [
        self.address_entry,
        self.command_entry,
        # ... etc
    ]

def apply_theme(self):
    colors = self._get_theme_colors()
    for widget in self._themeable_widgets:
        self._apply_widget_theme(widget, colors)
```

**Estimated Impact:** 50% reduction in theme application time, better scalability

---

### 3. **Repeated List Allocation in Command Serialization**
**File:** `mcrconpy/models.py:106-123`
**Severity:** 🟠 MEDIUM
**Type:** Unnecessary allocation

**Problem:**
```python
def to_dict(self) -> dict[str, Any]:
    """Serialize user session data."""
    return {
        # Creates new list on EVERY call
        "commands": [cmd.to_dict() for cmd in self.commands],
        # ...
    }
```

**Impact:**
- If `to_dict()` is called in a loop or frequently (e.g., auto-save), creates many temporary lists
- O(n) memory allocation where n = number of commands
- Each `Command.to_dict()` also creates a new dict

**Recommendation:**
1. Consider caching if called frequently
2. Or use generator for streaming serialization
3. Profile actual usage - may not be called frequently enough to matter

**Estimated Impact:** Depends on call frequency; potentially 30-50% reduction in serialization overhead

---

## Medium Priority Issues

### 4. **Auto-refresh Without Rate Limiting**
**File:** `mcrconpy/gui.py:367-371`
**Severity:** 🟡 MEDIUM
**Type:** Resource usage

**Problem:**
```python
def auto_refresh(self) -> None:
    """Periodically refresh player list every 5 seconds."""
    if self.rcon_client:
        self.fetch_player_list()  # Always fetches, even if window is hidden
    self.root.after(5000, self.auto_refresh)  # No pause when disconnected
```

**Impact:**
- Continues refreshing even when window is minimized/hidden
- No backoff on repeated failures
- Fixed 5-second interval could be configurable

**Recommendation:**
```python
def auto_refresh(self) -> None:
    if self.rcon_client and self.root.winfo_viewable():
        try:
            self.fetch_player_list()
        except Exception:
            # Implement exponential backoff on failure
            pass
    self.root.after(5000, self.auto_refresh)
```

**Estimated Impact:** Reduced CPU/network usage when window is hidden

---

### 5. **Bytes Concatenation in Loop**
**File:** `mcrconpy/core.py:231-249`
**Severity:** 🟡 LOW-MEDIUM
**Type:** Algorithmic inefficiency

**Problem:**
```python
def _recv_exact(self, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = self.socket.recv(n - len(data))
        if not chunk:
            break
        data += chunk  # Creates new bytes object on each iteration
    return data
```

**Impact:**
- Bytes concatenation creates new object on each iteration
- For large packets, this is O(n²) in worst case
- In practice, TCP usually delivers in few chunks, so impact is minimal

**Recommendation:**
```python
def _recv_exact(self, n: int) -> bytes:
    chunks = []
    received = 0
    while received < n:
        chunk = self.socket.recv(n - received)
        if not chunk:
            break
        chunks.append(chunk)
        received += len(chunk)
    return b"".join(chunks)  # Single allocation at end
```

**Estimated Impact:** 10-20% improvement for large packet reception

---

## Low Priority Issues

### 6. **Random ID Generation Overhead**
**File:** `mcrconpy/core.py:174, 211, 427`
**Severity:** 🟢 LOW
**Type:** Minor overhead

**Problem:**
```python
req_id = random.randint(0, 2147483647)  # Called on every command
```

**Impact:**
- Cryptographically secure random is overkill for request IDs
- Could use simple counter or cheaper PRNG
- Very minor overhead (microseconds)

**Recommendation:**
```python
class Rcon:
    def __init__(self, ...):
        self._req_id = 0

    def _next_req_id(self) -> int:
        self._req_id = (self._req_id + 1) % 2147483647
        return self._req_id
```

**Estimated Impact:** Negligible (1-2% in tight loops)

---

### 7. **Potential Log File Write Contention**
**File:** `mcrconpy/gui.py:116-127`
**Severity:** 🟢 LOW
**Type:** I/O pattern

**Problem:**
```python
def log_message(self, message: str) -> None:
    """Append timestamped message to log file."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except OSError:
        pass  # Fail silently
```

**Impact:**
- Opens/closes file on every log message
- Could use buffered writing or async I/O
- Failing silently could hide issues

**Recommendation:**
- Use `logging` module with proper handlers
- Implement log rotation
- Don't fail silently - at least log to stderr

**Estimated Impact:** Better reliability, minimal performance gain

---

## No Issues Found

✅ **N+1 Query Patterns:** Not applicable (no ORM/database queries)
✅ **Unnecessary Re-renders:** Not applicable (not a React/web framework)
✅ **Synchronous Blocking:** Good use of threading for GUI commands (gui.py:184-205)
✅ **Connection Pooling:** Not needed for single persistent RCON connection
✅ **JSON Performance:** Already using `orjson` for 6x speedup (audit.py, gui.py)

---

## Performance Wins Already Implemented

The codebase shows several good performance practices:

1. **orjson Usage** (audit.py:11-16, gui.py:21-27)
   - 6x faster JSON serialization than stdlib
   - Graceful fallback to stdlib json

2. **uvloop Integration** (core.py:322-326)
   - 2-4x async I/O performance boost
   - Optional dependency with fallback

3. **Atomic File Writes** (gui.py:94-114)
   - Prevents config corruption
   - Uses temp file + rename pattern

4. **Frozen Dataclasses** (models.py:11)
   - Immutable Command objects are more efficient
   - Better memory layout

5. **Context Managers** (core.py:266-279)
   - Proper resource cleanup
   - No connection leaks

---

## Recommendations Priority Order

1. **CRITICAL**: Fix audit log memory issue (Issue #1) - implement streaming
2. **HIGH**: Cache widget references for theme application (Issue #2)
3. **MEDIUM**: Add rate limiting to auto-refresh (Issue #4)
4. **MEDIUM**: Optimize bytes concatenation in _recv_exact (Issue #5)
5. **LOW**: Profile command serialization usage, cache if needed (Issue #3)
6. **LOW**: Use incremental IDs instead of random (Issue #6)
7. **LOW**: Use proper logging module (Issue #7)

---

## Benchmarking Recommendations

To validate these findings, benchmark:

1. **Audit log loading** with 10K, 100K, 1M entries
2. **Theme switching** time with 100+ widgets
3. **Command serialization** in tight loop (1000 iterations)
4. **Packet reception** with various sizes (1KB, 10KB, 100KB)

---

## Conclusion

The codebase is generally well-optimized with good use of modern Python features and performance libraries (orjson, uvloop). The critical issue is the audit log memory consumption, which needs immediate attention. Other issues are minor and can be addressed incrementally.

**Overall Performance Grade:** B+ (would be A- after fixing Issue #1)
