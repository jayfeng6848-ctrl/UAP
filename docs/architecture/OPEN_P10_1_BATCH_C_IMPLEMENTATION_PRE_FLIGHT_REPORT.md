# OPEN-P10-1 BATCH-C · IMPLEMENTATION PRE-FLIGHT REPORT

> ## 状态（文件抬头 · 无名号）
>
> ```text
> 轮次                       = BATCH-C IMPLEMENTATION PRE-FLIGHT（STRICT PRE-FLIGHT / ZERO IMPLEMENTATION）
> Phase 0 基线               = PASS（零 drift · §1）
> Decision reconciliation    = PASS（8/8 + 3/3 · 未重新解释 · §2）
> OI-DC-1                    = RESOLVED → INLINE（§3）
> OI-DC-2                    = RESOLVED（窗口期 runbook · 不入 0016 · §4）
> FD-C-1 / OI-G-3            = CONFIRMED / RESOLVED（临时前置语义 · §5）
> CC-7 contract              = FROZEN FOR IMPLEMENTATION（§6）
> 0016 contract              = FROZEN FOR CREATION（§7/§8/§12）
> Implementation             = NOT STARTED
> 0016 / 0017                = ABSENT / ABSENT
> HARD STOP                  = 等待独立的 `BATCH-C 0016 IMPLEMENTATION` start authorization
> ```

---

## §0 MEMORY / Evidence Governance（一致性检查）

- `MEMORY.md` 已于本会话开局按规程完成 curated 重写（2026-09-27 版 · 约 3.9KB · 注明"详细教训 = skill `uap-staged-gate` 87 条"）；本轮做**只读一致性检查**，不再次改写：
  - 保留面核对 = D-OP101 关键冻结（§3 计数与 CP-F/CC-7/Downgrade 条目）✓ · P13 Frozen（§3）✓ · BATCH-B Final（§7）✓ · BATCH-C Decision Record（§7 REGISTERED 行）✓ · `OI-G-3` ✓ · `OI-BB-14` ✓（§5 双 DSN/探针约束行）· `OI-DC-1/OI-DC-2` ✓ · `CF-C-1…7`（§7 内联映射）✓ · migration chain / security anchors / commit 拓扑 ✓；
  - 压缩面核对 = 详细 harness 教训已沉淀 skill（lesson 87 含本轮四类陷阱）✓ · 历史轮次逐轮细节已由 `uap-stage3-evidence/` 与仓库内报告承载 ✓；
  - **未借清理触碰任何工程源码 / migration / 数据库状态**（本轮 dirty 变更面见 §15）。

## §1 Phase 0 — Pre-Flight Baseline（只读实测 · 零 drift）

| 组 | 锚点 | 实测 | 判定 |
|---|---|---|---|
| Git | HEAD / branch / tags / remote | `034ee97c…` / `main` / 8 / 0 | PASS |
| Git | dirty | 100（= 98 轮前 + REVIEW REPORT + DECISION RECORD；Block 编辑不加行） | PASS |
| Migration | 活体 `alembic_version` | `0015_p12_indexes`（单头，与 `alembic heads` 一致） | PASS |
| Migration | 0016 / 0017 / `.py` 计数 | ABSENT / ABSENT / 15 | PASS |
| DB | 非 `pg_%` 角色 | 4（`uap`/`uap_app`/`uap_migrator`/`uap_seed`） | PASS |
| DB | `uap_migrator` 属性 | `rolsuper/createdb/createrole/replication/bypassrls = 0/0/0/0/0`（全 NOSUPERUSER 族） | PASS |
| DB | `uap_app` 显式授权 / ownership / residual | 5 / `uap_migrator:156`+`uap_migrator:22` = 178/178 / 0 | PASS |
| DB | `uap_migrator` schema CREATE / `default_acl` / 用户成员关系 | false / 0 / 0 | PASS |
| DB | 正式库 `uap` | 0 表 | PASS |
| 锚点 | PDL sha / `0007` sha / C2 md5 / 父级触发器 | `a83fde5c…` / `9e0105b9…` / `68678741…` 命中 1 / 39 | PASS |

## §2 Decision Reconciliation（不重新解释）

读取 `OPEN_P10_1_BATCH_C_DECISION_RECORD.md`，最终裁定 = `CF-C-1=A · CF-C-2=A · CF-C-3=A · CF-C-4=C · CC-7 MODEL=Trusted Migration Identity Model(CUSTOM) · MIGRATION ROLE POLICY=uap_migrator-only(A) · OWNERSHIP POLICY=Preserve Existing Ownership(A) · CF-C-5=B · CF-C-6=A · CF-C-7=CONFIRM`，`START = AUTHORIZED`。本报告一切契约**仅从该 Record 导出**，与 Human 消息原文逐字一致（raw 值见 Record §1）。

## §3 OI-DC-1 Resolution — CC-7 实现形态 = **RESOLVE TO INLINE**

1. 0016 内的 CC-7 函数改写采用 **migration revision 自包含 SQL**（`op.execute(...)` 内联完整函数定义，或与仓库 0014 同族既有的 inline execution 等价模式）；
2. **不得建立** `migrations_alembic/sql/cc7.sql`、`templates/`、runtime SQL file、external deployment SQL 等第二套执行载体（除非后续出现新的明确授权）；
3. 决定性理由（Human 给定，全数采纳）：① 0016 是独立 Trust Boundary revision；② CC-7 必须与 revision 绑定；③ 避免 migration 文件与外部 SQL 文件版本漂移；④ 最小载体原则；
4. **"inline" 审计红线**：完整函数定义 · 明确函数名 · 明确依赖 · 可审查 · 可 downgrade · **禁 dynamic SQL**（禁字符串拼接构造标识符/条件）。

## §4 OI-DC-2 Resolution — Privilege Window Runbook = **RESOLVED**

```text
Deployment / Orchestrator identity
        ↓ GRANT CREATE ON SCHEMA public TO uap_migrator   （执行窗口前 · pre-provision）
uap_migrator  ──（经 UAP_MIGRATION_DATABASE_URL）──▶  0016 migration
        ↓ CC-7 verification
REVOKE CREATE（post-verification）
        ↓ retain uap_migrator（禁 DROP ROLE · 对齐 D-OP101-12）
```

- **严格禁止**：`uap_migrator` 自授/自撤 CREATE · SECURITY DEFINER · SUPERUSER workaround · SET ROLE workaround · application_name/GUC trust；
- **GRANT/REVOKE 不写进 0016 migration 内部**（不作为自动权限生命周期机制）——属于 deployment/orchestration pre-provision / post-verification 操作；
- **本轮未执行任何 GRANT/REVOKE**（实测 `has_schema_privilege('uap_migrator','public','CREATE') = false` 保持）。

## §5 FD-C-1 / OI-G-3 Final Gate

决定性实验（BATCH-C PREP 轮实测）登记为 0016 硬前置：`CREATE TABLE → denied` · `CREATE OR REPLACE OWNED FUNCTION → denied` ⇒ **schema CREATE = necessary prerequisite**。`OI-G-3 = RESOLVED` 的**唯一合法解释** = "0016 execution prerequisite = schema CREATE **temporarily provisioned**"（CF-C-5=B 窗口期），**不得**解释为 `uap_migrator` 永久获得 CREATE。

## §6 CC-7 Contract Reconstruction（FROZEN FOR IMPLEMENTATION）

### §6.1 现行 C2（被替换对象 · 逐字节锚定）

- 唯一目标函数：`public.enforce_acl_subject_types_protect()`（trigger function，触发器 `tg_acl_subject_types_protect` 于 `acl_subject_types`，**0007_b1_4_resource_acl.py:78 首建**，trigger :245）；
- 现行定义全文已留档：`../uap-stage3-evidence/cc7_c2_functiondef_preflight.sql`；`md5(pg_get_functiondef) = 6867874166ae36966763c1026ab2af19`；
- 现行语义：INSERT → RAISE（registry 为 migration-controlled）· DELETE → RAISE（retire via archived_at）· UPDATE key 不可变。

### §6.2 Trust predicate（唯一受信条件 · 不得替换）

```text
current_user = 'uap_migrator'  AND  session_user = 'uap_migrator'   —— 须同时成立
```

禁用替代：`application_name` / custom GUC / environment variable / client supplied flag / 仅 role name 参数。

### §6.3 Role assertion（保留 · 不得删除或弱化）

`migrations_alembic/env.py:95 _assert_effective_role`（`:113 SELECT current_user, session_user` → 与 migration DSN 所指角色比对，不符即 `MigrationIdentityError` FAIL-CLOSED）**保持原样**；不得弱化为"connection succeeded"。

### §6.4 C2 不变量（0016 不得触碰）

禁 disable C2 / bypass C2 / alter C2 semantics（对 runtime 身份的拒绝行为与错误信息面）/ temporarily disable trigger（`DISABLE TRIGGER`、`session_replication_role` 永久禁令）/ change C2 failure behavior（runtime 路径 RAISE 语义保持）。**改写只允许**：在保持上述不变量的前提下，为 §6.2 受信 migration context 打开受控通道。

## §7 0016 Exact Scope Contract（FROZEN FOR CREATION）

**只允许**：CC-7 Trust Boundary rewrite + 实现该 rewrite 绝对必要的结构动作。
**明确禁止**：P13 seed · `0017` · `acl_subject_types` INSERT（作为数据）· permission seed · agent data · agent_versions · agent_permissions · tool_executions · runtime configuration · `uap_app` grants · ownership migration · G/H/I/J · RLS · SECURITY DEFINER。
**归属恒等式保持**：`0016 = Trust Boundary` · `0017 = P13 Seed`（`D-OP101-13`）。

## §8 Upgrade / Downgrade Contract

**Upgrade**：verify trusted migration identity（env.py 角色断言自然生效）→ replace CC-7 function（inline）→ verify function definition（`pg_get_functiondef` 比对 + 正/负向探针）→ stop / gate。
**Downgrade**：restore **exact previous CC-7 definition**（= §6.1 留档 SQL，`md5 = 68678741…` 为恢复后验证锚点）。
**Downgrade 必须证明不触碰**：roles · grants · ownership · C2 semantics（对 runtime）· unrelated functions；**禁止** DROP C2 / DELETE registry data / ALTER roles / DROP unrelated function / DROP unrelated trigger。

## §9 Existing Precedent Reconciliation

- `0014_p11_triggers.py` 含 4 处 `CREATE OR REPLACE FUNCTION`（:63/:98/:112/:129）——经比对均为**该迁移自建函数的首建**（防重跑幂等习语），**非跨迁移替换**；
- C2 于 `0007…:78` 首建 ⇒ **0016 对其的替换 = 全仓首个 cross-migration security-function replacement（先例 = 0）**，须产出独立 implementation evidence（替换前后 functiondef + md5 + 正/负探针日志）。

## §10 Test Strategy（OI-BB-14）

- **禁** `import migrations_alembic.env`（import 即进入 Alembic 执行路径）；
- 0016 验证 = **real Alembic CLI probe**（经 `tests/integration/alembic_testkit.py` B-4 已交付的 `migration_dsn()` FAIL-CLOSED + `make_config()`，走 `UAP_MIGRATION_DATABASE_URL`）+ **database verification**（functiondef md5 / 触发器行为探针 / 受信与运行时身份正负探针）；
- 不引入 `sql/` 载体测试、不修改测试基建（本批）。

## §11 Integration Ownership Protection（CF-C-4 = C）

- **Unsafe（本轮及 BATCH-C 全程禁跑）**：调用 `reset_test_database()` 的 **19 个文件** = `tests/integration/` 18 文件（含 `alembic_testkit.py` 自身）+ `tests/security/test_authorization_security.py` —— 会导致 DROP/CREATE DATABASE，摧毁 BATCH-A 178 ownership；
- **Safe probes（允许）**：只读 psql/SQL 查询 · `SET ROLE` 类负向探针（事务内回滚）· Alembic CLI 只读命令（`heads/history`）· 0016 实施时的 up/downgrade 探针（在窗口期授权下）——均不得破坏 178 ownership / `uap_app` grants=5 / C2。

## §12 Migration File Contract

```text
revision      = 0016_open_p10_1_trust_boundary   （30 字符 ≤ 32 ✓ · 与 RV-A 裁定一致）
filename      = 0016_open_p10_1_trust_boundary.py（filename == revision ✓）
down_revision = 0015_p12_indexes
collision     = 0（versions/ 全目录字面 `0016` 命中 = 0，实测）
branch / multiple heads = 0 / 0（单头 0015_p12_indexes）
不得创建 placeholder
```

## §13 Security Acceptance Matrix（C01…C20 · 实施验收 · 本轮全部 PLANNED）

```text
C01 migration identity assertion        PLANNED   C11 temporary CREATE removed after verification  PLANNED
C02 session_user assertion              PLANNED   C12 uap_migrator remains NOSUPERUSER             PLANNED
C03 current_user assertion              PLANNED   C13 no SECURITY DEFINER                          PLANNED
C04 schema CREATE prerequisite          PLANNED   C14 no GUC/application_name trust                PLANNED
C05 CC-7 replacement correctness        PLANNED   C15 no P13 seed                                  PLANNED
C06 C2 unchanged                        PLANNED   C16 0017 remains absent                          PLANNED
C07 runtime role unchanged              PLANNED   C17 migration chain single head                  PLANNED
C08 ownership unchanged                 PLANNED   C18 test strategy obeys OI-BB-14                 PLANNED
C09 grants unchanged                    PLANNED   C19 integration reset not executed               PLANNED
C10 downgrade restores prior function   PLANNED   C20 protected-object regression                  PLANNED
```

## §14 Pre-Flight Gate Harness（P01…P20）

独立 harness 复算结果 = **23/23 PASS**（P01…P20 + 轮次相对 S1/S2；首轮 2 FAIL 均为 harness 自身缺陷——P07 token 替换表达式逻辑错误、P16 期望串空格与 `psql -tA` 输出不符，实际值 `0|0|0|0|0` 正确——修 harness 不动工程对象后复跑全过）；日志 = `../uap-stage3-evidence/batch_c_implementation_preflight_gate.log`；集合断言均验证 expected set（空集不视为 PASS）。

## §15 本轮变更面

| 类别 | 对象 |
|---|---|
| 仓库内新增 | 本报告（唯一 `.md` 新增） |
| 仓库外 | C2 functiondef 留档 `cc7_c2_functiondef_preflight.sql` + harness + gate log |
| 未触碰 | 全部源码 / migration / 测试 / 配置 / Block / Record / PDL |

---

## FINAL PRE-FLIGHT GATE

```text
BATCH-C IMPLEMENTATION PRE-FLIGHT = PASS（P01…P20，见 gate log）

OI-DC-1 = RESOLVED（INLINE）
OI-DC-2 = RESOLVED（窗口期 runbook · GRANT/REVOKE 不入 0016）

CC-7 contract = FROZEN FOR IMPLEMENTATION
0016 contract = FROZEN FOR CREATION

Implementation = NOT STARTED
0016 = ABSENT
0017 = ABSENT

DDL = 0
DML = 0
ROLE CHANGE = 0
GRANT = 0
REVOKE = 0
OWNER CHANGE = 0
C2 CHANGE = 0

integration suite = NOT EXECUTED
```

**HARD STOP** —— 不创建 0016。下一阶段只能是 **`BATCH-C 0016 IMPLEMENTATION`**，且必须在收到独立的 implementation start authorization 后才能开始。

**END OF OPEN-P10-1 BATCH-C IMPLEMENTATION PRE-FLIGHT REPORT（2026-09-27 · `PRE-FLIGHT = PASS` · `IMPLEMENTATION = NOT STARTED` · `0016 = ABSENT`）**
