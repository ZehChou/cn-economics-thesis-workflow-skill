"""一键运行：按 Phase 顺序执行全部脚本（对应附录 F.6 / H.8）。

lit_fetch.py 需联网（OpenAlex 官方接口）；无网络时可用 `python run_all.py --offline` 跳过，
此时复用已存在的 references/citation_db.json。
"""
import pathlib
import subprocess
import sys

OFFLINE = "--offline" in sys.argv

SCRIPTS = [
    ("lit_fetch.py", True),
    ("00_setup.py", False),
    ("01_describe.py", False),
    ("02_baseline.py", False),
    ("03_endogeneity.py", False),
    ("04_robustness.py", False),
    ("05_mechanism.py", False),
    ("06_heterogeneity.py", False),
    ("08_cite_replace.py", False),
    ("07_build_docx.py", False),
]

HERE = pathlib.Path(__file__).parent
failed, skipped = [], []

for name, needs_net in SCRIPTS:
    p = HERE / name
    if not p.exists():
        print(f"[SKIP] {name}（文件不存在）", flush=True)
        skipped.append(name)
        continue
    if needs_net and OFFLINE:
        print(f"[SKIP] {name}（离网模式，复用已有文献库）", flush=True)
        skipped.append(name)
        continue
    print(f"\n{'=' * 60}\n[RUN ] {name}\n{'=' * 60}", flush=True)
    rc = subprocess.run([sys.executable, str(p)], cwd=str(HERE.parent)).returncode
    if rc != 0:
        print(f"[FAIL] {name} 退出码 {rc}", flush=True)
        failed.append((name, rc))
    else:
        print(f"[OK  ] {name}", flush=True)

if failed:
    print("\n失败清单：", failed)
    sys.exit(1)
print(f"\n=== 全部脚本运行完成（跳过 {len(skipped)} 个）===")
