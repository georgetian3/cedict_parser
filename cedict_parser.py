import re
import json

def mark_tone(word):

    if word[-1].isalpha() or word in [',', '·']:
        return word
    if word[-1] == '5':
        return word[:-1]

    tone = int(word[-1]) - 1
    word = word[:-1].replace('u:', 'ü')

    tones = {
        'a': 'āáǎà', 'A': 'ĀÁǍÀ',
        'e': 'ēéěè', 'E': 'ĒÉĚÈ',
        'i': 'īíǐì', 'I': 'ĪÍǏÌ',
        'o': 'ōóǒò', 'O': 'ŌÓǑÒ',
        'u': 'ūúǔù', 'ü': 'ǖǘǚǜ'
    }
    
    for vowel in ['a', 'A', 'e', 'E', 'Ou', 'ou']:
        if vowel in word:
            return word.replace(vowel[0], tones[vowel[0]][tone])

    for char in word[::-1]:
        if char in tones:
            return word.replace(char, tones[char][tone])        

    return word

def download_cedict(filename):
    from zipfile import ZipFile
    from io import BytesIO
    import requests

    file = ZipFile(BytesIO(requests.get('https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip').content)).open('cedict_ts.u8').read()

    with open(filename, 'wb') as f:
        f.write(file)

def parse_cedict(filename):
    
    with open(filename, encoding = 'utf8') as f:
        lines = f.readlines()

    cedict = {}

    for line in lines:
        # ignoring commented and empty lines
        if line[0] == '#' or line == '':
            continue
        # getting the simplified word
        word = re.search(r'^[^ ]+ ([^ ]+) \[', line).group(1)
        # converting pinyin tone marks from numeric to accents
        pinyin = ' '.join([mark_tone(x) for x in re.search(r'^[^\[]+\[([^\]]+)', line).group(1).split()])
        # creating a set of definitions using the / delimiter
        definitions = set(re.search(r'^[^\]]+\] /(.+)/', line).group(1).split('/'))

        for definition in definitions.copy():
            # removing definitions that say the word is a variant of itself, and definitions that purely give the word's Taiwanese pronunciation
            if 'variant of' in definition and word in definition or definition[:11] == 'Taiwan pr. ':
                definitions.remove(definition)
                continue
            new_definition = definition
            def_cache = ''
            while def_cache != new_definition:
                def_cache = new_definition
                # removing Taiwanese pronunciation in brackets
                new_definition = re.sub(r'\(Taiwan pr.[^\)]*\)', '', new_definition)
                # removing traditional
                pattern = re.search(r'[^\| :]+\|([^ \[]+)', new_definition)
                if pattern:
                    new_definition = new_definition.replace(pattern.group(0), pattern.group(1))
                # removing pinyin unless string contains 'also pr.', in which case format pinyin
                if new_definition[:8] == 'also pr.':
                    pinyin_raw = re.search(r'\[([^\]]+)\]', new_definition)
                    if pinyin_raw:
                        pinyin = ' '.join([mark_tone(x) for x in pinyin_raw.group(1).split()])
                        new_definition = new_definition.replace(pinyin_raw.group(0), pinyin)
                else:
                    new_definition = re.sub(r'\[[^\]]+\]', '', new_definition)
                # fixing spacing after punctuation
                new_definition = re.sub(r':([^\s])', r': \1', new_definition)
                new_definition = re.sub(r',([^\s])', r', \1', new_definition)

            # replace definition if it was changed
            if new_definition != definition:
                definitions.remove(definition)
                definitions.add(new_definition)

        if not definitions:
            continue
        
        # adding the new entry to dictionary
        if word in cedict:
            if pinyin in cedict[word]:
                for existing_definitions in cedict[word][pinyin]:
                    definitions -= existing_definitions
                if len(definitions) != 0:
                    cedict[word][pinyin].append(definitions)
            else:
                cedict[word][pinyin] = [definitions]
        else:
            cedict[word] = {pinyin: [definitions]}

    for word in cedict:
        for pinyin in cedict[word]:
            cedict[word][pinyin] = ['; '.join(x) for x in cedict[word][pinyin]]

    with open(f'{filename.split(".")[0]}.json', 'w', encoding = 'utf8') as f:
        json.dump(cedict, f, ensure_ascii = False, indent = 4)

if __name__ == '__main__':
    filename = 'cedict.txt'
    download_cedict(filename)
    parse_cedict(filename)