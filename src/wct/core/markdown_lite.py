from __future__ import annotations

import re


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"\*([^*]+)\*")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _inline(text: str) -> str:
    text = _esc(text)
    text = _INLINE_CODE.sub(r"<code>\1</code>", text)
    text = _BOLD.sub(r"<b>\1</b>", text)
    text = _ITALIC.sub(r"<i>\1</i>", text)
    text = _LINK.sub(r'<a href="\2" style="color:#5cd0ff;">\1</a>', text)
    return text


def render(md: str) -> str:
    out: list[str] = []
    in_list = False
    in_code = False
    code_buf: list[str] = []

    for raw in md.splitlines():
        line = raw.rstrip()

        if line.startswith("```"):
            if in_code:
                out.append(
                    '<pre style="background:#0d1428;border:1px solid #1c2945;'
                    'border-radius:8px;padding:10px;color:#c0c8d8;font-family:Consolas,Menlo,monospace;font-size:12px;">'
                    + "\n".join(_esc(c) for c in code_buf)
                    + "</pre>"
                )
                code_buf = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_buf.append(raw)
            continue

        m = _HEADING_RE.match(line)
        if m:
            if in_list:
                out.append("</ul>")
                in_list = False
            level = len(m.group(1))
            text = _inline(m.group(2))
            size = {1: 22, 2: 18, 3: 16, 4: 14, 5: 13, 6: 12}.get(level, 14)
            out.append(
                f'<div style="font-size:{size}px;font-weight:700;color:#e6ecf5;'
                f'margin-top:14px;margin-bottom:6px;">{text}</div>'
            )
            continue

        if line.startswith("- ") or line.startswith("* "):
            if not in_list:
                out.append('<ul style="margin:4px 0;padding-left:22px;color:#c0c8d8;">')
                in_list = True
            out.append(f"<li>{_inline(line[2:])}</li>")
            continue

        if not line:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<br/>")
            continue

        out.append(
            f'<div style="color:#c0c8d8;margin:2px 0;line-height:1.5;">{_inline(line)}</div>'
        )

    if in_list:
        out.append("</ul>")
    if in_code and code_buf:
        out.append("<pre>" + "\n".join(_esc(c) for c in code_buf) + "</pre>")

    return "\n".join(out)


def strip(md: str) -> str:
    text = re.sub(r"```.*?```", "", md, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    return text.strip()


def summary(md: str, length: int = 160) -> str:
    plain = strip(md)
    plain = " ".join(plain.split())
    if len(plain) <= length:
        return plain
    return plain[: length - 1].rsplit(" ", 1)[0] + "\u2026"
