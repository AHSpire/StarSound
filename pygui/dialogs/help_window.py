"""
Help Dialog - Context-Sensitive Help System
============================================

Simple help dialog that displays help content in a scrollable text area.
Works properly with modal dialogs without window stacking issues.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class HelpWindow(QDialog):
    """Simple help dialog for displaying context-sensitive help."""
    
    def __init__(self, parent=None, initial_topic=None):
        """
        Initialize the Help Dialog.
        
        Args:
            parent: Parent widget
            initial_topic: Topic to display (e.g., 'step1', 'audio_processing')
        """
        super().__init__(parent)
        self.setWindowTitle('🛟 StarSound Help')
        self.setModal(True)  # Modal works better with parent modal dialogs
        
        # Explicitly remove help button behavior (Windows default on QDialog)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.setMinimumSize(700, 500)
        
        self.setStyleSheet('''
            QDialog {
                background-color: #1a1f2e;
            }
            QLabel {
                color: #e6ecff;
            }
            QTextEdit {
                background-color: #181c2a;
                color: #e6ecff;
                border: 1px solid #3a4a6a;
                border-radius: 4px;
                padding: 8px;
            }
        ''')
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title = QLabel('🛟 StarSound Help & Guide')
        title.setStyleSheet('color: #00d4ff; font-size: 14px; font-weight: bold;')
        main_layout.addWidget(title)
        
        # Content area
        self.content_area = QTextEdit()
        self.content_area.setReadOnly(True)
        main_layout.addWidget(self.content_area, 1)
        
        # Close button
        close_btn = QPushButton('✕ Close')
        close_btn.setMaximumWidth(100)
        close_btn.setStyleSheet('''
            QPushButton {
                background-color: #c41e3a;
                color: #e6ecff;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e63235;
            }
        ''')
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)
        
        # Display content for initial topic
        if initial_topic:
            content = self._get_topic_content(initial_topic)
            self.content_area.setHtml(content)
        else:
            self.content_area.setHtml(self._get_topic_content('intro'))
    
    def _get_topic_content(self, topic_id):
        """Get HTML content for a topic."""
        contents = {
            'intro': '''
                <h3 style="color: #00d4ff;">🎵 Welcome to StarSound</h3>
                <p>StarSound makes it easy to add custom music to Starbound. Follow these steps:</p>
                <ol>
                    <li><b>Step 1:</b> Name your mod (e.g., "MyMusicMod")</li>
                    <li><b>Step 2:</b> Choose where to save the mod folder</li>
                    <li><b>Step 3:</b> Select the audio files you want to add</li>
                    <li><b>Step 4:</b> Convert your files to OGG format</li>
                    <li><b>Step 5:</b> Choose how to patch the game (Add, Replace, or Both)</li>
                    <li><b>Step 6:</b> Choose when your tracks play (Day/Night/Both)</li>
                </ol>
                <p style="color: #888888; font-size: 11px; margin-top: 12px;">
                    <b>Tip:</b> Click the "?" button in any dialog to get help for that specific feature.
                </p>
            ''',
            
            'step1': '''
                <h3 style="color: #00d4ff;">Step 1: Set Your Mod Name</h3>
                <p><b>What is a mod name?</b> A unique identifier for your music mod.</p>
                <p><b>Requirements:</b></p>
                <ul>
                    <li>Letters, numbers, and underscores only</li>
                    <li>No spaces or special characters</li>
                    <li>Example: <code>MyMusicMod</code>, <code>epic_battle_theme</code></li>
                </ul>
                <p><b>Dice Button:</b> Click the 🎲 button to generate a random mod name.</p>
                <p style="color: #888888; font-size: 11px; margin-top: 12px;">
                    Your mod name appears in the mods folder and game mod list. Choose something memorable!
                </p>
            ''',
            
            'step2': '''
                <h3 style="color: #00d4ff;">Step 2: Choose Mod Folder</h3>
                <p><b>Where should the mod go?</b> Starbound's mods directory.</p>
                <p><b>Default location:</b></p>
                <code style="color: #6bffb0; display: block; margin: 8px 0; padding: 6px; background: #181c2a; border-left: 3px solid #6bffb0;">
                    C:\\Steam\\steamapps\\common\\Starbound\\mods
                </code>
                <p><b>Steps:</b></p>
                <ol>
                    <li>Click the "Browse" button</li>
                    <li>Navigate to your Starbound installation folder</li>
                    <li>Select the <code>mods</code> folder</li>
                    <li>Click "Select Folder"</li>
                </ol>
                <p style="color: #888888; font-size: 11px; margin-top: 12px;">
                    StarSound will create a folder here with your mod name from Step 1.
                </p>
            ''',
            
            'step3': '''
                <h3 style="color: #00d4ff;">Step 3: Select Audio Files</h3>
                <p><b>What files can you add?</b> MP3, WAV, FLAC, OGG, M4A, and more.</p>
                <p><b>Steps:</b></p>
                <ol>
                    <li>Click "Browse" to open the file picker</li>
                    <li>Select one or more audio files</li>
                    <li>Click "Open"</li>
                </ol>
                <p><b>File Limit:</b> Starbound has a 30-minute limit per track.</p>
                <p><b>If your file is longer:</b> StarSound will ask if you want to split it automatically.</p>
                <p><b>Clear Selected Files:</b> Click this to remove all files and start over.</p>
                <p style="color: #888888; font-size: 11px; margin-top: 12px;">
                    Files are copied to your mod folder during conversion (not modified).
                </p>
            ''',
            
            'step4': '''
                <h3 style="color: #00d4ff;">Step 4: Convert to OGG</h3>
                <p><b>What happens?</b> Your files are converted to OGG format (required by Starbound).</p>
                <p><b>Steps:</b></p>
                <ol>
                    <li>Click "Convert to OGG"</li>
                    <li>Choose audio processing options (optional)</li>
                    <li>StarSound converts each file and shows progress</li>
                    <li>Your OGG files are saved to the mod folder</li>
                </ol>
                <p><b>Audio Processing:</b> You can customize:</p>
                <ul>
                    <li><b>Normalization:</b> Make all tracks the same loudness</li>
                    <li><b>Fade In/Out:</b> Smooth start and end (recommended)</li>
                    <li><b>Compression:</b> Reduce dynamic range</li>
                </ul>
                <p><b>Per-Track Settings:</b> Configure different settings for each file individually.</p>
                <p style="color: #888888; font-size: 11px; margin-top: 12px;">
                    Conversion may take a few minutes depending on file count and size.
                </p>
            ''',
            
            'step5': '''
                <h3 style="color: #00d4ff;">Step 5: Choose Patching Method</h3>
                <p><b>What is patching?</b> How your tracks are added to Starbound's music system.</p>
                <p><b>Three options:</b></p>
                <p><b>🎵 Add To Vanilla (Recommended)</b></p>
                <ul>
                    <li>Keeps all original Starbound music</li>
                    <li>Your tracks play randomly alongside vanilla tracks</li>
                    <li>Best for most players</li>
                </ul>
                <p><b>🔄 Replace Tracks</b></p>
                <ul>
                    <li>Removes some vanilla tracks</li>
                    <li>Your tracks replace them</li>
                    <li>Use if you want a completely different music experience</li>
                </ul>
                <p><b>⚡ Both (Add + Replace)</b></p>
                <ul>
                    <li>Combination of both methods</li>
                    <li>More control over which tracks are replaced</li>
                </ul>
                <p style="color: #888888; font-size: 11px; margin-top: 12px;">
                    You can change this later by creating a new mod with the same music files.
                </p>
            ''',
            
            'step6': '''
                <h3 style="color: #00d4ff;">Step 6: Choose When Tracks Play</h3>
                <p><b>When should your music play?</b></p>
                <p><b>🌞 Day Biome:</b> Music plays during the day</p>
                <p><b>🌙 Night Biome:</b> Music plays at night</p>
                <p><b>🌍 All Biomes:</b> Music plays everywhere</p>
                <p><b>Steps:</b></p>
                <ol>
                    <li>Select one or more biomes (left side)</li>
                    <li>Choose which tracks play in selected biomes (right side)</li>
                    <li>Click "Apply Selection"</li>
                </ol>
                <p><b>Multiple Biomes:</b> You can apply the same track to multiple biomes.</p>
                <p style="color: #888888; font-size: 11px; margin-top: 12px;">
                    Your selections are saved and can be loaded next time you run StarSound.
                </p>
            ''',
            
            'audio_processing': '''
                <h3 style="color: #00d4ff;">Audio Processing Tools</h3>
                <p><b>What are these tools?</b> Optional audio enhancements for your tracks.</p>
                <p><b>🔁 Audio Trimmer</b></p>
                <p>Remove unwanted sections from the start or end of your track (silence, intro, outro).</p>
                
                <p><b>🔇 Silence Trimming</b></p>
                <p>Automatically removes quiet/blank sections at the start and end.</p>
                
                <p><b>🎚️ Sonic Scrubber</b></p>
                <p>Removes low rumble and high hiss (cleaning filter).</p>
                
                <p><b>📊 Compression</b></p>
                <p>Reduces the volume difference between loud and quiet parts.</p>
                
                <p><b>🔅 Soft Clipping</b></p>
                <p>Prevents harsh digital distortion from loud peaks.</p>
                
                <p><b>🎛️ EQ (Equalization)</b></p>
                <p>Adjust treble/mid/bass frequencies. Options: Flat, Warm (bass), Bright (treble).</p>
                
                <p><b>📢 Normalization</b></p>
                <p><b>Recommended!</b> Makes all tracks the same perceived loudness so no track is too loud or quiet.</p>
                
                <p><b>🔈 Fade In/Out</b></p>
                <p><b>ALWAYS recommended!</b> Smooth volume fade at start and end of track. Prevents jarring cutoffs.</p>
                
                <p><b>🗣️ De-Esser</b></p>
                <p>Reduces harsh "sss" sounds in vocals and cymbals.</p>
                
                <p><b>🎼 Stereo to Mono</b></p>
                <p>Converts stereo files to mono. Use only if your file is actually mono.</p>
                
                <p style="color: #888888; font-size: 11px; margin-top: 12px;">
                    <b>Hover over each tool for more info.</b> You can customize settings per track.
                </p>
            ''',
            
            'split_files': '''
                <h3 style="color: #00d4ff;">Splitting Long Files</h3>
                <p><b>Why split?</b> Starbound has a 30-minute limit per music track.</p>
                <p><b>What happens?</b> If you have a file longer than 30 minutes, StarSound asks if you want to split it.</p>
                <p><b>Example:</b> A 60-minute ambient track becomes two 30-minute segments.</p>
                <p><b>Options:</b></p>
                <ul>
                    <li><b>✓ Split It:</b> Automatically divide the file into equal parts</li>
                    <li><b>✗ Skip Splitting:</b> Keep the file as-is (might not work in Starbound!)</li>
                    <li><b>Custom Segments:</b> Specify exact split points if you want (e.g., split at 25 min instead of 30)</li>
                </ul>
                <p><b>Split Segments Dialog:</b></p>
                <p>Configure segment length (how many minutes per split). Default is safe maximum (30 min).</p>
                <p>Each segment becomes a separate track in Starbound.</p>
                <p style="color: #888888; font-size: 11px; margin-top: 12px;">
                    <b>Tip:</b> Splitting loses no audio quality—it's just dividing the timeline.
                </p>
            ''',
            
            'biome_selection': '''
                <h3 style="color: #00d4ff;">Biome & Track Selection</h3>
                <p><b>What are biomes?</b> Different environments where music plays (Forest, Cave, Beach, etc.).</p>
                <p><b>Step 6 Dialog:</b></p>
                <ol>
                    <li><b>Left side:</b> List of all Starbound biomes</li>
                    <li><b>Right side:</b> List of your tracks</li>
                    <li>Select a biome, then select which of your tracks play there</li>
                    <li>Click "Apply Selection" to confirm</li>
                </ol>
                <p><b>Example:</b></p>
                <ul>
                    <li>Select "Forest" (left)</li>
                    <li>Check "MyTrack1.ogg" and "MyTrack2.ogg" (right)</li>
                    <li>These tracks will randomly play in Forest biomes</li>
                </ul>
                <p><b>Multiple Tracks Per Biome:</b> Starbound randomly chooses one track each time music plays.</p>
                <p style="color: #888888; font-size: 11px; margin-top: 12px;">
                    You can assign the same track to multiple biomes.
                </p>
            ''',
            
            'vanilla_tracks': '''
                <h3 style="color: #00d4ff;">Using Vanilla Starbound Tracks</h3>
                <p><b>What are vanilla tracks?</b> The original Starbound music files.</p>
                <p><b>Can I use them in my mod?</b> Yes, with the "Add To Vanilla" patch mode.</p>
                <p><b>Vanilla Setup Wizard:</b> StarSound can analyze and list vanilla tracks.</p>
                <p><b>Steps:</b></p>
                <ol>
                    <li>Have Starbound installed</li>
                    <li>StarSound will scan the vanilla assets</li>
                    <li>You'll see a list of all vanilla tracks</li>
                    <li>You can choose to keep them, replace some, or add your own</li>
                </ol>
                <p style="color: #888888; font-size: 11px; margin-top: 12px;">
                    The vanilla setup wizard runs automatically on first launch if Starbound is detected.
                </p>
            ''',
            
            'troubleshooting': '''
                <h3 style="color: #00d4ff;">Troubleshooting & FAQ</h3>
                
                <p><b>❓ My mod doesn't appear in Starbound</b></p>
                <p>✓ Make sure you saved it to <code>Starbound/mods/</code></p>
                <p>✓ Restart Starbound after installing the mod</p>
                <p>✓ Check that the mod folder has all required files</p>
                
                <p><b>❓ No music is playing</b></p>
                <p>✓ Music volume might be at 0% in game settings</p>
                <p>✓ Make sure you selected biomes in Step 6</p>
                <p>✓ Try using "Add To Vanilla" mode first</p>
                
                <p><b>❓ The conversion is very slow</b></p>
                <p>✓ Large files (1+ hours) take time to convert</p>
                <p>✓ Don't close StarSound while converting</p>
                <p>✓ Check that FFmpeg is installed correctly</p>
                
                <p><b>❓ Conversion failed with an error</b></p>
                <p>✓ Check the Active Log for error details</p>
                <p>✓ Make sure your audio file isn't corrupted</p>
                <p>✓ Try with a different audio format</p>
                
                <p><b>❓ Can I edit a mod after creating it?</b></p>
                <p>✓ Yes! Load the mod again by entering its name</p>
                <p>✓ StarSound remembers your settings</p>
                
                <p><b>❓ What audio formats are supported?</b></p>
                <p>✓ MP3, WAV, FLAC, OGG, M4A, WMA, and more</p>
                <p>✓ Anything FFmpeg supports will work</p>
                
                <p style="color: #888888; font-size: 11px; margin-top: 12px;">
                    For more help, check the log files or Discord community for StarSound.
                </p>
            ''',
        }
        
        return contents.get(topic_id, '<p style="color: #888888;">No help available for this topic.</p>')
