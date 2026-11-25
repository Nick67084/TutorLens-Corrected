"""Normalize explicit PDF references without inventing evidence."""
import re

_CODE = re.compile(r'(```[\s\S]*?(?:```|\Z)|~~~[\s\S]*?(?:~~~|\Z)|`[^`\n]*`)')
_REF = re.compile(r'\[(?:references?\s*:\s*)?(?:pp?\.?\s*|pages?\s+)(\d+(?:\s*(?:[,;–—-]|\bto\b)\s*(?:pp?\.?\s*|pages?\s+)?\d+)*)\](?!\()', re.I)

def normalize(answer):
    def replace(m):
        numbers = re.findall(r'\d+', m[1]); pages = [int(numbers[0])]
        for sep, number in re.findall(r'([,;–—-]|\bto\b)\s*(?:pp?\.?\s*|pages?\s+)?(\d+)', m[1], re.I):
            n = int(number)
            if sep in ('-', '–', '—', 'to'):
                if n < pages[-1] or n-pages[-1] > 100: return m[0]
                pages.extend(range(pages[-1]+1,n+1))
            else: pages.append(n)
        return ' '.join(f'[p.{p}]' for p in dict.fromkeys(pages))
    parts = _CODE.split(answer)
    for i in range(0,len(parts),2):
        parts[i] = _REF.sub(replace,parts[i])
        parts[i] = re.sub(r'\[\[(https?://[^\s\]]+)\]\(\1\)\]',r'<\1>',parts[i])
    return ''.join(parts)

def cited_pages(answer):
    return {int(n) for i,p in enumerate(_CODE.split(normalize(answer))) if i%2==0 for n in re.findall(r'\[p\.(\d+)\]',p)}
