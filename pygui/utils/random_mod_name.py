
import random
import string

# Session cache to avoid duplicates
_recent_names = []
_recent_max = 10  # Number of recent names to remember

def _a_or_an(word):
    """Return 'an' if word starts with a vowel sound, else 'a'."""
    return 'an' if word[0].lower() in 'aeiou' else 'a'

def generate_random_mod_name() -> str:
    # ============ STARBOUND-SPECIFIC WORD POOLS (BY FIRST LETTER) ============
    # These are used with higher priority when available
    starbound_by_letter = {
        'A': ['Apex', 'Avian', 'Affinity', 'Artifact', 'Agrobat', 'Aurorabee', 'Ashsprite', 'Anchor', 'Altar', 'Abyss', 'Alliance', 'Ancientvault', 'Aurora'],
        'B': ['Boomerang', 'Bow', 'Broadsword', 'Blaststone', 'Bobot', 'Bulbop', 'Brass', 'Batong', 'Bobfae', 'Bountylair', 'Ballroom', 'Beach'],
        'C': ['Chakram', 'Capricoat', 'Crabcano', 'Crutter', 'Cosmicintruder', 'Candyblock', 'Copper', 'Crystal', 'Casiopeia', 'Celestial', 'Cinderfly', 'Cathexis', 'Colossus', 'Constellation', 'Cultistlair', 'Cyberspace'],
        'D': ['Dagger', 'Direstone', 'Dermis', 'Durasteel', 'Dragon', 'Drosera', 'Desert', 'Dead', 'Deep', 'Dewhopper', 'Driftbell', 'Dustmoth', 'Diamond', 'Dolly'],
        'E': ['Europa', 'Error', 'Eternality', 'Etude', 'Eclipse', 'Eldritch', 'Emerald', 'Eridanus', 'Eventide', 'Eternal', 'Event', 'Exploration', 'Expedition'],
        'F': ['Flamethrower', 'Floran', 'Fireygiant', 'Flameroach', 'Frostfleck', 'Frostfly', 'Forest', 'Forsaken', 'Fennix', 'Fawnfly', 'Frostbite'],
        'G': ['Glitch', 'Geode', 'Girder', 'Glass', 'Gateway', 'Garden', 'Gasgiant', 'Glowbug', 'Glitchy', 'Gardengate', 'Gleap'],
        'H': ['Hylotl', 'Hammer', 'Hemogoblin', 'Hypnare', 'Hivehog', 'Heathugger', 'Haiku', 'Home', 'Hymn', 'Horsehead', 'Harmony', 'Heavydrone'],
        'I': ['Immortal', 'Inviolate', 'Iguarmor', 'Icetip', 'Impact'],
        'J': ['Jungle', 'Junk', 'Jazz'],
        'K': ['Kluex', 'Kluexian', 'Kingdom', 'Klezmer'],
        'L': ['Lash', 'Lilodon', 'Limestone', 'Lava', 'Lavahopper', 'Lunar', 'Luminous', 'Lush', 'Lyre', 'Lute', 'Lullaby'],
        'M': ['Mandraflora', 'Miasmop', 'Moonstone', 'Marble', 'Meteorite', 'Mirror', 'Moonrock', 'Moondust', 'Masteroid', 'Mechtest', 'Magmarock', 'Magma', 'Maelstrom', 'Midnight', 'Moon', 'Museum', 'Muddancer', 'Mudstag', 'Mira', 'Molten', 'Mazurka', 'Melody', 'Minuet'],
        'N': ['Novakid', 'Narfin', 'Nutmidge', 'Nomad', 'Nomadic', 'Nomads', 'Neon', 'Nebula', 'Naturalcave', 'Nocturne'],
        'O': ['Oogler', 'Orbide', 'Obsidian', 'Oceanfloor', 'Ocean', 'Outpost', 'Omnicannon', 'Oculob', 'Odeon', 'Opera', 'Orchestral'],
        'P': ['Plasma', 'Penguin', 'Peacekeeper', 'Peblit', 'Petricub', 'Pipkin', 'Punchy', 'Platinum', 'Purplecrystal', 'Planetarium', 'Peacekeepers', 'Phoenixfly', 'Polarmoth', 'Procyon', 'Psyche', 'Protective', 'Portal', 'Protectorate', 'Parasprite', 'Paratail', 'Pteropod', 'Pulpin', 'Prelude', 'Philharmonic', 'Percussion'],
        'Q': ['Quagmutt', 'Quantum'],
        'R': ['Rex', 'Ringram', 'Resonant', 'Ruby', 'Rustick', 'Rondo', 'Rhapsody'],
        'S': ['Shadow', 'Sawblade', 'Sentinel', 'Scaveran', 'Smoglin', 'Snaunt', 'Snuffish', 'Sporgus', 'Stellar', 'Sonic', 'Spectral', 'Synthesized', 'Symphonic', 'Scintillating', 'Spiraling', 'Sublime', 'Stardust', 'Swansong', 'Sirius', 'Savannah', 'Scorian', 'Sewer', 'Seismic', 'Scandroid', 'Snaggler', 'Spinemine', 'Sonata', 'Symphony', 'Samba', 'Ska', 'Synth'],
        'T': ['Tarball', 'Tank', 'Taroni', 'Toumingo', 'Trictus', 'Temple', 'Tentacle', 'Tile', 'Tranquility', 'Temporal', 'Techno', 'Thunder', 'Tingling', 'Tent', 'Toxic', 'Transcendent', 'Toccata', 'Trap', 'Tintic', 'Triplod', 'Tentaclebomb', 'Tentaclegnat', 'Tentaclespawner', 'Tidefly', 'Tango', 'Theremin', 'Timpani'],
        'U': ['Ultramarine', 'Universal', 'Underworld', 'Unreal', 'Ultra', 'Ukulele'],
        'V': ['Voltip', 'Vivace', 'Vaporwave', 'Void', 'Vault', 'Vex', 'Vile', 'Volatile', 'Viridian', 'Violet', 'Vampiric', 'Visions', 'Violin'],
        'W': ['Wand', 'Wild', 'Wreck', 'Wicker', 'Whisper', 'Winged', 'Wormhole', 'Waltz'],
        'X': ['Xenofly', 'Xylophone'],
        'Y': ['Yokat'],
        'Z': ['Ziggurat', 'Zodiac', 'Zenith', 'Zither'],
    }

    # 1. Easter egg names (rare)
    easter_eggs = [
        'Rickroll Rhapsody - StarSound Generated Music Mod',
        'The Forbidden Chord - StarSound Generated Music Mod',
        'The Lost MIDI File - StarSound Generated Music Mod',
        'The Infinite Loop - StarSound Generated Music Mod',
        '404 Track Not Found - StarSound Generated Music Mod',
        'The Blue Note of Destiny - StarSound Generated Music Mod',
        'The Secret Song - StarSound Generated Music Mod',
        'The Unplayable Symphony - StarSound Generated Music Mod',
        'The Final Countdown - StarSound Generated Music Mod',
        'The Hidden Track - StarSound Generated Music Mod',
        'The Brown Note - StarSound Generated Music Mod',
        'The Glitch in the Matrix - StarSound Generated Music Mod',
        'The Forbidden Scale - StarSound Generated Music Mod',
        'The 8-bit Banger - StarSound Generated Music Mod',
        'The Meme Medley - StarSound Generated Music Mod',
        'The Secret Cow Level - StarSound Generated Music Mod',
        'Wirt\'s Peg Leg - StarSound Generated Music Mod',
        'The Song That Must Not Be Named - StarSound Generated Music Mod',
        'The Phantom Melody - StarSound Generated Music Mod',
        'The Missing Link - StarSound Generated Music Mod',
        'The Uncanny Valley Waltz - StarSound Generated Music Mod',
        'The Yodeling Yeti - StarSound Generated Music Mod',
        'The Polka of Power - StarSound Generated Music Mod',
        'The Funky Chicken Dance - StarSound Generated Music Mod',
        'The Banned Song - StarSound Generated Music Mod',
        'The Neverending Track - StarSound Generated Music Mod',
        'The Secret Mario World - StarSound Generated Music Mod',
        'The Lo-Fi Hip Hop Study Jam - StarSound Generated Music Mod',
        'The Elevator Bossa Nova - StarSound Generated Music Mod',
        'The Cat Jams - StarSound Generated Music Mod',
        'The Forbidden Polyrhythm - StarSound Generated Music Mod',
        'The Meme Symphony - StarSound Generated Music Mod',
        'The Bass Drop Heard Around the World - StarSound Generated Music Mod',
    ]
    if random.random() < 0.01:
        return random.choice(easter_eggs)
    
    # ============ SPECIAL NARRATIVE PATTERNS (15% chance) ============
    # These create fun, interconnected names with storytelling flavor
    if random.random() < 0.15:
        locations = [
            'The Stars', 'The Void', 'The Cosmos', 'The Protectorate', 'The Temple', 'The Glitch Dimension', 
            'The Vault', 'The Tentacles', 'The Aether', 'The Galaxy', 'The Cosmic Sea', 'The Nebula', 
            'The Outlands', 'The Abyss', 'Deep Space', 'The Edge of Space', 'The Vault of Memories', 
            'The Void of Echoes', 'The Aether of Dreams', 'The Crystal Archives', 'The Cosmic Library'
        ]
        races = ['Hylotl', 'Novakid', 'Floran', 'Avian', 'Apex', 'Glitch', 'The Hylotl', 'The Floran', 'The Nomads', 'The Peacekeepers', 'The Sentinels', 'The Guardians']
        companions = ['PopTopCats', 'Tentaclings', 'Glitchlings', 'Lunar Sprites', 'Starlings', 'Void Walkers', 'Crystal Keepers', 'Song Spirits', 'Melody Sprites']
        adjectives_special = ['Cosmic', 'Stellar', 'Celestial', 'Mystical', 'Epic', 'Grand', 'Legendary', 'Melodic', 'Harmonic', 'Symphonic', 'Ethereal', 'Lost', 'Forgotten', 'Hidden', 'Secret', 'Eternal', 'Ancient']
        
        objects = ['Machine', 'System', 'Code', 'Network', 'Matrix', 'Collective', 'Choir', 'Assembly', 'Engine', 'Heartbeat', 'Pulse']
        concepts = ['Matrix', 'Cosmos', 'Void', 'Aether', 'Cosmic Dance', 'Digital Realm', 'Symphony', 'Harmony', 'Resonance', 'Infinite', 'Eternity']
        materials = ['Stars', 'Light', 'Dreams', 'Time', 'Energy', 'Sound', 'Echoes', 'Stardust', 'Memories', 'Infinity']
        nouns_pool = ['Melody', 'Symphony', 'Soundtrack', 'Aria', 'Harmony', 'Chord', 'Resonance', 'Echo', 'Whisper', 'Dream']
        place_objects = ['Stars', 'Cosmos', 'Void', 'Aether', 'Galaxy', 'Nebula', 'Outlands', 'Abyss', 'Vault', 'Space', 'Archive', 'Library', 'Crystal Archives']
        
        story_patterns = [
            'A Journey Through {location}',
            'A Quest Across {location}',
            '{race} and The {object}',
            '{article} {adjective} Mix-Tape From {location}',
            'The {adjective} Chronicles of {race}',
            '{adjective} Symphonies From {location}',
            'A Sonic Journey With {race}',
            'Tales From {location}',
            '{article} {adjective} Adventure Beyond {location}',
            'The {adjective} Saga of {race}',
            '{article} {noun} Written in the {place_objects}',
            '{race} in The {concept}',
            '{article} {noun} Made Of {material}',
        ]
        
        pattern = random.choice(story_patterns)
        
        # Replace placeholders with actual values
        if '{location}' in pattern:
            pattern = pattern.replace('{location}', random.choice(locations))
        if '{race}' in pattern:
            pattern = pattern.replace('{race}', random.choice(races))
        if '{companion}' in pattern:
            pattern = pattern.replace('{companion}', random.choice(companions))
        if '{object}' in pattern:
            pattern = pattern.replace('{object}', random.choice(objects))
        if '{concept}' in pattern:
            pattern = pattern.replace('{concept}', random.choice(concepts))
        if '{material}' in pattern:
            pattern = pattern.replace('{material}', random.choice(materials))
        if '{place_objects}' in pattern:
            pattern = pattern.replace('{place_objects}', random.choice(place_objects))
        if '{noun}' in pattern:
            pattern = pattern.replace('{noun}', random.choice(nouns_pool))
        if '{adjective}' in pattern:
            pattern = pattern.replace('{adjective}', random.choice(adjectives_special))
        
        # Fix article (A vs An) if present
        if '{article}' in pattern:
            # Get the next word after {article} to determine A vs An
            # Could be {adjective} or {noun} depending on pattern
            parts = pattern.split('{article} ')
            if len(parts) > 1:
                next_placeholder = parts[1].split(' ')[0]
                if next_placeholder == '{noun}':
                    first_word = random.choice(nouns_pool)
                elif next_placeholder == '{adjective}':
                    first_word = random.choice(adjectives_special)
                else:
                    first_word = next_placeholder
                article = 'An' if first_word and first_word[0].lower() in 'aeiou' else 'A'
            else:
                article = 'A'
            pattern = pattern.replace('{article}', article)
        
        name = pattern + ' - StarSound Generated Music Mod'
        return name
    
    adjectives = [
        # ============ STARBOUND-THEMED WORDS ============
        # Races & Factions
        'Stellar', 'Cosmic', 'Celestial', 'Glitchy', 'Glitched', 'Tentacled', 'Apex', 'Avian', 'Floran', 'Hylotl',
        'Novakid', 'Peaceful', 'Nomadic', 'Protectorate', 'Kluexian', 'Affinity', 'Volatile', 'Artifact',
        'Dimensional', 'Quantum', 'Aurora', 'Sonic', 'Resonant', 'Crystalline', 'Primal', 'Vile',
        # Biomes & Materials
        'Volcanic', 'Toxic', 'Frozen', 'Acidic', 'Arctic', 'Desert', 'Jungle', 'Oceanic', 'Corrupted',
        'Ashen', 'Crystallized', 'Rusted', 'Molten', 'Scorched', 'Barren', 'Earthy', 'Tentacled', 'Cursed',
        # Weapons & Combat
        'Plasma', 'Electric', 'Thorny', 'Flaming', 'Icy', 'Slashing', 'Piercing', 'Vexing', 'Bombarding',
        # Creatures & Biology
        'Buggy', 'Beastly', 'Venomous', 'Scaled', 'Winged', 'Chitinous',
        # Effects & Status
        'Frostbitten', 'Burning', 'Shocked', 'Poisoned', 'Stunned',
        
        # A words
        'Allegro', 'Andante', 'Aurora', 'Astral', 'Ambient', 'Aggression', 'Apex', 'Angelic', 'Arcane', 'Ascending',
        'Atmospheric', 'Alien', 'Awakening', 'Apocalyptic', 'Abyssal', 'Acoustic', 'Avant-garde', 'Aethereal',
        'Ancient', 'Arcadian', 'Anthemic', 'Acoustical', 'Archived', 'Aria', 'Arpeggiated', 'Articulate', 'Ascendant', 'Amplified', 'Augmented', 'Arranged',
        
        # B words
        'Baroque', 'Brilliant', 'Blazing', 'Broken', 'Boundless', 'Bewitching', 'Beautiful', 'Bracing', 'Bluesy',
        'Bouncy', 'Binary', 'Biological', 'Booming', 'Breathtaking', 'Bursting', 'Bassline', 'Bold', 'Breakbeat',
        
        # C words
        'Cosmic', 'Celestial', 'Chromatic', 'Crystalline', 'Crimson', 'Chilling', 'Cascading',
        'Colossal', 'Cinematic', 'Catchy', 'Chaotic', 'Consonant', 'Celestine', 'Courageous', 'Cybernetic',
        'Cantabile', 'Cantata', 'Classical', 'Choral', 'Chant', 'Cinematic', 'Choral', 'Cobalt',
        
        # D words
        'Dimensional', 'Dramatic', 'Dappled', 'Dreaming', 'Dissonant', 'Dazzling', 'Desolate', 'Delicate',
        'Dynamic', 'Driving', 'Dusky', 'Daring', 'Delirious', 'Demonic', 'Digital', 'Dubstep', 'Dolce',
        'Dancing', 'Diamond', 'Down', 'Dusky', 'Dusk', 'Drum and Bass', 'Darkwave', 'Deep House', 'Drill',
        
        # E words
        'Ethereal', 'Echoing', 'Elegant', 'Enigmatic', 'Euphoric', 'Electric', 'Energetic',
        'Exquisite', 'Ecstatic', 'Eerie', 'Elevating', 'Experimental', 'Endless', 'Explosive', 'Eternal',
        'Eternality', 'Etude', 'Eclipse', 'Echoic', 'Eldritch', 'Emerald', 'Expressive', 'Epic',
        
        # F words
        'Funky', 'Fabled', 'Foreboding', 'Frantic', 'Fluorescent', 'Fierce', 'Folksy', 'Formidable', 'Forte',
        'Futuristic', 'Flowing', 'Furious', 'Frenetic', 'Floating', 'Fantastical', 'Frivolous',
        'Falling', 'Frosted', 'Frozen', 'Folky', 'Futurism',
        
        # G words
        'Galactic', 'Groovy', 'Golden', 'Glorious', 'Glitchy', 'Gleaming', 'Gothic', 'Gaudy', 'Gorgeous',
        'Ghostly', 'Grandiose', 'Gritty', 'Grinding', 'Gravity', 'Gregarious', 'Groaning', 'Glimmering',
        'Gregorian', 'Granular', 'Growling', 'Graceful', 'Gallant', 'Glistening', 'Glowing', 'Gliding',
        'Giocoso', 'Gregorian', 'Glare', 'Gleaming', 'Grinding', 'Groaning', 'Glorious',
        
        # H words
        'Harmonic', 'Hypnotic', 'Heavenly', 'Haunting', 'Heroic', 'Hollow', 'Hyperdrive', 'Hopping',
        'Hazy', 'Hectic', 'Harmonious', 'Hallucinogenic', 'Hovering', 'Harsh', 'Hyperactive', 'Hopeful',
        'Hidden', 'Hypnotic', 'Haunting', 'Hyperdrive', 'Hip-Hop', 'House', 'Hyperpop',
        
        # I words
        'Iridescent', 'Infinite', 'Intense', 'Interstellar', 'Introspective', 'Industrial', 'Ironic', 'Inspiring',
        'Improvisational', 'Icy', 'Incandescent', 'Infectious', 'Invigorating', 'Irritating', 'Imaginative',
        'Improvised', 'Instrumental', 'Infernal',
        
        # J words
        'Jazzy', 'Jarring', 'Joyful', 'Jolting', 'Jaunty', 'Juddering', 'Joyriding', 'Jangling','Jingling',
        
        # K words
        'Kinetic', 'Kaleidoscopic', 'Kooky', 'Kickass', 'Kinky', 'Keystone', 'Knighted', 'Knowing',
        
        # L words
        'Lyrical', 'Luminous', 'Lucid', 'Lively', 'Lofty', 'Lush', 'Lamenting', 'Laconic', 'Lustrous',
        'Liminal', 'Languid', 'Legendary', 'Labyrinthine', 'Langur', 'Lethargic', 'Luxuriant', 'Luring',
        'Lavish', 'Lurid', 'Longing', 'Lazy', 'Laughing', 'Luminescent', 'Liberal', 'Lunar', 'Lento',
        'Lullaby', 'Legato', 'Layered', 'Lost', 'Lyric', 'Lilting', 'Lilting', 'Lisping', 'Liturgical',
        
        # M words
        'Melodic', 'Mystical', 'Majestic', 'Mystic', 'Monumental', 'Melancholic', 'Mesmerizing', 'Modular',
        'Magnetic', 'Minimalist', 'Mournful', 'Manic', 'Metallic', 'Modern', 'Medieval', 'Mechanized',
        'Melodious', 'Murky', 'Mutant', 'Monstrous', 'Messy', 'Mental', 'Morphing', 'Mixing',
        'Musical', 'Mellow', 'Mindful', 'Mirthful', 'Marching', 'Major', 'Minor', 'Moving',
        'Minor', 'Modal', 'Modernist', 'Mythic', 'Majestic', 'Mechanical',
        
        # N words
        'Nebulous', 'Nova', 'Nocturnal', 'Neon', 'Notorious', 'Nostalgic', 'Nuclear', 'Naive', 'Numerical',
        'Nomadic', 'Nefarious', 'Nurturing', 'Nullifying', 'Natural', 'Narcissistic', 'Narrative',
        
        # O words
        'Orbiting', 'Orchestral', 'Ominous', 'Opalescent', 'Organic', 'Otherworldly', 'Outlandish', 'Omniscient',
        'Obscure', 'Obsessive', 'Oneiric', 'Ornate', 'Oscillating', 'Outrageous', 'Oozing', 'Oceanic',
        'Opaline', 'Orchestral', 'Oneiric',
        
        # P words
        'Presto', 'Pulsing', 'Piano', 'Prismatic', 'Percussive', 'Progressive', 'Phantasmic', 'Panoramic',
        'Piercing', 'Pristine', 'Powerful', 'Psychedelic', 'Punk', 'Poetic', 'Phenomenal', 'Pungent',
        'Phantasmagoric', 'Perpetual', 'Parallel', 'Portentous', 'Pixelated', 'Programmed', 'Prophetic',
        'Polyphonic', 'Poppy', 'Pulsating', 'Progressive', 'Pop', 'Phonk', 'Progressive House',
        
        # Q words
        'Quantum', 'Quirky', 'Quiet', 'Quixotic', 'Quelling', 'Questioning', 'Quick', 'Quintessential',
        
        # R words
        'Resonant', 'Radiant', 'Rhapsodic', 'Rhythmic', 'Raging', 'Raucous', 'Ravishing', 'Relentless',
        'Robotic', 'Romantic', 'Roaring', 'Righteous', 'Radiating', 'Recursive', 'Reflected', 'Rotten',
        'Rotating', 'Rushing', 'Rustic', 'Regal', 'Roiling', 'Rambling', 'Racking', 'Ruptured',
        'Rising', 'Reggae', 'Resounding', 'Rhythmic', 'Rocking',
        
        # S words
        'Stellar', 'Sonic', 'Spectral', 'Serene', 'Soaring', 'Stitched', 'Somber', 'Surreal', 'Syncopated',
        'Synthesized', 'Spooky', 'Stratospheric', 'Scripted', 'Scattered', 'Surging', 'Swelling', 'Swinging',
        'Symphonic', 'Sensual', 'Sinister', 'Sizzling', 'Shadowed', 'Shimmering', 'Shattered', 'Screeching',
        'Seismic', 'Scintillating', 'Sacred', 'Spiraling', 'Stalwart', 'Stunning', 'Sublime', 'Shredding',
        'Ska', 'Secret', 'Solaris', 'Soothing', 'Stardust', 'Super', 'Swinging', 'Synthy',
        'Singing', 'Sonorous', 'Symphonious', 'Smooth', 'Soulful', 'Soprano', 'Stirring', 'Soloistic',
        'Synthwave', 'Synth', 'Synthpop', 'Samba', 'Soul', 'Synthpop', 'Tech House',
        
        # T words
        'Transcendent', 'Temporal', 'Techno', 'Twinkling', 'Thunderous', 'Thrashing', 'Tangled',
        'Titanic', 'Trancy', 'Trembling', 'Tranquil', 'Triumphant', 'Tragic', 'Twisted', 'Tingling',
        'Turbulent', 'Turbocharged', 'Tactile', 'Tremendous', 'Terrifyingly', 'Tender', 'Theatrical',
        'Tonal', 'Tribal', 'Tropical', 'Turquoise', 'Tattered', 'Thumping', 'Towering', 'Toccata',
        'Textured', 'Trap', 'Trap', 'Twilight', 'Turbo', 'Trance', 'Trap Soul', 'Theremin', 'Timpani', 'Tintic',
        
        # U words
        'Universal', 'Unbound', 'Ultraviolet', 'Unhinged', 'Undulating', 'Unrelenting', 'Unsettling',
        'Ultimate', 'Ubiquitous', 'Unified', 'Underworld', 'Uplifting', 'Urgent', 'Utopian', 'Unreal',
        'Ultra', 'Unexpected', 'Uplifting',
        
        # V words
        'Vivace', 'Vibrant', 'Vaporwave', 'Visceral', 'Vintage', 'Void', 'Virtuosic', 'Vindictive',
        'Ventured', 'Veiled', 'Vestigial', 'Venomous', 'Vertical', 'Volcanic', 'Vampiric', 'Vagabond',
        'Viridian', 'Violet', 'Virtuoso', 'Vital', 'Vivid', 'Vaporwave', 'Vapor',
        
        # W words
        'Wandering', 'Wistful', 'Wailing', 'Whimsical', 'Winding', 'Whispered', 'Wild', 'Warping',
        'Wondrous', 'Weeping', 'Windswept', 'Weathered', 'Wretched', 'Wholesome', 'Watery', 'Wavering',
        'Woozy', 'Withdrawn', 'Writhing', 'Witness', 'Winged', 'Wealthy', 'Weightless',
        
        # X words
        'Xenophobic', 'X-rated',
        
        # Y words
        'Yearning', 'Yodeling', 'Yielding', 'Youthful', 'Yawning', 'Yoked',
        
        # Z words
        'Zany', 'Zesty', 'Zealous', 'Zodiacal', 'Zonal', 'Zippy', 'Zirconic', 'Zapped', 'Zealot',
        'Zigzagging', 'Zooming', 'Zephyr', 'Zenith', 'Zeroed', 'Zinging', 'Zombie',
    ]
    
    nouns = [
        # ============ STARBOUND-THEMED WORDS (300+ DEEP!) ============
        # Races & Factions
        'Kluex', 'Apex', 'Avian', 'Floran', 'Glitch', 'Hylotl', 'Novakid', 'Penguin', 'Shadow',
        'Protectorate', 'Peacekeeper', 'Nomad', 'Cultist', 'Sentinel', 'Guardian',
        
        # Locations & Structures
        'Temple', 'Outpost', 'Lair', 'Vault', 'Gateway', 'Arena', 'Wreck', 'Sewer', 'Museum',
        'Ancientvault', 'Bountylair', 'Cultistlair', 'Cyberspace', 'Gardengate', 'Glitchsewer', 'Mechtest', 'Naturalcave',
        'Techchallenges', 'Tentacle', 'Forsaken',
        
        # Celestial Bodies & Space
        'Europa', 'Casiopeia', 'Eridanus', 'Saturn', 'Mercury', 'Jupiter', 'Cygnus', 'Psyche',
        'Mira', 'Procyon', 'Sirius', 'Vega', 'Altair', 'Deneb', 'Epsilon', 'Horsehead',
        'Magellanic', 'Asteroidfield', 'Lunarbase',
        
        # Music Track Themes & Concepts
        'Accretion', 'Disc', 'Atlas', 'Beach', 'Constellation', 'Dead', 'Deep', 'Desert', 'Drosera',
        'Error', 'Eternal', 'Event', 'Exploration', 'Forest', 'Gravitational', 'Haiku', 'Home',
        'Hymn', 'Impact', 'Immortal', 'Inviolate', 'Kluex', 'Lava', 'Nomads', 'Ocean', 'Peacekeepers',
        'Planetarium', 'Scorian', 'Stellar', 'Swansong', 'Tranquility', 'Ultramarine',
        
        # Weapons
        'Axe', 'Boomerang', 'Bow', 'Broadsword', 'Chakram', 'Dagger', 'Flamethrower', 'Hammer',
        'Lash', 'Plasma', 'Sawblade', 'Shield', 'Shortsword', 'Spear', 'Staff', 'Wand', 'Whip', 'Tarball',
        
        # Creatures & Monsters
        'Anglure', 'Bobot', 'Bulbop', 'Capricoat', 'Crabcano', 'Crutter', 'Fennix', 'Gleap', 'Hemogoblin',
        'Hypnare', 'Lilodon', 'Mandraflora', 'Miasmop', 'Narfin', 'Nutmidge', 'Oogler', 'Orbide', 'Peblit',
        'Petricub', 'Pipkin', 'Punchy', 'Quagmutt', 'Rex', 'Ringram', 'Scaveran', 'Smoglin', 'Snaunt',
        'Snuffish', 'Sporgus', 'Tank', 'Taroni', 'Toumingo', 'Trictus', 'Voltip', 'Yokat',
        'Agrobat', 'Batong', 'Bobfae', 'Cosmicintruder', 'Monopus', 'Parasprite', 'Paratail', 'Pteropod',
        'Scandroid', 'Tentaclebomb', 'Tentaclegnat', 'Tentaclespawner', 'Crustoise', 'Iguarmor', 'Oculob',
        'Pulpin', 'Snaggler', 'Tentaclecrawler', 'Tintic', 'Triplod', 'Ashsprite', 'Aurorabee', 'Beebug',
        'Brightstripe', 'Butterbee', 'Cinderfly', 'Dewhopper', 'Driftbell', 'Dustmoth', 'Fawnfly', 'Fireygiant',
        'Flameroach', 'Frostfleck', 'Frostfly', 'Gasgiant', 'Glowbug', 'Greentip', 'Heathugger', 'Hivehog',
        'Icetip', 'Lavahopper', 'Muddancer', 'Mudstag', 'Orphanfly', 'Phoenixfly', 'Polarmoth', 'Redwing',
        'Sandclown', 'Scuttleploom', 'Seahornet', 'Shadowmoth', 'Shardwing', 'Shellcreep', 'Snowskater', 'Stinkjack',
        'Sunskipper', 'Thornbee', 'Tidefly', 'Xenofly', 'Astrofae', 'Chiropterror', 'Cosmostache', 'Heavydrone',
        'Masteroid', 'Omnicannon', 'Rustick', 'Spinemine', 'Trifangle', 'Twigun', 'Dragon', 'Eye', 'Ape', 'Crystal', 'Robot', 'Spider',
        
        # Materials & Resources
        'Ancient', 'Ash', 'Aztectech', 'Bamboo', 'Blackglass', 'Blaststone', 'Bonematerial', 'Brass', 'Brick',
        'Bronze', 'Candyblock', 'Chain', 'Clay', 'Composite', 'Concrete', 'Copper', 'Corruptdirt', 'Crystal',
        'Dermis', 'Direstone', 'Durasteel', 'Eyepile', 'Fleshblock', 'Frozenwater', 'Geode', 'Girder', 'Glass',
        'Goldblock', 'Gravel', 'Hazard', 'Ice', 'Ironblock', 'Junk', 'Leather', 'Limestone', 'Magmarock',
        'Marble', 'Meteorite', 'Mirror', 'Moondust', 'Moonrock', 'Moonstone', 'Mud', 'Neon', 'Obsidian',
        'Platinum', 'Purplecrystal', 'Rust', 'Sand', 'Sandstone', 'Sewer', 'Shadowblock', 'Silver', 'Slime',
        'Smoothmetal', 'Snow', 'Supermatter', 'Tar', 'Tentacle', 'Tile', 'Tungsten', 'Vine', 'Waste', 'Wicker', 'Wood',
        
        # Biomes & Flora
        'Alien', 'Arctic', 'Barren', 'Desert', 'Earth', 'Forest', 'Garden', 'Jungle', 'Magma',
        'Midnight', 'Moon', 'Ocean', 'Oceanfloor', 'Savannah', 'Scorched', 'Snow', 'Tundra', 'Toxic', 'Volcanic',
        'Deadtree', 'Magictree', 'Mushroom', 'Seatrees', 'Swamp', 'Undergroundforest', 'Vine', 'Hive',
        
        # A words (Music & Starbound themed)
        'Aurora', 'Andante', 'Arpeggio', 'Acme', 'Apex', 'Aether', 'Anthem', 'Atmosphere', 'Archive', 'Artifact',
        'Archipelago', 'Algorithm', 'Alpha', 'Ancient', 'Anomaly', 'Apparatus', 'Avatar', 'Avalanche',
        
        # B words
        'Ballad', 'Beacon', 'Beat', 'Blaze', 'Bassline', 'Bridge', 'Broadcast', 'Biome', 'Behemoth',
        'Biota', 'Blip', 'Bloom', 'Burrow', 'Buffer', 'Binary', 'Boundary', 'Bagatelle',
        
        # C words
        'Cantata', 'Chord', 'Chorus', 'Concerto', 'Cadence', 'Cascade', 'Cosmos', 'Comet', 'Chaconne', 'Creation',
        'Constellation', 'Chamber', 'Chromatic', 'Cipher', 'Circuit', 'Coda', 'Crescendo', 'Crystalline',
        'Chant', 'Cybernetic', 'Cycle', 'Catalyst', 'Chronicle', 'Convection', 'Conductor', 'Cavity',
        
        # D words
        'Dream', 'Dimension', 'Disco', 'Drift', 'Dusk', 'Drop', 'Drums', 'Dynasty', 'Digital', 'Domain',
        'Daze', 'Daybreak', 'Decrescendo', 'Destination', 'Depths', 'Divide', 'Dynamo', 'Defiance', 'Duel',
        
        # E words
        'Echo', 'Etude', 'Eclipse', 'Epoch', 'Enigma', 'Expanse', 'Essence', 'Expedition', 'Equilibrium', 'Era',
        'Euphoria', 'Element', 'Endeavor', 'Eternity', 'Electron', 'Emergence', 'Empire', 'Engine', 'Equinox',
        
        # F words
        'Finale', 'Fugue', 'Fjord', 'Frontier', 'Frequency', 'Fusion', 'Flourish', 'Fervor', 'Foundation',
        'Fragment', 'Fresco', 'Fixture', 'Fiesta', 'Frenzy', 'Fable', 'Flux', 'Foray', 'Fortress', 'Fiber',
        
        # G words
        'Galaxy', 'Genesis', 'Grove', 'Groove', 'Gloss', 'Glow', 'Glitch', 'Garnet', 'Glimmer', 'Grand',
        'Grind', 'Gravity', 'Grotto', 'Geyser', 'Goblet', 'Gossamer', 'Gradient', 'Gestalt', 'Glare', 'Guardian',
        'Gavel', 'Gladiator', 'Glory', 'Guillotine', 'Glimpse', 'Gold', 'Goodness', 'Gravitas', 'Grid',
        
        # H words
        'Harmony', 'Haven', 'Horizon', 'Harmony', 'Harmonic', 'Hearth', 'Hyperdrive', 'Hyperspace', 'Hook',
        'Heritage', 'Herald', 'Hologram', 'Horoscope', 'Hostel', 'Hotbed', 'Hone', 'Hurl', 'Hymn',
        
        # I words
        'Infinity', 'Interlude', 'Interval', 'Iris', 'Islet', 'Icon', 'Ignition', 'Illumination', 'Imagination',
        'Impetus', 'Impulse', 'Inception', 'Incense', 'Inclination', 'Inquest', 'Insignia', 'Inspiration', 'Institute',
        
        # J words
        'Jazz', 'Journey', 'Juncture', 'Jubilee', 'Juniper', 'Jasmine', 'Jester', 'Jetstream',
        
        # K words
        'Key', 'Kingdom', 'Knowledge', 'Kaleidoscope', 'Keynote', 'Kinship', 'Knighthood', 'Karma',
        
        # L words
        'Loop', 'Lullaby', 'Lyre', 'Lagoon', 'Labyrinth', 'Layer', 'Larghetto', 'Legacy', 'Legend', 'Libretto',
        'Light', 'Liberty', 'Library', 'Limbo', 'Litany', 'Locket', 'Loom', 'Lament', 'Lantana',
        'Love', 'Luminescence', 'Lure', 'Luxe', 'Lyric', 'Leitmotif', 'Lexicon', 'Lineage', 'Lighthouse',
        'Lute', 'Largo', 'Legato', 'Lilt', 'Lumen',
        
        # M words
        'Melody', 'Mosaic', 'Muse', 'Mammoth', 'Mover', 'Majesty', 'Maestro', 'Mandate', 'Meadow', 'Meridian',
        'Mirage', 'Minuet', 'Manifesto', 'Magnitude', 'Mechanism', 'Metamorphosis', 'Meteor', 'Metronome',
        'Militia', 'Mindscape', 'Minister', 'Minute', 'Miracle', 'Mire', 'Miscellanea', 'Mission', 'Momentum',
        'Monument', 'Moonlight', 'Motif', 'Movement', 'Mecca', 'Menagerie', 'Merchant', 'Mercury', 'Merger',
        'Mazurka', 'Motet',
        
        # N words
        'Nebula', 'Nova', 'Nocturne', 'Narrative', 'Neon', 'Nitrate', 'Node', 'Nonpareil', 'Notation',
        'Novelty', 'Nucleus', 'Nullifier', 'Numeral', 'Nunnery', 'Nautilus', 'Nebulae', 'Network',
        
        # O words
        'Overture', 'Odyssey', 'Orbit', 'Outpost', 'Opus', 'Obsidian', 'Oasis', 'Oboe', 'Obliquity',
        'Observation', 'Obstruction', 'Occasion', 'Occultism', 'Occupant', 'Octet', 'Odeon',
        'Oracle', 'Oration', 'Ordnance', 'Organism', 'Orientation', 'Orifice', 'Origin', 'Ornament', 'Orpheus',
        
        # P words
        'Prelude', 'Pulse', 'Pathway', 'Precipice', 'Prism', 'Procession', 'Production', 'Prologue', 'Prophecy',
        'Protocol', 'Protector', 'Proton', 'Prototype', 'Psalm', 'Pseudonym', 'Psyche', 'Pulsar', 'Pump', 'Purr',
        'Passage', 'Passion', 'Pattern', 'Pavement', 'Pavilion', 'Peak', 'Pearl', 'Pedestal', 'Pendant', 'Petal',
        'Phantom', 'Pharaoh', 'Phase', 'Phenomenon', 'Philosophy', 'Phoenix', 'Phrase', 'Physician', 'Piano',
        
        # Q words
        'Quartet', 'Quest', 'Quartz', 'Quintessence', 'Quiver', 'Quirk', 'Quorum', 'Quotient',
        'Quarantine', 'Quarter', 'Quake', 'Quicksilver',
        
        # R words
        'Rhapsody', 'Resonance', 'Reverie', 'Rondo', 'Radiance', 'Realm', 'Remnant', 'Rendezvous', 'Revelation',
        'Rhythm', 'Rift', 'Rogue', 'Romance', 'Refuge', 'Regiment', 'Registry', 'Regress', 'Reign', 'Relic',
        'Remedy', 'Remembrance', 'Replica', 'Repository', 'Reprise', 'Resonator', 'Respite', 'Restraint',
        'Resurrection', 'Retina', 'Retinue', 'Return', 'Revenge', 'Revenue', 'Reverence', 'Reversal',
        
        # S words
        'Symphony', 'Serenity', 'Serenade', 'Sonata', 'Spire', 'Spectrum', 'Signal', 'Singularity', 'Solstice',
        'Syntax', 'Synthesis', 'System', 'Saturn', 'Satellite', 'Sanctuary', 'Sandbox', 'Sandstone',
        'Savanna', 'Scarab', 'Scar', 'Scenario', 'Scene', 'Scepter', 'Scholar', 'Schism', 'Scientist', 'Scope',
        'Scorpion', 'Scout', 'Scream', 'Screen', 'Scroll', 'Sculpture', 'Seal', 'Seam', 'Search', 'Seashell',
        'Season', 'Seat', 'Secession', 'Seclusion', 'Second', 'Secret', 'Sector', 'Security',
        'Sediment', 'Seduction', 'Segment', 'Seizure', 'Semaphore', 'Seminary', 'Semblance', 'Senate',
        'Sonatina', 'Sinfonia',
        
        # T words
        'Toccata', 'Temperament', 'Tempo', 'Tempest', 'Temple', 'Temptation', 'Tenacity', 'Tenement',
        'Tenor', 'Tension', 'Tent', 'Tenure', 'Terminal', 'Terminator', 'Terrain', 'Territory',
        'Tether', 'Text', 'Texture', 'Theater', 'Theism', 'Theme', 'Theorem', 'Therapist', 'Theremin',
        'Thesaurus', 'Thesis', 'Thief', 'Thimble', 'Thistle', 'Thorn', 'Thought', 'Thread', 'Threat', 'Threshold',
        'Thrill', 'Throb', 'Throne', 'Throng', 'Throttle', 'Throw', 'Thrust', 'Thunder', 'Tiara', 'Tier',
        'Tiger', 'Timberland', 'Timber', 'Timbre', 'Time', 'Timelapse', 'Timer', 'Timing', 'Tin',
        'Tincture', 'Tinder', 'Tinfoil', 'Tingle', 'Tinker', 'Tinsel', 'Tint', 'Tirade', 'Tissue',
        
        # U words
        'Universe', 'Utopia', 'Ultraviolet', 'Umbra', 'Umpire', 'Unity', 'Union', 'Unison', 'Undertow', 'Underworld',
        'Underpass', 'Underground', 'Unicorn', 'Uniform', 'Unit', 'Universal', 'Unfold', 'Unison', 'Upheaval',
        'Uprising', 'Upland', 'Uplifting', 'Uproar', 'Upshot', 'Upside', 'Upstage', 'Upstart', 'Upstream',
        'Upsurge', 'Uptake', 'Uptempo', 'Upthrust', 'Uptown', 'Uptrend', 'Upturn', 'Upward', 'Urbanity',
        'Urbanism', 'Urbanite', 'Urge', 'Urgency', 'Usage', 'User', 'Usher', 'Usual', 'Usurp', 'Utensil',
        
        # V words
        'Voyage', 'Vortex', 'Void', 'Vibrato', 'Virtuoso', 'Vanguard', 'Vault', 'Verse', 'Vestige', 'Vexation',
        'Vibrance', 'Vicar', 'Vicinity', 'Victory', 'Video', 'Vigilance', 'Vigil', 'Vigor', 'Village', 'Villain',
        'Villainy', 'Vine', 'Vineyard', 'Vinyl', 'Viola', 'Violin', 'Viper', 'Virgin', 'Virgo',
        'Virtuality', 'Virtue', 'Virtu', 'Virus', 'Visa', 'Visage', 'Viscera', 'Viscount', 'Viscosity',
        'Vision', 'Visit', 'Visor', 'Vista', 'Vita', 'Vitality', 'Vitamin', 'Vitriol', 'Vixen', 'Vizard', 'Vizier',
        
        # W words
        'Waltz', 'Wanderlust', 'Waveform', 'Waypoint', 'Whisper', 'Windmill', 'Windsong', 'Wonder', 'Wonderland',
        'Woodland', 'Worm', 'Wormhole', 'Wraith', 'Wrath', 'Wreck', 'Wren', 'Wrench',
        'Wrest', 'Wrestle', 'Wretch', 'Wriggle', 'Wring', 'Wrinkle', 'Writ', 'Write', 'Writer',
        'Writhe', 'Wroth', 'Wrought', 'Wryneck', 'Wych', 'Wye', 'Wyvern', 'Walrus', 'Wander', 'Ward',
        'Ware', 'Warehouse', 'Warfare', 'Warhead', 'Warhorse', 'Warlord',
        'Warning', 'Warp', 'Warrant', 'Warranty', 'Warren', 'Warrior', 'Warship', 'Wart', 'Wartime',
        'Wash', 'Wasp', 'Waste', 'Watch', 'Water', 'Waterfall', 'Waterfront', 'Watershed', 'Waterspout',
        'Watt', 'Wattage', 'Wave', 'Waver', 'Wax', 'Way', 'Waybill', 'Wayfarer', 'Waylay',
        
        # X words (Limited good options)
        'Xanadu', 'Xanth', 'Xenia', 'Xenium', 'Xenogamy', 'Xenograft', 'Xenolith', 'Xenon', 'Xenophage',
        'Xenophobia', 'Xenophyte', 'Xenops', 'Xenotime', 'Xenurus', 'Xeriscape', 'Xerophile', 'Xerophyte',
        'Xerox', 'Xerus', 'X-ray', 'Xylem', 'Xylitol', 'Xylograph', 'Xylography',
        'Xylol', 'Xylophone', 'Xylophonist', 'Xylopia', 'Xylose', 'Xylotomy',
        
        # Y words
        'Yearbook', 'Yearling', 'Yearlong', 'Yearly', 'Yearn', 'Yearning', 'Year', 'Yeast',
        'Yell', 'Yellow', 'Yellowhammer', 'Yelp', 'Yemen', 'Yen', 'Yeoman', 'Yep', 'Yes',
        'Yesterday', 'Yet', 'Yeti', 'Yew', 'Yield', 'Yin', 'Yip', 'Yipe', 'Yippee',
        'Yodel', 'Yogee', 'Yogh', 'Yoghurt', 'Yoga', 'Yogi', 'Yogurt', 'Yohimbe', 'Yoke',
        'Yokel', 'Yolk', 'Yom', 'Yomim', 'Yonder', 'Yoni', 'Yoo-hoo', 'Yore', 'York', 'Yorkshire',
        'You', 'Youngster', 'Younker', 'Your', 'Yours', 'Yourself', 'Youth', 'Yowl', 'Yo-yo', 'Yucca', 'Yucky',
        'Yule', 'Yum', 'Yummy', 'Yup', 'Yurt',
        'Youthful', 'Youths', 'Yowl', 'Yoyo', 'Yo-yo', 'Ytterbium', 'Yttria', 'Yttric', 'Yttrium', 'Yuan',
        
        # Z words
        'Zenith', 'Zephyr', 'Zillion', 'Zodiac', 'Zone', 'Zoology', 'Zucchetto', 'Zydeco', 'Zymology', 'Zygosis',
        'Zither', 'Zen', 'Ziggurat', 'Zircon', 'Zambomba', 'Zampogna', 'Zurna', 'Zest', 'Zeta', 'Zeugma',
        'Zing', 'Zinger', 'Zinnia', 'Zipcode', 'Zipper', 'Zirconia', 'Zirconium', 'Ziti', 'Zither',
    ]
    music_genres = [
        'Pop', 'Trap', 'Lofi', 'Hip-Hop', 'Dubstep', 'Techno', 'House', 'Trance', 'Ambient',
        'Synthwave', 'Vaporwave', 'Chillwave', 'Retrowave', 'Phonk', 'Drum and Bass', 'Garage',
        'Grime', 'Drill', 'Lo-Fi', 'Chill Hop', 'Glitch Hop', 'Glitch', 'Experimental', 'Digital',
        'Synthpop', 'Electropop', 'Synth', 'Darkwave', 'Coldwave', 'Industrial', 'EBM',
        'IDM', 'Intelligent Dance', 'Ambient Techno', 'Micro', 'Minimal', 'Tech House', 'Deep House',
        'Progressive House', 'Liquid', 'Liquid Funk', 'Neurofunk', 'Breakbeat', 'Breakcore', 'UK Garage',
        'Jungle', 'D&B', 'Drum&Bass', 'Atmospheric', 'Future Bass', 'Trap Soul', 'Emo Trap',
        'Cloud Rap', 'Vapor', 'Hyperpop', 'Pc Music', 'Footwork', 'Juke', 'Jersey Club'
    ]
    
    extras = [
        # ============ STARBOUND-THEMED EXTRAS (EXPANDED!) ============
        'of Kluex', 'of the Protectorate', 'of the Tentacles', 'of the Apex', 'of the Glitch',
        'of the Floran', 'of the Hylotl', 'of the Avian', 'of the Novakid', 'of the Outpost',
        'of the Temple', 'of the Vault', 'of the Gateway', 'of the Nomads', 'of the Peacekeepers',
        'of the Artifacts', 'of Affinity', 'from the Protectorate', 'from the Temple', 'from the Void',
        'from the Vault', 'from the Tentacles', 'from the Nexus', 'from the Aether',
        'of the Dragon', 'of the Crystal', 'of the Cultist', 'of the Sentinel', 'of the Guardian',
        'of the Volcano', 'of the Toxic Plane', 'of the Frozen Wastes', 'of the Desert', 'of the Jungle',
        'of the Ocean', 'of the Moon', 'of the Cyberspace', 'of the Ancientvault', 'of the Bountylair',
        'of Plasma', 'of Thunder', 'of Frost', 'of Flame', 'of the Tarball',
        # ============ MUSIC GENRES (NEW!) ============
        'Pop Edition', 'Trap Mix', 'Lofi Sessions', 'Hip-Hop Beats', 'Dubstep Drop',
        'Techno Vibes', 'House Party', 'Trance Journey', 'Ambient Drift', 'Synthwave Dreams',
        
        'of the Lyre', 'of the Lute', 'of the Lullaby', 'of the Loop', 'of the Largo', 'of the Lament', 'of the Lilt',
        'of the Ziggurat', 'of the Zodiac', 'of the Zither', 'of the Zephyr', 'of the Zenith',
        'of the Stars', 'of the Void', 'of the Cosmos', 'of the Ancients', 'of Harmony',
        'of the Protectorate', 'of the Night', 'of the Dawn', 'of the Outpost', 'of the Universe',
        'of the Nebula', 'of the Black Hole', 'of the Spiral', 'of the Dream', 'of the Song',
        'of the Lost Sector', 'of the Forgotten Realms', 'of the Infinite', 'of the Unknown',
        'of the Deep', 'of the Light', 'of the Shadow', 'of the Rift', 'of the Maelstrom',
        'of the Aurora', 'of the Eventide', 'of the Celestials', 'of the Guardians',
        'of the Nomads', 'of the Wanderers', 'of the Drifters', 'of the Seekers',
        'of the Astral Plane', 'of the Harmonics', 'of the Resonance', 'of the Pulse',
        'of the Expedition', 'of the Outlands', 'of the New Dawn', 'of the Old World',
        'of the First Light', 'of the Last Song', 'of the Final Frontier', 'of the Great Beyond',
        'of the Far Reaches', 'of the Silver Sea', 'of the Golden Age', 'of the Crystal Skies',
        'of the Sapphire Night', 'of the Ruby Sun', 'of the Emerald Dream', 'of the Platinum Horizon',
        'the Savior Of Worlds', 'of the Eternal', 'of the Cosmic', 'of the Transcendent',
        'of the Lost Wanderer', 'of the Silent Guardian', 'of the Radiant Beacon', 'of the Ethereal Realm', 'of the Stellar Path',
        'from the Stars', 'from the Void', 'from the Cosmos', 'from the Ancients', 'from Harmony',
        'from the Protectorate', 'from the Night', 'from the Dawn', 'from the Outpost', 'from the Universe',
        'from the Nebula', 'from the Black Hole', 'from the Spiral', 'from the Dream', 'from the Song',
        'from the Lost Sector', 'from the Forgotten Realms', 'from the Infinite', 'from the Unknown',
        'from the Deep', 'from the Light', 'from the Shadow', 'from the Rift', 'from the Maelstrom',
        'from the Aurora', 'from the Eventide', 'from the Celestials', 'from the Guardians',
        'from the Nomads', 'from the Wanderers', 'from the Drifters', 'from the Seekers',
        'from the Astral Plane', 'from the Harmonics', 'from the Resonance', 'from the Pulse',
        'from the Expedition', 'from the Outlands', 'from the New Dawn', 'from the Old World',
        
        'by Hylotl', 'by Floran', 'by Avian', 'by Novakid', 'by the Protectorate', 'by Kluex',
        'by the Hylotl', 'by the Floran', 'by the Avian', 'by the Nomads', 'by the Peacekeepers',
        'Sung by Hylotl', 'Composed by Floran', 'Played by Avian', 'Written by Nomadic Souls',
        'Performed by the Guardians', 'Orchestrated by the Sentinels', 'Arranged by Cosmic Beings',
        'Journey of the Hylotl', 'Path of the Floran', 'Quest of the Avian', 'Voyage Across the Protectorate',
        'Through the Glitch Dimension', 'Within the Void', 'Beyond the Tentacles', 'Across the Vault',
        'From Kluex Himself', 'From the Temple Keepers', 'From the Ancient Vault', 'From the Edge of Space',
    ]

    def pick(arr):
        return random.choice(arr)


    # Alliteration: 80% chance, try to match all three parts
    use_allit = random.random() < 0.8
    extra_used = random.random() < 0.75  # 75% chance for music genres/extras to appear
    multi_adj = random.random() < 0.3  # 30% chance to use two adjectives
    
    # Choose sentence structure (60% traditional, 40% alternate patterns)
    use_alternate = random.random() < 0.4
    
    name = None
    if use_allit:
        tries = 0
        while tries < 10:
            # 75% chance to use Starbound+Music words (PRIMARY), 25% chance to use generic words
            prefer_starbound_music = random.random() < 0.75
            
            if prefer_starbound_music and any(starbound_by_letter.values()):
                # Pick a letter that has Starbound+Music words (primary pool)
                available_letters = [l for l in starbound_by_letter if starbound_by_letter[l]]
                if available_letters:
                    letter = random.choice(available_letters)
                    pool = starbound_by_letter[letter]
                    # IMPORTANT: Ensure adjective and noun are different to avoid duplicates like 'Iguarmor Iguarmor'
                    if len(pool) > 1:
                        adj_choices = pool
                        noun_choices = pool
                    else:
                        # Pool too small, fall back to generic
                        letter = random.choice(string.ascii_uppercase)
                        adj_choices = [a for a in adjectives if a.upper().startswith(letter)]
                        noun_choices = [n for n in nouns if n.upper().startswith(letter)]
                else:
                    letter = random.choice(string.ascii_uppercase)
                    adj_choices = [a for a in adjectives if a.upper().startswith(letter)]
                    noun_choices = [n for n in nouns if n.upper().startswith(letter)]
            else:
                # Fall back to full generic music word lists
                letter = random.choice(string.ascii_uppercase)
                adj_choices = [a for a in adjectives if a.upper().startswith(letter)]
                noun_choices = [n for n in nouns if n.upper().startswith(letter)]
            
            extra_choices = []
            if extra_used:
                for e in extras:
                    # Find the first word after 'of', 'from', or 'the', or just the first word
                    e_words = e.split()
                    first = None
                    for w in e_words:
                        if w.lower() not in ['of', 'from', 'the']:
                            first = w
                            break
                    else:
                        if not e_words:
                            # Nothing to inspect in this extra; skip it
                            continue
                        first = e_words[0]
                    if first and first.upper().startswith(letter):
                        extra_choices.append(e)
            else:
                extra_choices = [None]
            if adj_choices and noun_choices and (not extra_used or extra_choices):
                if multi_adj and len(adj_choices) > 1:
                    adjs = random.sample(adj_choices, 2)
                    adj = f"{adjs[0]} {adjs[1]}"
                else:
                    adj = pick(adj_choices)
                # CRUCIAL FIX: Ensure noun is different from adj to prevent duplicates
                noun_choices_filtered = [n for n in noun_choices if n != adj]
                if not noun_choices_filtered:
                    noun_choices_filtered = noun_choices
                noun = pick(noun_choices_filtered)
                extra = pick(extra_choices) if extra_used else ''
                
                # Apply alternate sentence structure for alliteration
                if use_alternate and adj_choices and noun_choices:
                    pattern = random.choice(['noun_of_adj', 'adj_noun_and', 'noun_rising'])
                    if pattern == 'noun_of_adj':
                        noun2 = pick(noun_choices)
                        name = f"{noun2} of the {noun}"
                    elif pattern == 'adj_noun_and' and len(noun_choices) > 1:
                        noun2 = pick(noun_choices)
                        adj2 = pick(adj_choices)
                        name = f"{adj} {noun} and {adj2} {noun2}"
                    elif pattern == 'noun_rising':
                        action = pick(['Rising', 'Ascending', 'Descending', 'Falling', 'Spiraling', 'Flowing'])
                        name = f"{noun} {action}"
                    else:
                        name = f"{adj} {noun}"
                else:
                    name = f"{adj} {noun}"
                
                if extra_used and extra:
                    name += f" {extra}"
                break
            tries += 1
    
    if not name:
        if multi_adj:
            adjs = random.sample(adjectives, 2)
            adj = f"{adjs[0]} {adjs[1]}"
        else:
            adj = pick(adjectives)
        noun = pick(nouns)
        
        # Apply alternate patterns for non-alliteration too
        if use_alternate:
            pattern = random.choice(['noun_of_adj', 'adj_noun_and', 'noun_rising'])
            if pattern == 'noun_of_adj':
                noun2 = pick(nouns)
                name = f"{noun2} of the {noun}"
            elif pattern == 'adj_noun_and':
                noun2 = pick(nouns)
                adj2 = pick(adjectives)
                name = f"{adj} {noun} and {adj2} {noun2}"
            elif pattern == 'noun_rising':
                action = pick(['Rising', 'Ascending', 'Descending', 'Falling', 'Spiraling', 'Flowing'])
                name = f"{noun} {action}"
            else:
                name = f"{adj} {noun}"
        else:
            name = f"{adj} {noun}"
        
        if extra_used:
            name += f" {pick(extras)}"

    max_length = 40
    tries = 0
    while len(name) > max_length and tries < 5:
        adj = pick(adjectives)
        noun = pick(nouns)
        name = f"{adj} {noun}"
        if random.random() < 0.4:
            name += f" {pick(extras)}"
        tries += 1

    # Grammar: randomly use 'The' or 'A/An' as the article if not already present
    words = name.split()
    if words and words[0].lower() not in ['the', 'of', 'from']:
        if random.random() < 0.5:
            name = f"The {name}"
        else:
            article = _a_or_an(words[0])
            name = f"{article.capitalize()} {name}"

    # DUPLICATE PREVENTION: Detect and remove obvious word duplicates
    words = name.split()
    seen_words = set()
    filtered_words = []
    
    # Track phrase patterns to prevent "of the of the" and "from the from the"
    seen_phrases = set()
    
    for i, word in enumerate(words):
        clean_word = word.lower().rstrip('.,!?:')
        
        # Check for repeated preposition+article phrases (e.g., "of the" appearing twice)
        if i > 0:
            prev_word = words[i-1].lower().rstrip('.,!?:')
            phrase = f"{prev_word} {clean_word}"
            if phrase in ['of the', 'from the', 'and the'] and phrase in seen_phrases:
                continue  # Skip repeated phrase patterns
            if phrase in ['of the', 'from the', 'and the']:
                seen_phrases.add(phrase)
        
        if clean_word not in seen_words and clean_word not in ['the', 'of', 'from', 'and', 'a', 'an']:
            seen_words.add(clean_word)
            filtered_words.append(word)
        elif clean_word in ['the', 'of', 'from', 'and', 'a', 'an']:
            # Always keep grammatical words (they'll be filtered by phrase logic above)
            filtered_words.append(word)
    name = ' '.join(filtered_words)

    # GRAMMAR FIX: Remove awkward preposition mixing
    name = name.replace(' of the from the', ' of the')
    name = name.replace(' from the of the', ' from the')
    name = name.replace(' of the of ', ' of the ')      # Fixes "of the of [word]"
    name = name.replace(' of the from ', ' of the ')    # Fixes "of the from [word]"
    name = name.replace(' from the from the', ' from the')

    # EDGE CASE FIX: Remove trailing prepositions (broken extras like "of the -")
    broken_endings = [' of the', ' from the', ' of', ' from', ' and', ' -']
    for ending in broken_endings:
        if name.endswith(ending):
            name = name[:-len(ending)].strip()

    # Ensure the suffix is always present
    name = ' '.join(name.split())
    if not name.endswith('- StarSound Generated Music Mod'):
        name += ' - StarSound Generated Music Mod'

    # Avoid duplicates in session
    global _recent_names
    tries = 0
    while name in _recent_names and tries < 10:
        adj = pick(adjectives)
        noun = pick(nouns)
        name = f"{adj} {noun}"
        if random.random() < 0.4:
            name += f" {pick(extras)}"
        # Grammar
        words = name.split()
        if words and words[0].lower() not in ['the', 'of', 'from']:
            article = _a_or_an(words[0])
            name = f"{article.capitalize()} {name}"
        name = ' '.join(name.split())
        if not name.endswith('- StarSound Generated Music Mod'):
            name += ' - StarSound Generated Music Mod'
        tries += 1
    _recent_names.append(name)
    if len(_recent_names) > _recent_max:
        _recent_names = _recent_names[-_recent_max:]
    return name
