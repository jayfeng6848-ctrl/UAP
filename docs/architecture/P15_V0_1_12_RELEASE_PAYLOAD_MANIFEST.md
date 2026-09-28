# P15 V0.1.12 RELEASE PAYLOAD MANIFEST

日期：2026-09-28
轮次：P15 RELEASE CORRECTION（corrective release）
Parent baseline：`dc44c9939d7708b68e5b461a7ccb6684588d1106`（P15 0.1.11 · RELEASE-BLOCKED）
Tag candidate：`UAP-V0.1.12-P15-EVENT-CONSUMER`
Hash：SHA-256（全部为当前工作区实测值）

```text
Payload total = 9
  TEST INFRASTRUCTURE        = 2
  RELEASE METADATA           = 3
  RELEASE EVIDENCE           = 4
```

> 本 manifest **不是** 0.1.11 payload 的替代或修订。
> `P15_RELEASE_PAYLOAD_MANIFEST.md`（0.1.11）保持历史原状，附录其失败结论。

---

## 1. Payload Table

### 1.1 TEST INFRASTRUCTURE（2）

| Path | Classification | Ownership | SHA256 | Reason |
|---|---|---|---|---|
| `tests/integration/runtime_testkit.py` | TEST INFRASTRUCTURE | P15 CORRECTION | `4eb29975db7596cfebf0acf9316e621d4639d75d6503ac3e5eb467729449766d` | F-RP-04 · 被 10 个已提交测试模块 import 的 runtime DSN testkit（P14 既有 · 非业务语义） |
| `tests/architecture/test_p10_event_audit_boundary.py` | TEST INFRASTRUCTURE | P15 CORRECTION | `840709fd323ddf27301c9ff77c91c1f8769f0699f0f3fa8d5a3deed8ce3c5d66` | F-RP-04 · Wave 1 allowlist 成员 · P10 五载体边界守卫（静态扫描 · 无生产语义） |

### 1.2 RELEASE METADATA（3）

| Path | Classification | Ownership | SHA256 | Reason |
|---|---|---|---|---|
| `pyproject.toml` | RELEASE METADATA | P15 CORRECTION | `375f61596f60e95e9e15bd5e63a2b0841163c6205c718c4f7f1d3d8d9a84f053` | 版本元数据 0.1.11 → 0.1.12（仅 `version` 字段） |
| `config/settings.py` | RELEASE METADATA | P15 CORRECTION | `a57144e3b5a329fa09ae490719df0d0ad9f51ea5bfa496f61debed9a05e36325` | 版本元数据 0.1.11 → 0.1.12（仅 `APP_VERSION` 默认值） |
| `docker-compose.yml` | RELEASE METADATA | P15 CORRECTION | `76fa5a7c0de788d7b80eefb6180c3b807527c2a2c615f38e3ee33093b612f25f` | 版本元数据 0.1.11 → 0.1.12（仅 `APP_VERSION`） |

### 1.3 RELEASE EVIDENCE（4）

| Path | Classification | Ownership | SHA256 | Reason |
|---|---|---|---|---|
| `docs/architecture/P15_REMOTE_PUSH_RECORD.md` | RELEASE EVIDENCE | P15 CORRECTION | `02a52ae389f330c5aa520c5bdbccb165250f21454ff6d77db6ef98c1bb2e0697` | 0.1.11 post-release failure evidence（push 成功 · 验证失败 · RELEASE-BLOCKED） |
| `docs/architecture/P15_CLEAN_CLONE_DEPENDENCY_AUDIT.md` | RELEASE EVIDENCE | P15 CORRECTION | `9716f9470a7fbb13082bced1a472ed2cdfe29bb484f714cc0052eca12759ac6c` | clean-clone 依赖审计（tracked → untracked / 引用 / 分类 / 纯净树实测） |
| `docs/architecture/P15_RELEASE_CORRECTION_REPORT.md` | RELEASE EVIDENCE | P15 CORRECTION | `e5e371aaa3ff47a04abe07058c5380bc4baed1435eb106360bb0c56ab85bf785` | corrective release 报告（F-RP-04 CLOSED · F-RP-05 OPEN · 实测数据） |
| `docs/architecture/P15_V0_1_12_RELEASE_PAYLOAD_MANIFEST.md` | RELEASE EVIDENCE | P15 CORRECTION | `自引用（self-hash field excluded from canonical hash set）` | 本 payload manifest（自引用 · 见 §3） |

---

## 2. 双向完整性（§32）

```text
A — Ownership → Manifest：本 corrective payload 的全部路径均已登记
B — Manifest → Ownership：每条 path 均有 ownership 证据与 reason

missing    = 0
orphan     = 0
unresolved = 0
candidate index simulation vs manifest = exact match
```

---

## 3. SELF-HASH RULE

```text
SELF-HASH RULE（沿用 0.1.11 manifest 规则）=
  本 manifest 对**自身行**不写入 SHA256；该字段值为说明性文字。
  即 self-hash field is EXCLUDED from the canonical hash set。
  ⇒ 不存在 SHA256(full file) == embedded SHA256 这种数学自引用断言。

canonical hash set = 携带 64 位十六进制 SHA256 的行
  |canonical hash set| = 行总数 − 1 = 8
  校验方式（独立可复现）：
    1. 统计 64-hex SHA256 行数 ⇒ 必须等于 8
    2. 逐行重算 sha256(磁盘文件) ⇒ 必须全部相等
    3. manifest 自身完整性由 git commit object / annotated tag 背书
```

---

## 4. Revision / Scope 保护

```text
新建 Alembic revision = 0（0018+ = 0 · revision 文件 17）
P15 production implementation（kernel / claim / worker / apps/worker/main.py）改动 = 0
schema change = 0 · grant / revoke / role / principal 改动 = 0
Production allowlist = EMPTY · Production handlers = 0
```

---

## 5. Exclusion（未纳入 · 逐类说明）

```text
F-RP-02 residual（3）        tests/conftest.py · core/event/interfaces.py ·
                             infrastructure/database/__init__.py        → DO NOT FIX（保护）
BATCH-D maintenance（16）    含 scripts/generate_build_info.py ·
                             tests/unit/test_generate_build_info.py     → NOT STAGED（保护）
historical dirty（13）       含 docs/architecture/DEPENDENCY_RULES.md   → 未提交修改保持原状
DENY 面未跟踪测试（3）        test_p10_event_audit_schema / test_p11_triggers /
                             test_p12_indexes                           → OPTIONAL（非 release 必需）
handoff 包（17）· 非 P15 历史文档（81）· __pycache__/pyc（36）          → NOT REQUIRED
```

```text
本 payload 未从任何被排除文件吸收内容（excluded leakage = 0）
```

---

## 6. Candidate 形态（隔离临时 index 实测）

```text
Files Added    = 6
Files Modified = 3
Files Deleted  = 0
Payload total  = 9
real staged    = 0（真实 index 未被使用）
```

**END OF P15 V0.1.12 RELEASE PAYLOAD MANIFEST**
