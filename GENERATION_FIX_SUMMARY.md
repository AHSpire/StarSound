# Generate Mod - Folder Structure Fix

## Problem
When clicking "Generate Mod" button, the created mod folder was almost empty (missing folders and `_metadata` file).

**Expected:** Mod folder should contain:
```
mod_name/
├── _metadata (JSON with mod metadata)
├── biomes/
│   ├── surface/
│   ├── underground/
│   └── space/
├── music/
├── music_replacers/
├── music_add_and_replace/
└── outputs/
```

**Actual (Before Fix):** Folder was mostly empty, missing `_metadata` and required subdirectories.

---

## Root Cause
The `PatchGenerationWorker._do_generation()` method in `starsound_gui.py` was calling `generate_patch()` to create patch files, but **never calling `create_mod_folder_structure()`** from `atomicwriter.py`.

Without this call:
- ❌ No `_metadata` file created  
- ❌ No base folder structure (`biomes/surface`, `biomes/underground`, etc.)
- ✅ Patch files were created (because `generate_patch()` handles this)
- ✅ Audio files were copied (because `generate_patch()` handles this)

---

## Solution
Added a call to `create_mod_folder_structure()` in the patch generation workflow.

### Code Change
**File:** `pygui/starsound_gui.py`  
**Location:** `PatchGenerationWorker._do_generation()` method (line 7314+)

**Before:**
```python
def _do_generation(self):
    try:
        import shutil
        from utils.patch_generator import generate_patch  # ❌ Missing import
        
        # ... setup code ...
        mod_path = staging_dir / safe_mod_name
        
        # ❌ NO CALL TO create_mod_folder_structure()
        
        # Clear old biomes folder...
```

**After:**
```python
def _do_generation(self):
    try:
        import shutil
        from utils.patch_generator import generate_patch
        from utils.atomicwriter import create_mod_folder_structure  # ✅ Added import
        
        # ... setup code ...
        mod_path = staging_dir / safe_mod_name
        
        # ✅ CREATE MOD FOLDER STRUCTURE WITH _metadata
        self.progress_update.emit('📁 Creating mod folder structure...')
        create_mod_folder_structure(staging_dir, safe_mod_name)
        self.main_window.logger.log(f'Created mod folder structure for: {safe_mod_name}', context='PatchGen')
        
        # Clear old biomes folder...
```

---

## What Gets Created
When `create_mod_folder_structure(staging_dir, safe_mod_name)` is called, it:

1. **Creates base folder:** `staging/{mod_name}/`
2. **Creates subdirectories:**
   - `biomes/surface/`
   - `biomes/underground/`
   - `biomes/space/`
   - `music/`
   - `music_replacers/`
   - `music_add_and_replace/`
   - `outputs/`

3. **Generates `_metadata` JSON file** with:
   - `name` - Internal name (spaces → underscores)
   - `friendlyName` - Display name
   - `author` - "StarSound User"
   - `description` - Editable description
   - `version` - "1.0.0"
   - `priority` - 9999

---

## Workflow After Fix
1. User clicks "Generate Mod" button
2. `PatchGenerationWorker._do_generation()` is called
3. **NEW:** `create_mod_folder_structure()` creates base structure + `_metadata` ✅
4. `generate_patch()` is called for each biome (creates patches + copies audio)
5. Mod folder is now **complete** with all required files

---

## Testing
Created `test_mod_generation_fix.py` to verify `create_mod_folder_structure()` works:

```
✅ Mod folder exists
✅ biomes/surface exists  
✅ biomes/underground exists
✅ biomes/space exists
✅ music exists
✅ music_replacers exists
✅ music_add_and_replace exists
✅ outputs exists
✅ _metadata file exists
✅ _metadata JSON parses correctly
```

---

## Verification
- ✅ `starsound_gui.py` compiles without syntax errors
- ✅ `create_mod_folder_structure()` function works correctly
- ✅ All imports are properly resolved
- ✅ Function is called at the right time in the workflow

---

## Impact
This fix ensures that when users click "Generate Mod", the resulting folder in `staging/` will have:
- ✅ Proper folder structure
- ✅ Required `_metadata` file (so Starbound recognizes it as a valid mod)
- ✅ All subdirectories needed for patch files and audio
- ✅ Complete, functional mod ready to export

The mod will no longer appear "almost empty" and will be installable in Starbound.
