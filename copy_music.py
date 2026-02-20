import shutil
import os

src_dir = r'c:\Users\Stephanie\OneDrive\Documents\Original Starbound Unpacked\music'
dst_dir = r'c:\Users\Stephanie\OneDrive\Documents\Starbound Modding\StaroundMusicModGenerator\assets\music'

count = 0
for file in os.listdir(src_dir):
    if file.endswith('.ogg'):
        src_file = os.path.join(src_dir, file)
        dst_file = os.path.join(dst_dir, file)
        shutil.copy2(src_file, dst_file)
        count += 1
        
print(f'Successfully copied {count} music files!')
