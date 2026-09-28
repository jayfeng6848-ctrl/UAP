# UAP — P14 OVERALL OI / FINDING CLOSURE MATRIX

> ```text
> 轮次 = P14 OVERALL FINAL ACCEPTANCE（2026-09-28）
> 口径 = 每项给出 Status / Blocking? / Evidence；**Deferred 不等于 PASS**
> ```

| Finding | Status | Blocking? | Evidence |
|---|---|---|---|
| `OI-G-1` | CLOSED | No | Security implementation + 53 次探针 · Wave1/2 复测 grants 51/6/5/0/245 未变 |
| `OI-G-4` | OPEN / BATCH-D | No | 既有 maintenance（`test_generate_build_info.py` 硬编码 head）· 本轮未修 · 不在 allowlist |
| `OI-G-9` | REGISTERED / UNFIXED | No | stale head 断言（CF-C-4 面）· 本轮未修（REGISTER ONLY） |
| `D-01` | DEFERRED / NON-BLOCKING FOUNDATION MAINTENANCE | No | active P14 路径不依赖故障 helper（见下） |
| `D-02` | **CLOSED（Human OPTION B · 2026-09-28）** | No（已解除） | Wave 1 artifact 逐字节恢复且不再改动；该项失败裁决为环境状态产物；审计不变量由 Wave 2 独立测试覆盖 |
| `ENV-1` | CLOSED | No（已关闭） | 权威清单已加 `argon2-cffi==25.1.0`；干净 venv 安装后 20 tests passed |
| `FINDING-AUTHZ-1` | ACCEPTED / DEFERRED | No | 未新增 permission vocabulary；管理类操作登记为 SEPARATE HUMAN DECISION |
| `FINDING-ENGINE-1` | ACCEPTED COMPATIBILITY FINDING | No | `/ready` 探针与 RuntimeDatabase 并存 · 未重构 · 不改变 Wave 1 health contract |
| `FINDING-P11-1` | INFO（正向证据） | No | P11 触发器两次正确拒绝 scope 不匹配的 fixture |
| `FINDING-IDX-1` | INFO | No | 发现并遵守既有唯一索引（credentials / identities / sessions） |

---

# D-01 证据（active-path exclusion · 只读）

```text
故障文件 = infrastructure/database/persistence.py::Repository._fetch_one/_fetch_all
  sha256 = 69d2c14064d19d5355cf867665476c3432cca2e4561f491bab0c86c9f3876fd6（未改动）

继承关系（实测 rg）
  services/reads.py:35                    class SafeReader(Repository)        ← 覆盖两方法，语义正确
  services/identity/repository.py:29      class IdentityRepository(SafeReader) ✅
  services/device/repository.py:21        class DeviceRepository(SafeReader)   ✅
  services/session/repository.py:25       class SessionRepository(SafeReader)  ✅
  services/authorization/repository.py:31 class AuthorizationRepository:        （不继承 Repository；
                                              自带 _fetch/_fetch_one ⇒ Stage 2 不受影响）

⇒ P14 active runtime path（Identity / Device / Session / Context / API / Stage 2）
   完全不依赖故障的 legacy helper。
⇒ 原文件保持 frozen；SafeReader = 当前 P14 approved persistence path；
   future foundation change 需独立 authorization。
```

---

# D-02 证据与阻塞说明

```text
事实链
  1. Wave 2 曾把 tests/integration/test_runtime_db_wave1.py 的 `assert audit == 0`
     改为不变量断言（登记 D-02）。
  2. 本轮 Step A：**已逐字节恢复 Wave 1 原始断言**（`assert audit == 0`）。
  3. 本轮 Step B：新增 tests/integration/test_wave2_audit_invariant.py（4 个 delta 断言：
     纯读路径 +0 · 成功认证 +1 · 拒绝认证 +1(denied) · 设备撤销 +1(HIGH)）⇒ 该套件通过。
  4. 本轮 Step C：重跑 Wave 1 frozen set ⇒ **210 passed · 1 failed**，
     唯一失败 = `test_approved_reads: assert 926 == 0`。

根源（非代码缺陷）
  · audit_logs append-only（tg_audit_immutable · D-P10-11）：UPDATE/DELETE 一律 RAISE，
    连 fixture 身份也无法删除 ⇒ 该表**不可能回到 0**。
  · 926 行 = Wave 2 安全套件的 **EXPECTED TEST DATA**（Wave 2 manifest §4 已声明）。
  · 指令 §二十七："audit_logs 因为 immutable：**不得强制归零**；必须使用 expected test
    audit state 或 delta-based assertion，而不是 audit_logs == 0"。
  · 指令 §七 Step A 要求恢复 `audit_logs == 0` 的原始断言。
  ⇒ 两条要求在**当前数据库状态**下互斥。

关闭 D-02 的可选路径（均需 Human 授权 · 本轮均未执行）
  OPTION A：授权一次 "Wave 1 基线环境重建"：经 CF-C-4 approved destructive path 重置
      uap_b1_test → 0017 迁移 → Security DB Boundary 精确重放（= HD-P14-REC-01 的已文档化
      恢复规程）。之后 Wave 1 frozen set 在干净基线上可复现（audit=0），Wave 2 再产生 delta 证据。
      代价：该规程需要 GRANT/REVOKE（本轮 §二 明令禁止）⇒ 需你明确授权 Boundary replay。
  OPTION B：确认该断言为 Wave-1-only baseline 断言，以"artifact 已恢复 + 不变量已由 Wave 2
      独立测试覆盖"结案（接受这 1 项失败为环境状态产物，不改文件）。
      代价：Wave 1 frozen set 在本 DB 状态下永久保留 1 项失败。

⇒ **Human 裁决（2026-09-28）= OPTION B**（canonical registration = PDL **附录 Q**）：
  · 不重建测试库（无 reset）· 不 replay GRANT/REVOKE · 无 schema / migration / role 操作
  · Wave 1 frozen artifact **保持恢复后的原始断言，不再改动**
  · 该断言 = Wave-1-only baseline 断言；其在含 append-only EXPECTED TEST DATA 的库状态下的
    失败 = **环境状态产物**（非代码回归 · 非验收缺陷）
  · 审计不变量由独立 Wave 2 测试覆盖（test_wave2_audit_invariant.py）
⇒ D-02 = **CLOSED**（by Human adjudication）⇒ 唯一 blocking item 解除
```

---

# ENV-1 证据（已关闭）

```text
Step A（只读）
  权威清单 = pyproject.toml [project].dependencies + requirements.txt（均为精确 `==` 风格）
  lockfile = 不存在（无 poetry.lock / uv.lock / Pipfile.lock）
  实际版本 = argon2-cffi 25.1.0（bindings 26.1.0 · cffi 2.1.1）
Step B（只改必要依赖）
  两处清单各加一行 `argon2-cffi==25.1.0`；未升级其他包；未更换 Argon2 实现；未改 Runtime 语义
Step C（干净隔离环境验证）
  新建 venv → pip install -r requirements.txt → exit 0
  → import argon2 OK（25.1.0）
  → 该 venv 运行 Wave 2 Unit + Wave 1 taxonomy = **20 passed**
  → 哈希前缀 = argon2id · verify = True · 错误口令拒绝 = True
  ⇒ 证明 P14 Runtime 不依赖"机器上刚好装过的包"
```

**END OF P14 OVERALL OI CLOSURE MATRIX（2026-09-28 · ENV-1 CLOSED · D-01 DEFERRED · D-02 CLOSED by Human OPTION B · blocking item = 0 · HARD STOP ACTIVE）**
