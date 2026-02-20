# StarSound Roadmap 🎵

**A lightweight Python-based music mod generator for Starbound**

---

## 📊 Project Status

**Current Phase:** v0.1.0 Pre-Release 
**Last Updated:** February 2026  
**Repository:** StarSound (Python/PyQt5)

---

## ✅ v0.1.0 - Complete Features (RELEASED)

### Core Music Replacement
- ✅ Add custom music to any Starbound biome (Add mode)
- ✅ Replace all vanilla music cleanly (Replace mode)
- ✅ Combine both operations (Both mode)
- ✅ **NEW: Remove vanilla tracks** - Total biome replacement via JSON Patch remove/add operations
  - RFC 6902 compliant patch generation
  - Backwards-compatible remove operations
  - Direct index adds for predictable track order

### Track Splitting (30+ Minute Files)
- ✅ Automatic detection of files >30 minutes
- ✅ User-configurable segment length (5-30 min)
- ✅ FFmpeg lossless WAV intermediates
- ✅ Split preview showing segment breakdown
- ✅ Automatic temporary file cleanup
- ✅ All audio effects applied uniformly to segments
- ✅ Prevents empty segments (floating-point safety)

### Audio Processing
- ✅ Format conversion (MP3, FLAC, WAV → OGG Vorbis)
- ✅ Bitrate control (64-320 kbps)
- ✅ Audio compression with presets
- ✅ EQ adjustments (low/mid/high)
- ✅ Normalization & fade effects
- ✅ Real-time preview of settings

### Biome Coverage
- ✅ **85+ biomes** including:
  - Core biomes (5)
  - Space biomes (3)
  - Surface biomes (24)
  - **Surface detached biomes (18)** - NEW: Alpine, Oasis, Spring, Swamp, etc.
  - Underground biomes (19)
  - **Underground detached biomes (11)** - NEW: Bonecaves, Tarpit, Wilderness, etc.

### User Experience
- ✅ Intuitive 6-step workflow
- ✅ Real-time audio validation
- ✅ Visual feedback on track status
- ✅ Comprehensive error handling
- ✅ Full logging system (debug & errors)
- ✅ Auto-save mod state
- ✅ Export as PAK or loose files
- ✅ Critical user warnings (world generation caveat, Terraformer option)

### Mod Packaging
- ✅ Automatic mod folder structure
- ✅ Metadata generation (_metadata file)
- ✅ PAK file creation
- ✅ Loose file export (for mod development)

---

## 🔄 v1.0 Current Phase - Testing & Polish

### In Progress
- bugtesting
- 🔧 Performance optimization
- 🔧 Converted Ogg size limit (<500MB target)
- 🔧 UI/UX refinement feedback
- 🔧 Documentation polish

### Known Limitations
- ⚠️ **World Baking:** Music tracklists are baked into world files at generation time
  - Custom music appears in new worlds only
  - Existing worlds need Terraformer or regeneration
  - This is a Starbound engine limitation, not a StarSound issue
- ⚠️ **Split Track Playback:** Starbound randomizes all tracks (can't guarantee sequential order)
  - Recommendation: Use Remove vanilla tracks + Add mode for predictable biome ownership
- ⚠️ **Removal Of Mod from Save - General Case:** Removing any Add/Replace mode music mod from your save will result in the save reverting to playing vanilla tracks.
- ⚠️ **CRITICAL: Removal Of Mod After Remove Mode - Permanent Data Loss:** If you use Remove mode and later remove/disable the StarSound mod, affected biomes will have NO music (vanilla fallback fails because vanilla tracks were permanently removed from the save). 
  - **Why no recovery?** World states are baked at generation time—patches cannot retroactively modify existing world data.
  - **The only solution:** Use Terraformer to regenerate affected biomes (exactly like any other music mod conflict).
  - **Recommendation:** Only use Remove mode if you plan to keep that mod installed indefinitely. For safer behavior, use Replace mode instead (overwrites vanilla but keeps fallback data intact).

---

## 📋 v1.0 - Planned Features

### Radio Message Trigger ⭐
- 📻 Automatic notification when players land on planet
- 📻 `"🎵 Now Playing: [Collection Name] by StarSound User"`
- 📻 Zero CPU overhead (uses native radioMessages system)
- 📻 Hooks into onTeleport/onWorldEnter events
- 📻 Generates automatic player.config.patch
- 📻 Non-intrusive, auto-dismissing messages

### Enhanced UI
- 🎨 Dark mode toggle
- 🎨 Theme customization
- 🎨 Keyboard shortcuts (more of them)
- 🎨 Mod Templates

### Additional Music/Sound Customization ###
- Ambient tracks
- Combat/Boss music

### Quality of Life
- 💾 Batch mod generation (multiple collections)
- 💾 Import/export templates
- 💾 **Mod Compatibility Checker (Re-added from legacy)** - Validate patches against installed mods, auto detect conflicts and offer tradeoff resolution
- 💾 Mod comparison tool
- 💾 Track preview improvements

---

## 🚀 Future Vision (v2.0+ - Exploratory)

### Advanced Features ⚠️ *Subject to Starbound Engine Capabilities*
- 🌟 **Playlist Randomization:** Control track play probability (feasible)
- 🌟 **Dynamic Theme Switching:** Apply coordinated day/night music collections with one click (likely)
- 🌟 **Contextual Music:** Weather/combat-based music switching (exploring feasibility)
- 🌟 **Ambient Mixing:** Blend music with location ambience (exploring feasibility)

### Community Features
- 👥 Music collection sharing (nexus integration)
- 👥 Community presets library
- 👥 Analytics dashboard (what's most popular)
- 👥 Extended mod validation (advanced compatibility scenarios)

### Technical Enhancements
- ⚙️ Multi-threaded conversion (faster batch processing)
- ⚙️ GPU acceleration for audio processing
- ⚙️ Cloud sync for mod collections
- ⚙️ Alternative audio codecs (Opus, etc.)

---

## 🐛 Known Issues & Workarounds

| Issue | Status | Workaround |
|-------|--------|-----------|
| Pre-existing worlds don't hear new music | Starbound Design | Create new world or use Terraformer |
| Split tracks play randomly | Starbound Design | Use "Remove vanilla" + Add mode for biome ownership |
| Large audio files take time to process | Expected | Unavoidable for now |
| Detached biomes have no vanilla data | Info Only | Users can add custom music freely |

---

## 📚 Documentation

- **[TRACK_SPLITTING_WORKFLOW.md](./TRACK_SPLITTING_WORKFLOW.md)** - How track splitting works
- **[BOTH_MODE_IMPLEMENTATION_PLAN.md](./BOTH_MODE_IMPLEMENTATION_PLAN.md)** - Replace + Add combination mode
- **[SAVE_ARCHITECTURE.md](./SAVE_ARCHITECTURE.md)** - State persistence system

---

## 🤝 How to Contribute

### Testing
- Create music mods and report issues!
- Test on mod-heavy setups!
- Document edge cases you find!
- Share feedback on UI/UX!

### Development
- Check existing GitHub issues
- Pick a v1.5 feature to implement
- Follow Python standards (PEP 8, type hints)
- Test thoroughly before submitting PR

### Community
- Share your StarSound creations
- Create tutorials & guides
- Help other users in discussions
- Suggest features based on real needs

---

## 📈 Version History

| Version | Release Date | Focus |
|---------|--------------|-------|
| v0.0.1 | Late Jan 2026 | Creation in Electron |
| v0.0.5 | Early Feb 2026 | Transfer/Rebuild in Python |
| v0.1.0 | Late Feb 2026 | Reliable functionality, track splitting, Remove vanilla tracks |
| v1.0 | TBD | Radio messages, enhanced UI, quality of life |
| v2.0 | TBD | Advanced features (randomization, themes, weather) |

---

## 🎯 Philosophy

**StarSound** is built for:
- **Stability** - No crashes, comprehensive error handling
- **Simplicity** - Intuitive workflows, minimal learning curve
- **Elegance** - Easy to understand code, zero CPU waste, RFC 6902 standards
- **Community** - Making Starbound even better with easy custom music for everyone

---

## 📞 Support

- 🐛 **Bug Reports:** GitHub Issues
- 💡 **Feature Requests:** GitHub Discussions
- 📖 **Documentation:** See Readme and [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md)
- 💬 **Community Chat:** Discord (TBD)

---

**Made with ❤️ for the Starbound community**
