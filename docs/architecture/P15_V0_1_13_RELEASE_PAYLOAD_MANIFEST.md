# P15 V0.1.13 RELEASE PAYLOAD MANIFEST

日期：2026-09-28
轮次：F-RP-02 / F-RP-05 FOUNDATION RESOLUTION（HD-FRP-FOUNDATION-01）
Parent baseline：`a238e85710fe7f13796a89cae8816bbd1ebbfca8`（0.1.12 · immutable）
Tag candidate（本阶段未创建）：`UAP-V0.1.13-P15-EVENT-CONSUMER`
Hash：SHA-256 · **Hash Basis = committed Git blob bytes**（禁止以 Windows 工作区渲染为基准）

> **Amendment 0.1.14（2026-09-28 · F-RP-06）**
> 本 manifest 原为 0.1.13 candidate 的 payload 记录。0.1.14 修正其中 1 条哈希基准错误
> （`docs/architecture/DEPENDENCY_RULES.md`：工作区渲染 → committed blob），
> 将 3 条版本元数据行推进到 0.1.14 的 canonical 值，并补登 0.1.14 新增产物（见 §1.4）。
> 0.1.13 commit `5244b5916e51eebc958bb3f844dbc579d66014f3` 及其内容保持不可变历史。

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

0.1.14 CORRECTIVE ADDITIONS = 2（RELEASE EVIDENCE · 见 §1.4）
```

---

## 1. Payload Table

| Path | Classification | SHA256 | Reason |
|---|---|---|---|
| `core/event/interfaces.py` | CONTRACT ALIGNMENT | `afd5ce7b7104c694235cf39092953f43161583c4d868b8b1726eec6ddec4c67c` | D-P10-02 / D-AUTH-22 实施落地：`_new_id()` 委托 `new_event_id()`（UUIDv7）；`tenant_id: str \| None = None`；docstring 记录 EventBus != Outbox |
| `tests/architecture/test_event_contract_alignment.py` | TEST | `4da189e264edba829c2b95678466d43e9cbe5715692481d62a0ae7708c1835f4` | 9 项对齐守卫：canonical generator / 无 uuid4 / tenant-scoped / platform-scoped / NULL ≠ 授权旁路 / actor provenance |
| `docs/architecture/DEPENDENCY_RULES.md` | DOCUMENTATION BASELINE | `5bf516f5cf03ce1d37b195e7fb4d63663ff85cbebaa82719d5f9c5f6393c5220` | 仅恢复 D-P10-17 Carrier faces 段（+24 / −0）；不含 AGENT_RUNTIME §9；不改写 P09 状态块（0.1.14 修正哈希基准 · F-RP-06） |
| `docs/architecture/PLATFORM_DECISION_LOG.md` | GOVERNANCE | `58e3ec09bd881324de07acc215a5268c532bcb959061fd7f9c5c88061c95bd40` | 追加附录 U（append-only · 附录 A–T 零改写） |
| `docs/architecture/P15_EVENT_CONTRACT_ALIGNMENT.md` | CONTRACT (docs) | `24d955592f50d9edc527031130ae3ead39555f3a614fec1432b836763c096dda` | Event identity / tenant 语义 / platform scope / 可追溯性矩阵 |
| `docs/architecture/P15_FOUNDATION_RESOLUTION_REPORT.md` | RELEASE EVIDENCE | `03e158b9e43b3c90787d4cefb0827b5e6a28c9017ff024da3bb2bcda3db2c178` | 本轮主报告：变更、Before/After、闭包、安全/DB/迁移、发布状态 |
| `docs/architecture/P15_WAVE1_BASELINE_CLOSURE.md` | RELEASE EVIDENCE | `db7631ad0bed02c4681ca3cdf8701b0b4831a0c067e81160dfc3630ec9f0db68` | Wave 1 基线冻结（committed clean clone）+ F-RP-05 关闭证据 |
| `docs/architecture/F_RP_05_F_RP_02_FOUNDATION_DECISION_PACKAGE.md` | RELEASE EVIDENCE | `ec7e660f4584c4c246cd78dc942dacd5f85d8eea20bd2a0d28623a214b127f3b` | 决策前事实包（含 §19 Human Decision 追加登记） |
| `docs/architecture/P15_F_RP_05_RESOLUTION_REPORT.md` | RELEASE EVIDENCE | `c2ba10f47c9aa7f197970810e4a5a66ceea9dfbb8ef2e12d0692fae261edf6b1` | F-RP-05 取证报告（含 §16 / §17 append-only 追加） |
| `pyproject.toml` | RELEASE METADATA | `5a88dbc3782cf07b7dced5f5155e87ab95b33d25abc1cd99ee402fd41290f87e` | 版本 → 0.1.14（仅 version 字段 · 0.1.13 值 `b63883c7…` 为其历史态） |
| `config/settings.py` | RELEASE METADATA | `bdb325aed2b9def8c080fab3dcb279ae69b525590a84ef57f7dd83e11385b40b` | 版本 → 0.1.14（仅 APP_VERSION 默认值 · 0.1.13 值 `6c35f04d…`） |
| `docker-compose.yml` | RELEASE METADATA | `54209a8e8d3a1b4422ec403817cb9d8236abb3a4f0197b9f7ff1bdb22441fb9f` | 版本 → 0.1.14（仅 APP_VERSION · 0.1.13 值 `d9693c88…`） |
| `docs/architecture/P15_V0_1_13_RELEASE_PAYLOAD_MANIFEST.md` | MANIFEST (self) | `自引用（self-hash field excluded from canonical hash set）` | 本 payload manifest（见 §3） |

### 1.4 0.1.14 Corrective Payload（F-RP-06 修复轮新增）

| Path | Classification | SHA256 | Reason |
|---|---|---|---|
| `docs/architecture/P15_F_RP_06_HASH_BASIS_RECORD.md` | RELEASE EVIDENCE | `f1568f7d590fb708f62dc1d098db323eb94107ee867b87c5965b202502a112e7` | F-RP-06 记录：Finding / Root cause / 三份字节对照 / Canonical hash source / Resolution / Regression prevention |
| `docs/architecture/P15_V0_1_13_RELEASE_GATE_REPORT.md` | RELEASE EVIDENCE | `4916bbaa75b35c7428a977cf834ab9284438eb9e4c912fbaba9227c6e3468afe` | 0.1.13 Release Gate 的 pre-tag gate report（记录 BLOCKED 与阻塞项） |

```text
0.1.14 corrective commit 的完整路径集合 =
  本 manifest（M · self-hash excluded）
  + pyproject.toml / config/settings.py / docker-compose.yml（M · §1 内已按 canonical 值登记）
  + §1.4 两条新增（A）
⇒ missing = 0 · orphan = 0 · unresolved = 0 · leakage = 0
```

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
canonical hash set = 携带 64-hex SHA256 的 artifact 行
  = §1 的 12 条 + §1.4 的 2 条 = 14（同一路径不重复计数）
校验（0.1.14 起冻结）：
  1. git cat-file blob <tree>:<path> → 取 raw bytes
  2. SHA-256(raw bytes) 必须等于 manifest 声明值
  3. working-tree rendering（含 CRLF/LF 差异）**不得**作为 release hash 基准
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
F-RP-06 = CLOSED（hash basis 修正 + 方法冻结；未做任何行尾批量归一化）
```

**END OF P15 V0.1.13 RELEASE PAYLOAD MANIFEST（0.1.14 manifest-correction revision · Hash Basis = committed Git blob bytes）**
