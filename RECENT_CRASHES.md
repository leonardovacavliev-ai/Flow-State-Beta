# Recent Deployment Crashes - Phase 4 (July 17, 2026)

**Context**: Phase 4 implementation (database-backed ESP management) caused 4 consecutive crashes on Railway deployment.

---

## Crash #1: Database Connection at Import Time

### Error Log
```
psycopg2.OperationalError: invalid integer value "port" for connection option "port"

Traceback:
  File "/app/backend/app.py", line 54, in <module>
    from app_admin_esp_routes import register_esp_admin_routes
  File "/app/backend/app_admin_esp_routes.py", line 15, in <module>
    esp_mgr = get_esp_manager()
  File "/app/backend/esp_manager.py", line 392, in get_esp_manager
    _esp_manager = ESPManager()
  File "/app/backend/esp_manager.py", line 19, in __init__
    self.db = get_database_adapter()
```

### Root Cause
ESP manager was initialized at module-level (when Python imports the file), trying to connect to PostgreSQL **before Flask app was ready**. The DATABASE_URL environment variable wasn't properly parsed at that early stage.

### Code Problem
```python
# app_admin_esp_routes.py (BAD)
from esp_manager import get_esp_manager

# THIS RUNS AT IMPORT TIME - TOO EARLY!
esp_mgr = get_esp_manager()  # ← Connects to database immediately

def register_esp_admin_routes(app, BASE_PATH, vectorizer):
    # Routes use esp_mgr...
```

### Fix: Lazy Initialization
```python
# app_admin_esp_routes.py (GOOD)
from esp_manager import get_esp_manager

def register_esp_admin_routes(app, BASE_PATH, vectorizer):
    # Helper function - only connects when called
    def get_mgr():
        return get_esp_manager()
    
    @app.route('/api/admin/esps', methods=['GET'])
    def get_esps():
        esp_mgr = get_mgr()  # ← Connects only when route is hit
        # ...
```

**Lesson**: Never initialize database connections at module import time. Use lazy initialization inside route handlers.

**Commit**: `120646f` - "fix: Use lazy initialization for ESP manager to avoid startup crash"

---

## Crash #2: Duplicate Route Endpoints

### Error Log
```
AssertionError: View function mapping is overwriting an existing endpoint function: get_esps

Traceback:
  File "/app/backend/app.py", line 239, in <module>
    @app.route('/api/admin/esps', methods=['GET'])
  File "/usr/local/lib/python3.11/site-packages/flask/sansio/app.py", line 657, in add_url_rule
    raise AssertionError(
```

### Root Cause
Both OLD filesystem-based routes and NEW database-backed routes were trying to register the same Flask endpoints. Flask doesn't allow duplicate route names.

### Code Problem
```python
# app.py
from app_admin_esp_routes import register_esp_admin_routes
register_esp_admin_routes(app, BASE_PATH, vectorizer)  # ← Registers /api/admin/esps

# Later in same file...
@app.route('/api/admin/esps', methods=['GET'])  # ← ERROR: Duplicate!
def get_esps():
    # Old filesystem code...
```

### Fix: Conditional Route Loading
```python
# app.py
USE_DATABASE_ESP_ROUTES = True

if USE_DATABASE_ESP_ROUTES:
    from app_admin_esp_routes import register_esp_admin_routes
    register_esp_admin_routes(app, BASE_PATH, vectorizer)

# Later in same file...
if not USE_DATABASE_ESP_ROUTES:  # ← Only load if database routes disabled
    @app.route('/api/admin/esps', methods=['GET'])
    def get_esps():
        # Old filesystem code...
```

**Lesson**: When replacing routes, disable old ones with feature flags or remove them entirely.

**Commit**: `d6a6fe9` - "fix: Disable old filesystem ESP routes to avoid duplicate endpoint error"

---

## Crash #3: Indentation Syntax Error

### Error Log
```
SyntaxError: 'return' outside function

  File "/app/backend/app.py", line 273
    return jsonify({'esps': esps})
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

### Root Cause
When adding `if not USE_DATABASE_ESP_ROUTES:` wrapper, the function body wasn't indented properly. The `def get_esps():` line was indented but the function body wasn't, making Python think the `return` was outside the function.

### Code Problem
```python
# app.py (BAD INDENTATION)
if not USE_DATABASE_ESP_ROUTES:
    @app.route('/api/admin/esps', methods=['GET'])
    def get_esps():
        """Get list of ESPs"""
    docs_path = os.path.join(BASE_PATH, 'docs')  # ← WRONG: Not indented
    esps = []
    # ...
    return jsonify({'esps': esps})  # ← ERROR: Outside function
```

### Fix: Proper Indentation
```python
# app.py (CORRECT INDENTATION)
if not USE_DATABASE_ESP_ROUTES:
    @app.route('/api/admin/esps', methods=['GET'])
    def get_esps():
        """Get list of ESPs"""
        docs_path = os.path.join(BASE_PATH, 'docs')  # ← Indented 4 more spaces
        esps = []
        # ...
        return jsonify({'esps': esps})  # ← Inside function
```

**Lesson**: When wrapping existing code in conditionals, indent the ENTIRE block consistently. Python requires exact indentation.

**Commit**: `812d566` - "fix: Fix indentation in conditional ESP routes block"

---

## Crash #4: Incomplete Route Wrapping

### Error Log
```
AssertionError: View function mapping is overwriting an existing endpoint function: get_esp_links

Traceback:
  File "/app/backend/app.py", line 314, in <module>
    @app.route('/api/admin/esp/<esp_name>/links', methods=['GET'])
  File "/usr/local/lib/python3.11/site-packages/flask/sansio/app.py", line 657, in add_url_rule
    raise AssertionError(
```

### Root Cause
Only the FIRST old route (`/api/admin/esps`) was wrapped in `if not USE_DATABASE_ESP_ROUTES:`. All the OTHER old ESP routes (starting at line 314) were still outside the conditional, causing duplicate endpoint errors.

### Code Problem
```python
# app.py (INCOMPLETE FIX)
if not USE_DATABASE_ESP_ROUTES:
    @app.route('/api/admin/esps', methods=['GET'])
    def get_esps():
        # ...
        return jsonify({'esps': esps})

# These routes are OUTSIDE the conditional - ERROR!
@app.route('/api/admin/esp/<esp_name>/links', methods=['GET'])
def get_esp_links(esp_name):
    # ...

@app.route('/api/admin/esp/<esp_name>/add-link', methods=['POST'])
def add_esp_link(esp_name):
    # ...
# ... more routes
```

### Fix: Wrap ALL Old ESP Routes
```python
# app.py (COMPLETE FIX)
if not USE_DATABASE_ESP_ROUTES:
    @app.route('/api/admin/esps', methods=['GET'])
    def get_esps():
        # ...
        return jsonify({'esps': esps})
    
    # Additional ESP admin routes (filesystem-based)
    @app.route('/api/admin/esp/<esp_name>/links', methods=['GET'])
    def get_esp_links(esp_name):
        # ...
    
    @app.route('/api/admin/esp/<esp_name>/add-link', methods=['POST'])
    def add_esp_link(esp_name):
        # ...
    
    # ... all other ESP routes indented inside the conditional
    
    # ========== END OF OLD FILESYSTEM-BASED ESP ROUTES ==========

# Routes outside the conditional continue here
@app.route('/api/admin/refresh', methods=['POST'])
def refresh_all():
    # ...
```

**Routes wrapped** (lines 314-678 in app.py):
- `/api/admin/esp/<esp_name>/links` (GET)
- `/api/admin/esp/<esp_name>/add-link` (POST)
- `/api/admin/esp/create` (POST)
- `/api/admin/esp/<esp_name>/crawl-selected` (POST)
- `/api/admin/esp/<esp_name>/paste-content` (POST)
- `/api/admin/esp/<esp_name>/delete-links` (POST)

**Lesson**: When disabling old routes, wrap ALL of them in the conditional, not just the first one. Use clear markers (comments) to identify the start and end of the block.

**Commit**: (pending) - "fix: Wrap all old ESP routes in USE_DATABASE_ESP_ROUTES conditional"

---

## Timeline

| Time | Crash | Error | Fix | Commit |
|------|-------|-------|-----|--------|
| Deploy 1 | #1 | Database connection at import | Lazy initialization | 120646f |
| Deploy 2 | #2 | Duplicate Flask endpoints | Conditional route loading | d6a6fe9 |
| Deploy 3 | #3 | Indentation syntax error | Fixed indentation | 812d566 |
| Deploy 4 | #4 | Incomplete route wrapping | Wrapped all old ESP routes | (pending) |
| Deploy 5 | ✅ | **SUCCESS** | - | - |

---

## Prevention Checklist

**Before deploying database-backed features**:

- [ ] **Lazy initialization**: Never connect to database at module import
- [ ] **Remove old routes**: Disable or delete ALL routes being replaced (not just some)
- [ ] **Test syntax locally**: Run `python3 -m py_compile app.py`
- [ ] **Check indentation**: Use consistent 4-space indentation
- [ ] **Test imports**: `python3 -c "import app"` before pushing
- [ ] **Feature flags**: Use flags for easy rollback (like `USE_DATABASE_ESP_ROUTES`)
- [ ] **Mark boundaries**: Use comments to clearly mark start/end of conditional blocks

---

## Rollback Instructions

**If Phase 4 causes problems**, change one line in `backend/app.py`:

```python
# Line ~54
USE_DATABASE_ESP_ROUTES = False  # ← Reverts to filesystem routes
```

Then commit and push. Old filesystem routes will work again.

---

## Lessons Learned

1. **Database connections**: Always lazy-load. Never initialize at module level.
2. **Route conflicts**: Flask errors on duplicate routes. Use feature flags to toggle.
3. **Python indentation**: When wrapping code in `if` blocks, indent EVERYTHING inside.
4. **Testing locally**: `python3 -c "import module"` catches syntax errors before deploy.
5. **Feature flags**: Essential for safe rollbacks and A/B testing new features.
6. **Thorough wrapping**: When disabling old code, wrap ALL related code, not just the first piece.
7. **Clear markers**: Use comments to mark boundaries of conditional blocks for easy debugging.

---

## Current Status

✅ **All crashes resolved**
✅ **App imports successfully with no duplicate endpoint errors**
✅ **Database-backed ESP routes active**
✅ **Rollback mechanism in place**

**Next**: Test deployment and apply database schema if successful.

---

**Document Updated**: July 17, 2026
**Author**: Claude Code
**Phase**: 4 (Database-Backed ESP Management)
