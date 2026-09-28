# P15 V0.1.13 RELEASE PAYLOAD MANIFEST

日期：2026-09-28
轮次：F-RP-02 / F-RP-05 FOUNDATION RESOLUTION（HD-FRP-FOUNDATION-01）
Parent baseline：`a238e85710fe7f13796a89cae8816bbd1ebbfca8`（0.1.12 · immutable）
Tag candidate（本阶段未创建）：`UAP-V0.1.13-P15-EVENT-CONSUMER`
Hash：SHA-256（全部为当前工作区实测值）

```text
Payload total = 13
  CONTRACT ALIGNMENT     = 1
  TEST                   = 1
  DOCUMENTATION BASELINE = 1
  GOVERNANCE             = 1
  CONTRACT (docs)        = 1
  RELEASE EVIDENCE       = 4
  RELEASE METADATA       = 3
  MANIFEST (self)        = 1
```

---

## 1. Payload Table

| Path | Classification | SHA256 | Reason |
|---|---|---|---|
| `core/event/interfaces.py` | CONTRACT ALIGNMENT | `afd5ce7b7104c694235cf39092953f43161583c4d868b8b1726eec6ddec4c67c` | D-P10-02 / D-AUTH-22 实施落地：`_new_id()` 委托 `new_event_id()`（UUIDv7）；`tenant_id: str \| None = None`；docstring 记录 EventBus != Outbox |
| `tests/architecture/test_event_contract_alignment.py` | TEST | `4da189e264edba829c2b95678466d43e9cbe5715692481d62a0ae7708c1835f4` | 9 项对齐守卫：canonical generator / 无 uuid4 / tenant-scoped / platform-scoped / NULL ≠ 授权旁路 / actor provenance |
| `docs/architecture/DEPENDENCY_RULES.md` | DOCUMENTATION BASELINE | `ba82fde57f9bc183e98579e00e1dd6644e8750fb52fc9dd28dcabf3ed48afe78` | 仅恢复 D-P10-17 Carrier faces 段（+24 / −0）；不含 AGENT_RUNTIME §9；不改写 P09 状态块 |
| `docs/architecture/PLATFORM_DECISION_LOG.md` | GOVERNANCE | `58e3ec09bd881324de07acc215a5268c532bcb959061fd7f9c5c88061c95bd40` | 追加附录 U（append-only · 附录 A–T 零改写） |
| `docs/architecture/P15_EVENT_CONTRACT_ALIGNMENT.md` | CONTRACT (docs) | `24d955592f50d9edc527031130ae3ead39555f3a614fec1432b836763c096dda` | Event identity / tenant 语义 / platform scope / 可追溯性矩阵 |
| `docs/architecture/P15_FOUNDATION_RESOLUTION_REPORT.md` | RELEASE EVIDENCE | `03e158b9e43b3c90787d4cefb0827b5e6a28c9017ff024da3bb2bcda3db2c178` | 本轮主报告：变更、Before/After、闭包、安全/DB/迁移、发布状态 |
| `docs/architecture/P15_WAVE1_BASELINE_CLOSURE.md` | RELEASE EVIDENCE | `db7631ad0bed02c4681ca3cdf8701b0b4831a0c067e81160dfc3630ec9f0db68` | Wave 1 基线冻结（committed clean clone）+ F-RP-05 关闭证据 |
| `docs/architecture/F_RP_05_F_RP_02_FOUNDATION_DECISION_PACKAGE.md` | RELEASE EVIDENCE | `ec7e660f4584c4c246cd78dc942dacd5f85d8eea20bd2a0d28623a214b127f3b` | 决策前事实包（含 §19 Human Decision 追加登记） |
| `docs/architecture/P15_F_RP_05_RESOLUTION_REPORT.md` | RELEASE EVIDENCE | `c2ba10f47c9aa7f197970810e4a5a66ceea9dfbb8ef2e12d0692fae261edf6b1` | F-RP-05 取证报告（含 §16 / §17 append-only 追加） |
| `pyproject.toml` | RELEASE METADATA | `b63883c78e529a849be53ecabe6d13d5c231fcbe2e1461e408d890e699ac5f49` | 版本 0.1.12 → 0.1.13（仅 version 字段） |
| `config/settings.py` | RELEASE METADATA | `6c35f04d5174686402084b75d90566783f6e7cc4e8c200c860011abf25c7cf4a` | 版本 0.1.12 → 0.1.13（仅 APP_VERSION 默认值） |
| `docker-compose.yml` | RELEASE METADATA | `d9693c884ef585d0bdb7fb78cd1eecf3620292fa628bbf837737cc54f5fac39f` | 版本 0.1.12 → 0.1.13（仅 APP_VERSION） |
| `docs/architecture/P15_V0_1_13_RELEASE_PAYLOAD_MANIFEST.md` | MANIFEST (self) | `自引用（self-hash field excluded from canonical hash set）` | 本 payload manifest（见 §3） |

---

## 2. 双向完整性

```text
missing    = 0
orphan     = 0
unresolved = 0
deleted    = 0
excluded leakage = 0
candidate index simulation vs manifest = exact match
real staged = 0
```

---

## 3. SELF-HASH RULE

```text
本 manifest 对自身行不写入 SHA256（该字段值为说明性文字）。
canonical hash set = 携带 64-hex SHA256 的行 = 12 = 行总数 − 1
校验：逐行重算 sha256(磁盘文件) 必须全部相等；
      manifest 自身完整性由 git commit object 背书。
```

---

## 4. 边界不变量（本 payload 自证）

```text
schema mutation = 0 · migration mutation = 0 · 0018+ = 0 · revision 文件 = 17
role / grant / revoke / ACL / subject vocabulary = 0
P15 production implementation（kernel / claim / worker / apps/worker/main.py）= 0 改动
P15 production allowlist = EMPTY · production handlers = 0
未纳入：tests/conftest.py · infrastructure/database/__init__.py（F-RP-02 remaining）
        AGENT_RUNTIME future scope · P09 status block 重写 · historical dirty · BATCH-D
```

**END OF P15 V0.1.13 RELEASE PAYLOAD MANIFEST**
