# Dependency Audit Report

**Project:** mc-rcon
**Date:** 2025-12-27
**Auditor:** Claude Code

## Executive Summary

The mc-rcon project has a lean dependency footprint with **no security vulnerabilities** detected. Most dependencies are up-to-date, but there are several configuration inconsistencies and opportunities for improvement.

**Key Findings:**
- ✅ No security vulnerabilities found
- ✅ Minimal dependency bloat
- ⚠️  Configuration inconsistencies between PEP 621 and Poetry
- ⚠️  One slightly outdated package (ruff)
- ⚠️  Missing test infrastructure despite test dependencies

---

## Dependency Analysis

### Runtime Dependencies

| Package | Current | Latest | Status | Usage |
|---------|---------|--------|--------|-------|
| **platformdirs** | 4.5.1 | 4.5.1 | ✅ Up-to-date | Used in `pathclass.py` for cross-platform paths |
| **orjson** | 3.11.5 | 3.11.5 | ✅ Up-to-date | Optional optimization in `audit.py` (6x faster JSON) |
| **uvloop** | 0.22.1 | 0.22.1 | ✅ Up-to-date | Optional optimization in `core.py` (async I/O boost) |

### Development Dependencies

| Package | Current | Latest | Status | Necessity |
|---------|---------|--------|--------|-----------|
| **pytest** | 9.0.2 | 9.0.2 | ✅ Up-to-date | ⚠️ No tests directory exists |
| **pytest-asyncio** | 1.3.0 | 1.3.0 | ✅ Up-to-date | ⚠️ No async tests found |
| **pytest-cov** | 7.0.0 | 7.0.0 | ✅ Up-to-date | ⚠️ No tests to measure coverage |
| **ruff** | 0.14.9 | 0.14.10 | ⚠️ Outdated | Actively used for linting/formatting |
| **mypy** | 1.19.1 | 1.19.1 | ✅ Up-to-date | Type checking (strict mode) |

---

## Security Assessment

**Status:** ✅ PASS

```bash
$ pip-audit scan
No known vulnerabilities found
```

All dependencies have been scanned against the OSV vulnerability database. No CVEs or security advisories were found.

---

## Issues & Recommendations

### 🔴 Critical: Configuration Inconsistency

**Issue:** The `pyproject.toml` contains both PEP 621 `[project]` and Poetry `[tool.poetry]` dependency declarations, which are inconsistent and confusing.

**Current State:**
```toml
# PEP 621 style
[project]
dependencies = ["platformdirs (>=4.3.8,<5.0.0)"]

# Poetry style (different dependencies!)
[tool.poetry.dependencies]
orjson = "^3.11.5"
python = "^3.10"
uvloop = { version = "^0.22.1", markers = "sys_platform != 'win32'" }
```

**Impact:**
- `uv` reads `[project]` dependencies (only platformdirs)
- Poetry would read `[tool.poetry]` dependencies (orjson, uvloop, python)
- Mismatch causes installation issues depending on the tool used

**Recommendation:**
Choose one dependency specification standard. Since CLAUDE.md mandates using `uv` (not Poetry), migrate to PEP 621 format:

```toml
[project]
dependencies = [
    "platformdirs>=4.3.8,<5.0.0",
    "orjson>=3.11.5,<4.0.0",
]

[project.optional-dependencies]
# uvloop is optional (Unix-only performance optimization)
performance = ["uvloop>=0.22.1,<0.23.0; sys_platform != 'win32'"]

dev = [
    "pytest>=9.0.2",
    "pytest-asyncio>=1.3.0",
    "pytest-cov>=7.0.0",
    "ruff>=0.14.10",
    "mypy>=1.19.1",
]

[build-system]
requires = ["hatchling"]  # or "setuptools>=68"
build-backend = "hatchling.build"  # not poetry-core
```

### 🟡 Medium: Missing Test Infrastructure

**Issue:** The project has pytest dependencies configured but no `tests/` directory exists.

**Impact:**
- Cannot verify code correctness
- pytest-asyncio and pytest-cov dependencies are unused
- No CI/CD quality gates possible

**Recommendation:**
Either:
1. **Create tests** (recommended for production libraries):
   ```bash
   mkdir tests
   # Add test files for core functionality
   ```

2. **Remove test dependencies** if tests aren't planned:
   ```toml
   # Remove from dev dependencies
   # "pytest>=9.0.2",
   # "pytest-asyncio>=1.3.0",
   # "pytest-cov>=7.0.0",
   ```

### 🟡 Medium: Outdated Package

**Issue:** `ruff` is one minor version behind (0.14.9 vs 0.14.10)

**Recommendation:**
```bash
uv add --dev ruff --upgrade-package ruff
```

### 🟢 Low: Documentation Inconsistency

**Issue:** CLAUDE.md mentions using `pyrefly` for type checking, but `pyproject.toml` uses `mypy`.

**Files in conflict:**
- `CLAUDE.md:43-44` says "use pyrefly for type checking"
- `pyproject.toml:32` declares `mypy = "^1.19.1"`
- No `pyrefly` dependency exists

**Recommendation:**
Update CLAUDE.md to reflect actual tooling:
```diff
- use pyrefly for type checking
-   - run `pyrefly init` to start
-   - run `pyrefly check` after every change
+ use mypy for type checking
+   - run `uv run mypy --strict mcrconpy/` to check types
```

### 🟢 Low: Optional Dependencies Pattern

**Issue:** `orjson` and `uvloop` are listed as required dependencies but implemented as optional with fallbacks.

**Current Implementation:**
```python
# audit.py
try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False
    import json

# core.py
with suppress(ImportError):
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
```

**Recommendation:**
Make the dependency specification match the implementation by using optional dependencies:

```toml
[project]
dependencies = [
    "platformdirs>=4.3.8,<5.0.0",
]

[project.optional-dependencies]
# Performance optimizations (recommended but not required)
perf = [
    "orjson>=3.11.5,<4.0.0",
    "uvloop>=0.22.1,<0.23.0; sys_platform != 'win32'",
]
```

**Installation:**
```bash
# Minimal install
uv add mc-rcon

# Recommended install (with performance)
uv add mc-rcon[perf]
```

---

## Dependency Bloat Analysis

**Status:** ✅ LEAN

The project has minimal dependencies:
- **3 runtime dependencies** (1 required, 2 optional)
- **5 dev dependencies** (3 actually used: ruff, mypy + 2 unused: pytest stack)

**Bloat Score:** 0/10 (excellent)

### Transitive Dependencies Check

```bash
$ uv tree
mc-rcon v0.0.1
└── platformdirs v4.5.1
```

Only 1 transitive dependency. No deep dependency chains or supply-chain risk.

---

## Action Items

### Immediate (High Priority)

1. **Fix dependency configuration inconsistency**
   - [ ] Migrate from Poetry to PEP 621 format in `pyproject.toml`
   - [ ] Remove `[tool.poetry]` sections
   - [ ] Update `[build-system]` to non-Poetry backend
   - [ ] Test with `uv install` to verify

2. **Update ruff to latest**
   ```bash
   uv add --dev ruff --upgrade-package ruff
   ```

3. **Resolve test dependency issue**
   - [ ] Either create `tests/` directory with basic tests
   - [ ] OR remove pytest/pytest-asyncio/pytest-cov from dependencies

### Short-term (Medium Priority)

4. **Fix documentation inconsistency**
   - [ ] Update CLAUDE.md to reference `mypy` instead of `pyrefly`
   - [ ] Add actual type-checking commands to guidelines

5. **Clarify optional dependencies**
   - [ ] Document performance benefits of orjson/uvloop in README
   - [ ] Show both minimal and recommended installation methods

### Nice-to-have (Low Priority)

6. **Add dependency version constraints**
   - [ ] Consider adding upper bounds to dev dependencies
   - [ ] Document reasoning for version ranges

7. **Set up Dependabot**
   - [ ] Configure GitHub Dependabot for automated updates
   - [ ] Monitor for security vulnerabilities

---

## Comparison with CLAUDE.md Guidelines

| Guideline | Compliance | Notes |
|-----------|-----------|-------|
| Only use uv, never pip | ⚠️ Partial | Poetry still in build-system |
| Type hints required | ✅ Pass | mypy strict mode configured |
| Run pytest for tests | ⚠️ N/A | No tests exist |
| Use anyio for async testing | ❌ Fail | Uses pytest-asyncio instead |
| Use ruff for formatting | ✅ Pass | Configured correctly |
| Use pyrefly for type checking | ❌ Fail | Uses mypy instead |

**Recommendation:** Update either CLAUDE.md or the tooling to match. The current tools (mypy, pytest-asyncio) are more common than the documented ones (pyrefly, anyio).

---

## Conclusion

The mc-rcon project has **excellent dependency hygiene** with no security issues and minimal bloat. The main concern is the **configuration inconsistency** between PEP 621 and Poetry dependency declarations, which should be resolved to prevent installation issues.

### Overall Grade: B+

**Strengths:**
- No security vulnerabilities
- Minimal dependency footprint
- All packages up-to-date (except ruff)
- Smart use of optional dependencies with fallbacks

**Areas for Improvement:**
- Resolve PEP 621 vs Poetry configuration conflict
- Align documentation with actual tooling
- Either add tests or remove test dependencies
- Update ruff to latest version

### Recommended Next Steps

1. Create a new branch: `git checkout -b fix/dependency-configuration`
2. Migrate `pyproject.toml` to PEP 621 format (see recommendation above)
3. Update ruff: `uv add --dev ruff --upgrade-package ruff`
4. Update CLAUDE.md to match actual tooling
5. Decide on testing strategy (add tests vs remove dependencies)
6. Run `uv lock` to generate a lockfile
7. Test installation: `uv install` and `uv install --all-extras`
8. Commit and push changes

---

**End of Report**
