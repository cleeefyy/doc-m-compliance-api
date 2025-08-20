# sanitizers.py
import re

_FSTR_PREFIX_RE = re.compile(r'(?P<prefix>\bf[ru]*)(?P<quote>["\'])', re.IGNORECASE)
_BRACED_EXPR_RE = re.compile(r'\{([^{}]+)\}')
_TRIPLE_QUOTE_RE = re.compile(r'([rubf]*)(\"\"\"|\'\'\')', re.IGNORECASE)

def strip_type_hints(py_code):
    py_code = re.sub(r'(\)\s*->\s*[^:]+):', r'):', py_code)
    def _strip_params(m):
        params = m.group(1)
        params = re.sub(r'(\b\w+\b)\s*:\s*[^,\)\n]+', r'\1', params)
        return '(' + params + ')'
    py_code = re.sub(r'\(([^)]*)\)', _strip_params, py_code)
    return py_code

def _convert_one_fstring(literal):
    if not literal or literal[0].lower() != 'f':
        return literal, False
    m = _FSTR_PREFIX_RE.match(literal)
    if not m:
        return literal, False
    prefix, quote = m.group('prefix'), m.group('quote')
    if literal.count(quote) < 2:
        return literal, False
    body = literal[len(prefix):]
    exprs = []
    idx = 0
    def repl(mobj):
        nonlocal idx
        expr = mobj.group(1).strip()
        exprs.append(expr)
        out = '{%d}' % idx
        idx += 1
        return out
    new_body = _BRACED_EXPR_RE.sub(repl, body)
    if exprs:
        return new_body + ".format(" + ", ".join(exprs) + ")", True
    return new_body, False

def convert_fstrings_to_format(py_code):
    lines = py_code.splitlines(True)
    out = []
    for ln in lines:
        if 'f"' not in ln and "f'" not in ln and 'f"""' not in ln and "f'''" not in ln:
            out.append(ln); continue
        if 'f"""' in ln or "f'''" in ln:
            ln = re.sub(r'\bf("""|\'\'\')', r'\1', ln)
        parts = []
        i = 0
        while i < len(ln):
            if i+1 < len(ln) and ln[i].lower() == 'f' and ln[i+1] in ("'", '"'):
                q = ln[i+1]
                j = i+2
                escaped = False
                while j < len(ln):
                    c = ln[j]
                    if c == '\\' and not escaped:
                        escaped = True; j += 1; continue
                    if c == q and not escaped:
                        j += 1
                        break
                    escaped = False
                    j += 1
                literal = ln[i:j]
                converted, ok = _convert_one_fstring(literal)
                parts.append(converted if ok else literal)
                i = j
            else:
                parts.append(ln[i])
                i += 1
        out.append(''.join(parts))
    return ''.join(out)

def enforce_py2_print_compat(py_code):
    py_code = re.sub(r'print\(([^,]+)\)', r'print \1', py_code)
    return py_code

def sanitize_for_ironpython(py_code):
    code = strip_type_hints(py_code)
    code = convert_fstrings_to_format(code)
    code = enforce_py2_print_compat(code)
    if re.search(r'(^|\W)f["\']', code):
        code = re.sub(r'\bf(?=["\'])', '', code)
    return code