# 🎵 StarSound

A lightweight, Python-based music mod generator for Starbound. Easily add custom music to your Starbound experience without the headache!

---

## 🎯 What is StarSound?

StarSound simplifies the process of adding music to Starbound. Instead of manually crafting JSON patches and managing file structures, you provide your music files and let StarSound handle the rest.

**Built for stability and ease of use** — no external dependencies beyond Python's standard library and FFmpeg.

---

## 📊 Project Status

| Item | Status |
|------|--------|
| **Current Version** | v0.1.0 (Pre-Release) |
| **Last Updated** | February 2026 |
| **Development Phase** | Active Development |
| **Platforms** | ✅ Windows • ✅ Linux/Steam Deck • ✅ macOS |

There were earlier versions, including the original that was based on Electron, but moving to Python ultimately proved to be the best decision.

### Platform Support Details

**All Platforms:**
- ✅ Music file format conversion (MP3, FLAC, WAV → OGG)
- ✅ Audio processing (bitrate, compression, EQ, fades)
- ✅ Loose file mod export (full-featured)
- ✅ Complete biome library (85+)
- ✅ Track splitting for long files (>30 min)

**Windows:**
- ✅ Automatic Starbound installation detection
- ✅ PAK file export (uses native `asset_packer.exe`)

**Linux/Steam Deck:**
- ✅ Automatic Starbound installation detection (including Flatpak)
- ✅ Proton/Wine compatibility for Starbound
- ✅ Loose file export (recommended)
- ℹ️ PAK export not available (but not needed—loose files work great!)

**macOS:**
- ✅ Automatic Starbound installation detection (via Steam)
- ✅ Loose file export (full-featured)
- ⚠️ PAK export not available (Starbound doesn't ship `asset_packer.exe` for macOS—use loose files instead)

---

### 🎵 Three Music Patching Modes (Choose What Works Best)

**🔒 Add Mode** ⭐ **— The Safest & Most Compatible Option** (Recommended for multi-mod setups)
  - Layer custom music on top of vanilla tracks
  - **100% compatible with ANY other music mod** (ADD operations never conflict)
  - Perfect for players using multiple music mods
  - Mix vanilla + custom music (~40-60% custom depending on file count)
  - Guaranteed to work with other players' music mods

**⚡ Remove Mode** — The Fastest & Simplest Option (Recommended for single-mod users)
  - Automatic vanilla track removal + custom music replacement
  - Simplest workflow, fastest setup (~1 minute)
  - ONLY your music plays in selected biomes (100% guaranteed)
  - Perfect for first-time users & complete theme replacements
  - ⚠️ *Can conflict with other REPLACE-based music mods (rare)—use Add Mode if that's a concern*

- **Replace Mode** — Manually swap specific vanilla tracks (for advanced users)
- **Both Mode** — Replace vanilla + add custom music (for complex scenarios)

### 🔊 Robust Audio Processing
- Multi-format support
- Bitrate control
- Audio compression with presets
- EQ adjustments
- Normalization & fade effects
- Real-time preview of audio while editing

### 🗺️ Comprehensive Biome Coverage
- **85+ biomes** supported including:
  - Core biomes, space biomes, surface biomes
  - Surface & underground detached biomes (Alpine, Oasis, Swamp, Bonecaves, Tarpit, etc.)

### 📏 Track Splitting for Long Files
- Automatic detection of files >30 minutes
- Configurable segment length (5–30 minutes)
- FFmpeg lossless WAV intermediates
- Split preview before processing
- Prevents empty segments (floating-point safe)

### 📦 Flexible Mod Export
- Export as **PAK files** (standard mod format)
- Export as **loose files** (for mod developers)
- Automatic metadata generation
- Proper mod folder structure

### 💻 User Experience
- Intuitive 6-step workflow
- Real-time audio validation
- Comprehensive error handling & logging
- Auto-save progress, save/load at any time
- Cross-platform support (Windows, Linux, macOS)

---

## 🚀 Getting Started

### Requirements
- **Python 3.10+**
- **FFmpeg** (for audio conversion)
- **Audio files** (MP3, FLAC, WAV, or OGG)
- **Starbound installation** folder path

### Installation

1. Clone or download this repository
2. Ensure Python 3.10+ and FFmpeg are installed
3. Run the application:
   ```bash
   starsound_gui.py
   ```
4. Follow the 6-step workflow in the GUI

### Quick Workflow

1. **Name your Mod** - Name your mod
2. **Set Mod Folder** - Determine mod output directory
3. **Pick Your Music** — Select audio files
4. **Convert To OGG** — Set bitrate, compression, EQ, etc if desired
5. **Select Patch Mode** — Choose Add, Replace, or Both
6. **Generate Mod** — Decide wether you'd like your mod as a .pak file or loose

---

## ⚠️ Important Limitations & Warnings

### World Baking (Native Starbound Behavior)
Music tracklists are baked into world files when they're first generated. This means:
- ✅ **New worlds** will hear your custom music
- ❌ **Existing worlds** will continue playing vanilla music
- 💡 **Workaround:** Use the in-game tool Terraformer to regenerate affected biomes

### Split Track Playback
When files are auto-split (>30 minutes), Starbound randomizes all tracks:
- 🎲 **Cannot guarantee sequential playback**
- 💡 **Recommendation:** Use "Add Mode" for guaranteed compatibility with other mods, or "Replace/Both Mode" for predictable biome ownership 

### ⚠️ CRITICAL: Silent Biome Risk (Replace/Both/Remove Modes)

**Replace, Both, and Remove modes all use REPLACE operations**, which can cause silent biomes if the mod is removed.

**If you disable/remove a mod using REPLACE operations:**
- ❌ Affected biomes will have **NO MUSIC** (vanilla fallback fails)
- 🔴 **Permanent data loss** — world data is baked, patches can't retroactively fix it
- ✅ **Solution:** Keep the mod installed indefinitely, OR
- ✅ **Better Solution:** Use **Add Mode** (vanilla fallback always available, never causes silent biomes)

**You should use Replace/Both/Remove modes ONLY if:**
- You plan to keep the mod installed indefinitely, OR
- You're okay with potential silent biomes if something goes wrong

**Add Mode advantages:**
- ✅ Vanilla music always plays as fallback (safe!)
- ✅ 100% compatible with any other music mod
- ✅ No silent biome risk
- ✅ Simplest to remove (just delete the mod folder)

---

## 📁 Project Structure

```
StarSound/
├── README.md                   # This file
├── starsound_gui.py            # Entry point
├── OpenPythonGUI.bat           # Quick launcher (Windows)
├── atomicwriter.py             # file management
├── patch_generator.py          # generates patches
└── ...                         # Additional utilities
```

## 📝 Documentation & Guides

For detailed information, see:

**Feature Documentation:**
- [ROADMAP.md](./ROADMAP.md) — Full development roadmap and feature status
- [BOTH_MODE_IMPLEMENTATION.md](./docs/architecture/BOTH_MODE_IMPLEMENTATION.md) — How Both Mode works (replace + add combination)
- [TRACK_SPLITTING_WORKFLOW.md](./docs/guides/TRACK_SPLITTING_WORKFLOW.md) — How track splitting works
- [SAVE_ARCHITECTURE.md](./docs/architecture/SAVE_ARCHITECTURE.md) — State persistence system
- [PER_TRACK_AUDIO_CONFIG_GUIDE.md](./docs/guides/PER_TRACK_AUDIO_CONFIG_GUIDE.md) — Audio processing details

## 🗺️ What's Coming

- 📻 **Radio Message Triggers** — "🎵 Now Playing" notifications when landing on planets
- 🎨 **Enhanced UI** — Dark mode, themes, keyboard shortcuts
- 🎵 **Ambient & Combat Music** — Add/replace ambient and boss battle tracks
- 💾 **Quality of Life** — Batch mod generation, import/export templates, mod compatibility checker
- 🧩 **Mod Compatibility Validator** — Auto-detect conflicts from other music mods and suggests resolutions or provide patches

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **StarSound can't be found** | Use the Browse button to manually specify your Starbound install folder |
| **Audio conversion fails** | Ensure FFmpeg is installed and in your system PATH. Test with `ffmpeg -version` in terminal |
| **My music file is too large** | Enable track splitting (automatic for files >30 min, or manual for large audio) |
| **Existing worlds don't hear new music** | Music is baked at world creation. Create a new world or use Terraformer to 'refresh' biome|
| **Split tracks play out of order** | This is Starbound's default behavior. Use Replace or Both mode instead of Add for more predictable playback |
| **GUI won't start** | Ensure Python 3.10+ is installed. Try `python --version` to verify |

---

## ❓ FAQ

**Q: What's the difference between Add, Replace, and Both modes?**  
A: **Add Mode** layers your music on top of vanilla (more variety). **Replace Mode** swaps all vanilla music with your own(full control). **Both Mode** replaces vanilla tracks AND adds yours on top!

**Q: Can I use MP3 or WAV files?**  
A: Yes! StarSound auto-converts MP3, MP4, FLAC, WAV, and other common formats to optimized OGG Vorbis for Starbound.

**Q: What happens if my music file is longer than 30 minutes?**  
A: StarSound automatically detects and splits it into segments (5–30 min each). You can preview the split before processing.

**Q: Can I add my 3hrs+ long tracks?**
A: Yes but splitting is highly advised as Starbound will- not play the track, play vanilla music instead, hang, crash, or all of the above.

**Q: Will existing worlds hear my custom music?**  
A: No—music is baked into worlds/planets at generation. Create a new world/planet or use in-game Terraformer machine to 'refresh' biomes.

**Q: Can I use StarSound with other music mods?**  
A: **Yes!** It depends on the mode:
- ✅ **Add Mode**: 100% compatible with ANY other music mod (ADD operations never conflict)
- ⚠️ **Remove/Replace/Both Mode**: Can conflict with other REPLACE-based mods (rare)
- 💡 **Recommendation**: Use Add Mode if you want to stack multiple music mods safely.

**Q: Is StarSound safe to use?**  
A: StarSound never modifies your original Starbound files. All changes are isolated to the mod folder. You can revert changes at any time.

**Q: What happens if I remove the mod later?**  
A: 
- ✅ **Add Mode**: Reverts to vanilla music (safe, always works)
- ⚠️ **Replace Mode**: Affected biomes have SILENT tracks (replaced indices become empty)
- ⚠️ **Remove Mode**: Affected biomes have SILENT tracks (vanilla removal is permanent without mod)
- ⚠️ **Both Mode**: Affected biomes have SILENT tracks (combines Replace + Remove issues)
- 💡 **Recommendation**: Use Add Mode for safety and flexibility. Keep other modes installed permanently.

**Q: Can I export my generated mod for distribution?**  
A: Yes! Create music overhauls with ease and share to your heart's content.

**Q: Can I customize how fast music transitions between biomes?**  
A: Yes! Edit your Starbound installation's `interface.config` file. Look for these settings:
- `musicTrackSwitchGrace` (default 3.0 seconds) — Wait time before switching music
- `musicTrackFadeInTime` (default 0.5 seconds) — How long fade-in takes
- `ambientTrackSwitchGrace` (default 1.0 seconds) — Wait time for ambient sounds
- `ambientTrackFadeInTime` (default 0.5 seconds) — How long ambient fade-in takes

Lower values = faster transitions, higher values = slower/smoother transitions. This is an advanced feature for power users!

---

## 📜 Credits & Partnership

This project is a collaboration between human and artificial intelligence.

| Role | Contributors |
|------|--------------|
| **Lead Architect & Auditor** | AHSpire |
| **Code & Implementation** | GitHub Copilot Claude, Google's Gemini |

### Philosophy

StarSound was built using a **"Partner" model**. While AI provided the vast majority of logic and implementation, human oversight ensured architecture quality, creative direction, and rigorous testing for a program everyone can enjoy.

---

## ⚖️ License

This work is dedicated to the **public domain** under the [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) license.

We believe that universal truths found in code should be shared, not hidden.

---

## 🤝 Contributing

StarSound welcomes contributions! Whether bug reports, feature requests, or code improvements, your feedback helps make this tool better.

---

**Made with ❤️ for the Starbound community**
