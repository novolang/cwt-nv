# Writes ../cwt_rfc8392_tests.nv from the text of RFC 8392 appendix A.
#
#   curl -sLo rfc8392.txt https://www.rfc-editor.org/rfc/rfc8392.txt
#   python3 -I gen_cwt_vectors.py rfc8392.txt
#   novo fmt ../cwt_rfc8392_tests.nv
#
# The hexadecimal blocks of the claims set (A.1), the keys (A.2.1 to A.2.3)
# and the signed (A.3), MACed (A.4) and encrypted (A.5) tokens are cut out of
# the RFC's text, so no byte of them was typed.
import os
import re
import sys

lines = open(sys.argv[1]).read().split("\n")


def block(heading):
    """The hexadecimal block that follows the first line starting with `heading`
    at or after the appendix, up to the first blank line."""
    start = next(i for i, l in enumerate(lines) if l.startswith(heading) and i > 900)
    i = start + 1
    while not re.match(r"^   [0-9a-f]{20,}", lines[i]):
        i += 1
    out = ""
    while re.match(r"^   [0-9a-f]+\s*$", lines[i]):
        out += lines[i].strip()
        i += 1
    return out


vectors = {
    "@CLAIMS@": block("A.1.  Example CWT Claims Set"),
    "@KEY128@": block("A.2.1.  128-Bit Symmetric Key"),
    "@KEY256@": block("A.2.2.  256-Bit Symmetric Key"),
    "@KEYEC@": block("A.2.3.  Elliptic Curve Digital Signature Algorithm"),
    "@SIGNED@": block("A.3.  Example Signed CWT"),
    "@MACED@": block("A.4.  Example MACed CWT"),
    "@ENCRYPTED@": block("A.5.  Example Encrypted CWT"),
}

here = os.path.dirname(os.path.abspath(__file__))
text = open(os.path.join(here, "cwt_rfc8392_template.nv")).read()
for k, v in vectors.items():
    text = text.replace(k, v)
open(os.path.join(here, "..", "cwt_rfc8392_tests.nv"), "w").write(text)
