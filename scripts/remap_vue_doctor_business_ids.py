# -*- coding: utf-8 -*-
"""将 Vue 静态医生列表中的 id 重写为 6 位工号：100000 + 顶层科室×100 + 科内序号（1..999）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def doctor_business_id(dept: int, seq: int) -> int:
    return 100_000 + dept * 100 + seq


def dept_for_sub_key(key: int) -> int:
    if 1 <= key <= 10 or key == 1001:
        return 1
    if 200 <= key <= 299:
        return 2
    if 10000 <= key < 11000:
        return key // 1000
    if 11000 <= key < 12000:
        return 11
    if 12000 <= key < 13000:
        return 12
    if 13000 <= key < 14000:
        return 13
    if 14000 <= key < 15000:
        return 14
    if 15000 <= key < 16000:
        return 15
    if 16000 <= key < 17000:
        return 16
    if 17000 <= key < 18000:
        return 17
    if 18000 <= key < 19000:
        return 18
    if 19000 <= key < 20000:
        return 19
    if 20000 <= key < 21000:
        return 20
    if 21000 <= key < 22000:
        return 21
    if 22000 <= key < 23000:
        return 22
    if 23000 <= key < 24000:
        return 23
    if 24000 <= key < 25000:
        return 24
    if 25000 <= key < 26000:
        return 25
    if 26000 <= key < 27000:
        return 26
    if 27000 <= key < 28000:
        return 27
    raise ValueError(f'无法从列表键 {key} 推断顶层科室 ID')


def extract_brace_block(s: str, open_brace: int) -> tuple[str, int]:
    depth = 0
    for i in range(open_brace, len(s)):
        if s[i] == '{':
            depth += 1
        elif s[i] == '}':
            depth -= 1
            if depth == 0:
                return s[open_brace + 1 : i], i
    raise ValueError('大括号不匹配')


def replace_ids_in_body(body: str, dept: int, seq_by_dept: dict[int, int]) -> str:
    def repl(m: re.Match[str]) -> str:
        seq_by_dept[dept] = seq_by_dept.get(dept, 0) + 1
        seq = seq_by_dept[dept]
        if seq > 999:
            raise ValueError(f'科室 {dept} 序号超过 999')
        return m.group(1) + str(doctor_business_id(dept, seq))

    return re.sub(r'(\{\s*id:\s*)\d+', repl, body)


def remap_object_inner(inner: str, seq_by_dept: dict[int, int], specialty_all_dept1: bool) -> str:
    parts: list[str] = []
    pos = 0
    n = len(inner)
    while pos < n:
        m = re.search(r'\s*(\d+):\s*\[', inner[pos:])
        if not m:
            parts.append(inner[pos:])
            break
        abs_m0 = pos + m.start()
        abs_m1 = pos + m.end()
        parts.append(inner[pos:abs_m0])
        key = int(m.group(1))
        start = abs_m1
        depth = 1
        j = start
        while j < n and depth:
            if inner[j] == '[':
                depth += 1
            elif inner[j] == ']':
                depth -= 1
            j += 1
        body = inner[start : j - 1]
        dept = 1 if specialty_all_dept1 else dept_for_sub_key(key)
        new_body = replace_ids_in_body(body, dept, seq_by_dept)
        parts.append(inner[abs_m0:abs_m1])
        parts.append(new_body)
        parts.append(']')
        pos = j
    return ''.join(parts)


def patch_file(path: Path, seq_by_dept: dict[int, int]) -> None:
    text = path.read_text(encoding='utf-8')
    for label, specialty_mode in (
        ('subDepartmentDoctors:', False),
        ('specialtyDoctors:', True),
    ):
        idx = text.find(label)
        if idx < 0:
            continue
        brace = text.find('{', idx)
        if brace < 0:
            continue
        inner, close_i = extract_brace_block(text, brace)
        new_inner = remap_object_inner(inner, seq_by_dept, specialty_mode)
        text = text[: brace + 1] + new_inner + text[close_i:]
    path.write_text(text, encoding='utf-8')


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    for rel in ('src/views/AppointmentDoctor.vue', 'src/views/Appointment.vue'):
        p = root / rel
        if not p.exists():
            print('skip missing', p, file=sys.stderr)
            continue
        # 每个页面独立编号，避免先处理的大文件占用序号导致另一页工号偏离 100101 起点
        seq_by_dept: dict[int, int] = {}
        patch_file(p, seq_by_dept)
        print('patched', p, 'per-dept max:', dict(sorted(seq_by_dept.items())))


if __name__ == '__main__':
    main()
