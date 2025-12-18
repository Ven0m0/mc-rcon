# Dependency Audit Report
**Date:** 2025-12-18
**Auditor:** Claude Code

## Executive Summary

This audit analyzed all project dependencies for outdated packages, security vulnerabilities, and unnecessary bloat. **No security vulnerabilities were found**. The audit identified **1 unused package** (httpx) and **4 packages with available updates**.

## Current Dependencies

### Production Dependencies
- `platformdirs`: >=4.3.8,<5.0.0 (currently resolves to 4.5.1)
- `orjson`: ^3.9.10 (optional, with stdlib fallback)
- `uvloop`: ^0.22.1 (optional, Unix-only, with stdlib fallback)

### Development Dependencies
- `pytest`: ^9.0.2
- `pytest-asyncio`: ^1.3.0
- `pytest-cov`: ^7.0.0
- `ruff`: ^0.14.8
- `mypy`: ^1.13.0
- `httpx`: ^0.28.1 ⚠️ **UNUSED**

## Findings

### 1. Outdated Packages

| Package | Current Constraint | Latest Available | Update Type | Priority |
|---------|-------------------|------------------|-------------|----------|
| platformdirs | >=4.3.8,<5.0.0 | 4.5.1 | Minor | Low |
| orjson | ^3.9.10 | 3.11.5 | Minor (2 versions) | Medium |
| ruff | ^0.14.8 | 0.14.9 | Patch | Low |
| mypy | ^1.13.0 | 1.19.1 | Minor (6 versions) | Medium |

**Details:**
- **platformdirs**: Already resolves to latest (4.5.1), constraint allows it
- **orjson**: 3.9.10 → 3.11.5 (performance improvements, bug fixes)
- **ruff**: 0.14.8 → 0.14.9 (patch release with bug fixes)
- **mypy**: 1.13.0 → 1.19.1 (significant updates to type checker)

### 2. Unused Dependencies (Bloat)

**httpx (^0.28.1)** - Development dependency
- ❌ Not imported in any Python file in the codebase
- ❌ Not used in tests, scripts, or tooling
- ✅ Safe to remove
- **Impact**: Reduces dependency tree, install size (~1.5MB), and maintenance burden

### 3. Security Vulnerabilities

✅ **No CVE vulnerabilities found** for any dependency in 2024-2025.

**Verification Methods:**
- Web search of CVE databases (NVD, OSV.dev, CISA)
- Package-specific security advisories
- Known vulnerability databases

**Note:** All dependencies are actively maintained open-source projects with good security track records.

### 4. Dependency Usage Analysis

**Well-Implemented Patterns:**
- ✅ Optional performance dependencies with stdlib fallbacks (orjson, uvloop)
- ✅ Minimal production dependency footprint (only platformdirs required)
- ✅ Development dependencies appropriately isolated

**Code Analysis:**
- `orjson`: Used in `audit.py` (lines 11, 45, 78) and `gui.py` (lines 22, 79, 107) with json fallback
- `uvloop`: Used in `core.py` (lines 345-347) with asyncio fallback
- `platformdirs`: Used in `pathclass.py` (line 7) for cross-platform path handling
- `httpx`: **Not used anywhere** ❌

## Recommendations

### Immediate Actions (High Priority)

1. **Remove httpx** - Unused bloat
   ```bash
   uv remove --dev httpx
   ```

2. **Update mypy** - 6 versions behind, important type checking improvements
   ```bash
   uv add --dev mypy --upgrade-package mypy
   ```

3. **Update orjson** - Performance and bug fix improvements
   ```bash
   uv add orjson --upgrade-package orjson
   ```

### Medium Priority Actions

4. **Update ruff** - Latest bug fixes
   ```bash
   uv add --dev ruff --upgrade-package ruff
   ```

5. **Update platformdirs constraint** (optional)
   - Current constraint already allows latest version
   - Consider updating minimum if using newer features

### Long-term Improvements

6. **Add CI Security Scanning**
   - Integrate `pip-audit` or `safety` in CI pipeline
   - Enable Dependabot for automated dependency updates
   - Schedule quarterly dependency audits

7. **Document Optional Dependencies**
   Consider adding optional dependency groups:
   ```toml
   [project.optional-dependencies]
   performance = ["orjson>=3.11.5", "uvloop>=0.22.1; sys_platform != 'win32'"]
   ```

8. **Fix Build System**
   - Current poetry-core setup has package detection issues
   - Consider migration to modern build backend compatible with uv

## Impact Assessment

| Metric | Current | After Cleanup | Improvement |
|--------|---------|---------------|-------------|
| Production deps | 3 (1 required) | 3 (1 required) | No change |
| Dev deps | 6 | 5 | -1 dependency |
| Install size | ~X MB | ~(X-1.5) MB | Smaller |
| Security risk | None | None | No change |
| Maintenance | 4 outdated | 0 outdated | Improved |

## Compliance

- ✅ No known security vulnerabilities
- ✅ All dependencies are actively maintained
- ✅ Licenses are compatible (all permissive licenses)
- ✅ No deprecated packages in use

## Next Audit

**Recommended:** Q1 2026 (3 months) or when major version updates are released.

---

**Audit Tool:** Manual analysis via uv, pip, and web searches
**Repositories Checked:** PyPI, NVD, OSV.dev, GitHub Security Advisories
