# Final test - Verify fonts work on restart
import json
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import QFont

# Set UTF-8 encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent / "pygui"))

def test_final():
    """Final font verification test"""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    from starsound_gui import MainWindow
    gui = MainWindow()
    
    print("\n" + "="*70)
    print("FINAL FONT TEST - StarSound Font Persistence & Application")
    print("="*70)
    
    # Check settings
    saved_font_name = gui.settings.get('current_font', 'Hobo')
    print(f"\n1. Settings Persistence:")
    print(f"   Saved font in settings.json: {saved_font_name}")
    
    # Check if font is in menu checkmark
    fonts_applied = 0
    total_labels = len(gui.findChildren(QLabel))
    
    for label in gui.findChildren(QLabel):
        label_font = label.font()
        label_family = label_font.family()
        
        if label_family == saved_font_name:
            fonts_applied += 1
    
    print(f"\n2. Font Application on Screen:")
    print(f"   Total labels tested: {total_labels}")
    print(f"   Labels with correct font: {fonts_applied}")
    font_percentage = int((fonts_applied / total_labels) * 100) if total_labels > 0 else 0
    print(f"   Success rate: {font_percentage}%")
    
    # Final verdict
    print(f"\n3. Verdict:")
    if fonts_applied >= (total_labels * 0.8):  # 80% threshold
        print(f"   [SUCCESS] Fonts are persisting and displaying correctly!")
        print(f"   [{font_percentage}% of widgets have correct font applied]")
        result = 0
    else:
        print(f"   [PARTIAL] Some widgets still have system default font")
        print(f"   [{font_percentage}% of widgets have correct font applied]")
        result = 1
    
    print("\n" + "="*70 + "\n")
    
    gui.close()
    sys.exit(result)

if __name__ == "__main__":
    test_final()
