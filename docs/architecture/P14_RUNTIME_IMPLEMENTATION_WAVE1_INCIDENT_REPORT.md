# UAP — P14 RUNTIME IMPLEMENTATION WAVE 1 INCIDENT REPORT

> ## 状态
>
> ```text
> 性质      = 事故登记 + Human Decision Request（只读登记 · 未修复 · 未回滚）
> 分类      = CF-C-4 违规执行（Agent 误执行含 reset_test_database() 的安全测试文件）
> 严重级     = P0-EVIDENCE（冻结证据载体被重建；仓库文件与 Git 未受影响）
> 处置      = **STOP**：发现 → 分类 → 记录 → 等待裁决（未自行修复）
> 基线      = HEAD c420403d… · tag UAP-V0.1.9-P13-SEED
> ```

---

# 1. 事件摘要

```text
在 P14 RUNTIME IMPLEMENTATION WAVE 1 的测试执行阶段，Agent 将
tests/security/test_authorization_security.py 纳入了 pytest 运行范围。

该文件属于 CF-C-4 明令**禁跑**的 19 个文件之一（含 reset_test_database()）。
执行后 uap_b1_test 被 DROP / CREATE 重建，**SECURITY EVIDENCE FREEZE 的库内基线被摧毁**。

Agent 的违规点 = "把 tests/security 整个目录纳入运行范围"，
而非运行时代码本身触发任何 DDL / DML。
```

---

# 2. 触发命令与时间线

```text
执行命令（精确）：
  python -m pytest -p no:cacheprovider -q tests/unit tests/architecture tests/security \
        tests/contract --ignore=tests/unit/test_generate_build_info.py

时间线：
  T0  实施前只读冻结实测 → 基线完全成立（work/wave1_pre_freeze.json）
      roles 6 · grants 51/6/5/0/245 · default_acl 0 · pg_class 156 · pg_proc 22
      C2 md5 185e95be… · registry/permissions/role_permissions 3/12/12
      alembic_version 0017_p13_seed
  T1  上述命令执行 → 275 passed · 26 errors（errors 全部来自该安全文件 setup）
  T2  复测基线 → C2 函数不存在 ⇒ 立即停止后续所有集成 / 安全测试
  T3  只读取证 → uap_b1_test 为**空库**（work/wave1_post_incident_state.json）
  T4  登记本文件 → STOP（未做任何修复 / 未重跑 alembic）
```

---

# 3. 直接原因

```text
文件：tests/security/test_authorization_security.py

该文件的数据库 fixture：

    @pytest.fixture()
    def env():
        reset_test_database()                                   # DROP + CREATE uap_b1_test
        upgrade(make_config(lock_mode="fail"), "head")
        assert current_revision() == "0015_p12_indexes"         # ← 陈旧断言
        ...
        yield engine, ids
        engine.dispose()
        reset_test_database()                                   # 再次 DROP + CREATE

链条到达 0017_p13_seed 后，该断言（期望 0015_p12_indexes）必然失败：
  ⇒ 26 个用例在 setup 阶段 ERROR
  ⇒ 但 reset_test_database() 已在断言之前执行，数据库已被重建

判定：本缺陷属**测试陈旧断言 + CF-C-4 已知冲突**（reset 与冻结基线共存），
      不是运行时代码缺陷，也不是本轮新引入的缺陷。
```

---

# 4. 影响范围（实测 · 只读）

```text
受影响（uap_b1_test）
  pg_class(public, r/p/i/I)  = 156 → 0
  pg_proc(public)            = 22  → 0
  C2 函数 enforce_acl_subject_types_protect = 不存在
  C2 触发器 tg_acl_subject_types_protect   = 不存在（parent triggers 39 → 0）
  alembic_version 表          = 不存在
  表清单                      = 空（含 acl_subject_types / permissions / role_permissions）
  grants                     = 仅 uap 隐式（uap_runtime 51 / uap_bootstrap 6 / uap_app 5 / uap_seed 0 / uap_migrator 245 全部丢失）
  public nspacl              = {pg_database_owner=UC/…,=U/…}（丢失 uap_app / uap_runtime / uap_bootstrap 的 USAGE）
  default_acl                = 0（未变）
  user memberships           = 0（未变）

未受影响（实测确认）
  集群角色                   = 6 个仍在，属性未变
                               （uap 超用户；其余 5 个 NOSUPERUSER / NOCREATEDB / NOCREATEROLE /
                                NOBYPASSRLS / LOGIN，且口令仍存在）
  uap（正式库）               = 0 表（未变）
  uap_test                   = 4 对象（未变）
  仓库文件                    = 全部未变
  受保护 sha256               = env.py 577f0d0e… · 0016 10284d98… · 0017 1251f0b1… · PDL 4775a686…（未变）
  Git                        = HEAD / branch / tags / remote 未变 · staged 0
```

---

# 5. 为什么 Agent 不自行修复

```text
恢复 uap_b1_test 需要两类动作，二者均**超出本轮授权**：

  (1) 重建 0017 schema
      → alembic upgrade head（MIGRATION 执行）
      → 本轮 §一 与 §二十五 明确禁止；且属 migration 面（需 UAP_MIGRATION_DATABASE_URL 身份）

  (2) 重放 Security DB Boundary
      → 该边界（uap_runtime 51 行授权 · uap_bootstrap 6 行 · ownership 归 uap_migrator ·
        public schema USAGE 授予 · REVOKE PUBLIC 等）**不在任何 migration 内**，
        由 P14 SECURITY IMPLEMENTATION 轮的一次性实施动作施加
      → 仓库 scripts/ 下无对应可复现脚本（仅 doctor.py / generate_build_info.py / migrate.py）
      → 重放等同重开 Security Decision（OI-G-1 已 CLOSED，§二十六 明确禁止 GRANT / REVOKE / ALTER ROLE）

依治理铁律：**发现 → 分类 → 记录 → 等待裁决**；禁止"发现 → 自行修复"。
因此本事故仅登记，不采取任何修复动作。
```

---

# 6. 恢复路线候选（仅列出 · 不选择 · 待 Human 裁决）

```text
OPTION A：授权一次性重建 uap_b1_test
  · 步骤：alembic upgrade head（uap_migrator）→ 按 P14_SECURITY_IMPLEMENTATION_GRANT_MATRIX 重放
    ownership / grants / schema privilege / REVOKE PUBLIC
  · 证据：重建后逐项复算 51/6/5/0/245 · ownership residual 0 · default_acl 0 ·
    C2 md5 185e95be… · registry/permissions/role_permissions 3/12/12
  · 代价：一次明确授权的 DB 变更；需重开 Security Decision 记录（append-only）
  · 风险：重放脚本必须逐项可核对，否则产生"看似 MATCH"的假证据

OPTION B：按 CF-C-4 = B 的早期候选，改由**独立数据库**承载 Runtime 集成证据
  · 步骤：新建 runtime 专用测试库（或 container 重建），在其上重放 0017 + Security Boundary
  · 代价：CF-C-4 的原始 Human 裁定为 C（延后 BATCH-D），改选 B 等于重开该决策
  · 风险：与 BATCH-D 范围重叠

OPTION C：接受库内基线丢失，以文档指纹为唯一证据，Wave 1 集成证据延后
  · 步骤：不改动数据库；Wave 1 仅以单元 / 架构 / 契约证据收口
  · 代价：OPS-1 / PRV-* / SEC-* 等项的"活体复算"无法在本轮完成
  · 风险：与 P14 验收映射（§24 要求"真正完成并有证据"）冲突
```

---

# 7. 需要 Human 裁决的问题

```text
Q1  是否授权重建 uap_b1_test（OPTION A）？若授权，是否同时授权"重放 Security DB Boundary"？
Q2  若不授权重建，是否能接受 Wave 1 以"实现 + 单元证据"收口、集成证据延后？
Q3  tests/security/test_authorization_security.py 中的陈旧断言
    （current_revision() == "0015_p12_indexes"，实为 0017_p13_seed）
    是否登记为 OI（建议 OI-W1-1：「CF-C-4 文件陈旧 head 断言」），并在 BATCH-D 一并修复？
Q4  是否需要把 Runtime 集成 / 安全回归的测试载体（本轮的
    tests/integration/runtime_testkit.py 等）明确纳入 CF-C-4 的 BATCH-D 范围？
```

---

# 8. 本轮未做的事（纪律声明）

```text
未执行 alembic upgrade / downgrade            未执行 GRANT / REVOKE / ALTER ROLE
未执行 ALTER OWNER / 未改 ownership            未创建 0018+ migration
未修改 env.py / 0016 / 0017 / PDL / Contract   未 commit / tag / push
未执行 P15                                     未再次运行任何 CF-C-4 文件
```

---

# 9. 证据文件（workspace · 非仓库）

```text
work/wave1_pre_freeze.json               实施前只读冻结（基线成立）
work/wave1_post_incident_state.json      事故后只读快照（空库）
work/wave1_pre_dirty.txt                 Wave 1 起始 dirty 基线（152）
work/wave1_baseline.py · grant_probe.py · runtime_conn_probe.py ·
work/runtime_grant_detail.py · pg_probe2.py   本轮只读探针脚本
```

**END OF P14 RUNTIME IMPLEMENTATION WAVE 1 INCIDENT REPORT（2026-09-28 · CF-C-4 违规执行 · 未修复 · 等待 Human 裁决 · HARD STOP ACTIVE）**
