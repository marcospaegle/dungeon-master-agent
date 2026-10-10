# Chapter 4: Unicode Text Versus Bytes

## Core Idea
"Humans use text. Computers speak bytes." Python 3 enforces a strict `str` (code points) vs `bytes` (raw 0-255) divide; correctness comes from explicit encodings, decoding early and encoding late, and normalizing before comparing.

## Frameworks Introduced
- **Unicode sandwich**: decode bytes to `str` as early as possible on input; keep the business logic on `str` only; encode to bytes as late as possible on output.
  - When to use: all text I/O.
  - How: `open(path, encoding='utf_8')` in text mode does decoding/encoding for you; never encode/decode mid-processing.
  - Failure mode: relying on default encodings produces files that differ per platform (Windows cp1252 reads UTF-8 `café` as `cafÃ©`).
- **Always pass `encoding=` explicitly**: "do not rely on defaults". Most important default: `locale.getpreferredencoding()` (files, and redirected stdout).
- **Error-handler choice** (`errors=`): `strict` (default, raises), `ignore` (silent data loss, usually bad), `replace` (`?` on encode, U+FFFD on decode), `xmlcharrefreplace` (only lossless non-UTF option when encoding). Extensible via `codecs.register_error`.
- **Normalize-before-compare** ladder:
  1. NFC for equality (canonical equivalents; W3C-recommended; normalize user text before saving).
  2. `normalize('NFC', s).casefold()` for case-insensitive compare.
  3. NFKC/NFKD only for search/indexing (lossy).
  4. Diacritic stripping / asciizing only as a deliberate, language-aware last resort.
- **Sorting ladder**: default code-point sort is wrong for non-ASCII -> `locale.strxfrm` after `setlocale(LC_COLLATE, ...)` (global, OS-dependent) -> `pyuca.Collator().sort_key` (UCA, portable, not locale-aware) -> PyICU (language-specific rules).

## Key Concepts
- **Code point**: number U+0000 to U+10FFFF identifying a character; independent of bytes.
- **Encoding**: algorithm mapping code points to bytes (`str.encode`) and back (`bytes.decode`).
- **bytes / bytearray**: immutable / mutable sequences of ints 0-255; `b[0]` is an int, `b[:1]` is bytes; no `format`, `casefold`, `isdecimal`, `encode`...; `bytes.fromhex`.
- **Buffer protocol**: constructing `bytes(array)` copies; `memoryview` shares.
- **Codec families**: latin1 (basis of cp1252 and Unicode), cp1252 (Microsoft superset), cp437, gb2312, utf-8 (variable, no endianness), utf-16 (surrogate pairs).
- **Mojibake / gremlins**: garbled text from wrong 8-bit codec; cp1252/latin1/koi8_r decode any bytes silently, UTF-8 usually raises.
- **BOM**: U+FEFF at start; `\xff\xfe` means little-endian UTF-16; `utf_16le/be` emit none; `utf-8-sig` = UTF-8 with BOM (`\xef\xbb\xbf`).
- **Canonical equivalents**: `'é'` vs `'é'`; NFC composes, NFD decomposes.
- **Compatibility characters**: `µ`, `½`, `4²`; NFKC/NFKD replace them with preferred forms (may change meaning).
- **Case folding**: `str.casefold()` = lowercase plus extras (`ß` -> `ss`, `µ` -> `μ`); ~300 code points differ from `lower()`.
- **Dual-mode API**: functions accepting `str` or `bytes` and behaving differently (`re`, `os`).

## Mental Models
- `.encode()` produces cryptic bytes for storage/transmission; `.decode()` produces human text.
- You cannot detect an encoding from bytes alone ("you must be told"): use headers/metadata; heuristics (Chardet) or "try UTF-8, fall back to cp1252" (UTF-8 rarely decodes garbage by accident).
- Read UTF-8 with `utf-8-sig` (harmless, tolerates BOM); write plain `utf-8` (BOM breaks `#!` shebangs).
- Use binary mode only for binary files; for unknown text use Chardet rather than reinventing.
- Linux/macOS: UTF-8 everywhere; Windows: several mutually incompatible defaults (stdout is UTF-8 on a console but locale encoding when redirected).

## Anti-patterns
- **`open('f.txt')` without encoding**: platform-dependent bytes.
- **`errors='ignore'`**: silent data loss.
- **`==` on unnormalized Unicode**: visually identical strings compare unequal.
- **NFKC for permanent storage**: lossy (`4²` -> `42`).
- **`sorted()` on accented text / `locale.setlocale` inside a library**: wrong order; locale is process-global.
- **Treating 1 char == 1 byte**, or slicing Unicode text arbitrarily (combining marks, emoji sequences).
- **Using `\N{}`-less magic hex** in source for special chars: prefer `'\N{INFINITY}'` (SyntaxError if the name is wrong).
- **Changing `sys.getdefaultencoding()`**: unsupported.

## Code Examples
```python
>>> s1 = 'café'
>>> s2 = 'cafe\N{COMBINING ACUTE ACCENT}'
>>> len(s1), len(s2), s1 == s2
(4, 5, False)

from unicodedata import normalize

def nfc_equal(str1, str2):
    return normalize('NFC', str1) == normalize('NFC', str2)

def fold_equal(str1, str2):
    return (normalize('NFC', str1).casefold() ==
            normalize('NFC', str2).casefold())
```
- **What it demonstrates**: canonical equivalence and the two utility comparators.

```python
def shave_marks(txt):
    """Remove all diacritic marks"""
    norm_txt = unicodedata.normalize('NFD', txt)
    shaved = ''.join(c for c in norm_txt
                     if not unicodedata.combining(c))
    return unicodedata.normalize('NFC', shaved)
```
- **What it demonstrates**: decompose, filter combining marks, recompose. `shave_marks_latin` only strips marks whose base char is in `string.ascii_letters` (keeps Greek accents); `asciize` adds `str.translate` maps (`dewinize`) and `ß` -> `ss`.

```python
import pyuca
coll = pyuca.Collator()
sorted(fruits, key=coll.sort_key)   # ['açaí', 'acerola', 'atemoia', 'cajá', 'caju']
```

```python
def find(*query_words, start=START, end=END):
    query = {w.upper() for w in query_words}
    for code in range(start, end):
        char = chr(code)
        name = unicodedata.name(char, None)
        if name and query.issubset(name.split()):
            print(f'U+{code:04X}\t{char}\t{name}')
```
- **What it demonstrates**: `cf.py` character finder using set `issubset` on name words.

## Reference Tables
| Setting | Controls |
|---|---|
| `locale.getpreferredencoding()` | default for `open()` text and redirected std streams |
| `sys.stdout/stdin/stderr.encoding` | UTF-8 for interactive (3.6+ Windows), locale if redirected |
| `sys.getdefaultencoding()` | internal implicit conversions; do not change |
| `sys.getfilesystemencoding()` | filenames (not contents); `bytes` paths bypass it |

| Normalization | Does | Use |
|---|---|---|
| NFC | compose, shortest | default for comparison/storage |
| NFD | decompose | base for stripping marks |
| NFKC/NFKD | + compatibility decomposition | search/indexing only |

Regex: `str` patterns `\d \w` match Unicode (use `re.ASCII` to restrict); `bytes` patterns match ASCII only. `os` functions: `str` arg -> `str` results decoded with filesystem encoding; `bytes` arg -> `bytes` results; helpers `os.fsencode/fsdecode`.

## Worked Example
`octets = b'Montr\xe9al'`: decode as `cp1252` -> `'Montréal'`; as `iso8859_7` -> `'Montrιal'` and `koi8_r` -> `'MontrИal'` with no error (silent mojibake); as `utf_8` -> `UnicodeDecodeError`; with `errors='replace'` -> `'Montr�al'` (U+FFFD). Lesson: legacy 8-bit codecs never complain, UTF-8 does.

## Key Takeaways
1. `str` is text (code points); `bytes` is data; convert only at the boundaries (Unicode sandwich).
2. Specify `encoding=` on every text `open()`; never trust defaults.
3. Identify the exact exception (`UnicodeEncodeError`, `UnicodeDecodeError`, `SyntaxError` for source) before fixing.
4. Normalize to NFC (and `casefold`) before comparing; reserve NFKC and diacritic stripping for search.
5. Sort human text with a collation algorithm (`pyuca`/PyICU), not code points.
6. Dual-mode APIs: `bytes` in -> `bytes` out; `bytes` regexes are ASCII-only.
7. Mind BOMs: read with `utf-8-sig`, write `utf-8`.

## Connects To
- **Ch 2**: memoryview, bytes/bytearray as flat sequences, `sorted(key=)`.
- **Ch 3**: sets and dicts used in the character finder.
- **Ch 5**: next chapter on data class builders.
- **Ch 12/ Ch 16**: Unicode in `__format__`/`__bytes__` examples.
- **Ch 21**: async I/O where text streams show up.
