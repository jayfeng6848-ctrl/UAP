# OPEN-P10-1 BATCH-B · FINAL EXECUTION REPORT（B-1…B-6 · FINAL SECURITY VERIFICATION）

> ## 状态（文件抬头 · 无名号）
>
> ```text
> 轮次      = OPEN-P10-1 BATCH-B IMPLEMENTATION · B-6 FINAL SECURITY VERIFICATION
> 模式      = Stop-Gated（B-1…B-6 每步验证）· 本轮 = 只读最终核验（无任何源码/配置/测试修改）
> 结论      = **BATCH-B FINAL SECURITY VERIFICATION = PASS**
>           （BB-S01…S08 全 PASS · 配置静态边界 PASS · Alembic static DSN PASS ·
>             testkit/conftest boundary PASS · protected-object PASS · round-relative scope PASS）
> as-of     = HEAD 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e · branch main · tags 8 · remote none
>             单头 0015_p12_indexes · 0016/0017 = ABSENT/ABSENT · commit = 0 · tag = 0 · push = 0
> Gate      = B6_final_gate.log **67 / 67 PASS**（exit 0）· 独立复算，非引用前序结论
> 自证缺陷  = 真实缺口 **0** · harness 口径缺陷 **3 类 / 6 项断言**（2 次复跑）· 新增登记 **OI-BB-14**
> ```

---

## §1 执行序列与各步结论

| 步 | 内容 | 结论 | 证据 |
|---|---|---|---|
| **B-1** | Config Resolution（`env.py` 解析链重写 + 角色断言） | **PASS** | `B1B2_probes.log` · `B1_role_assertion.log` |
| **B-2** | Alembic DSN Isolation（`alembic.ini` 移除可执行 DSN） | **PASS** | 同上（`^sqlalchemy.url` 可执行行 = 0） |
| **B-3** | Runtime DSN Boundary（`settings.py` 仅注释边界说明） | **PASS** | `B3_settings_diff.txt`（+5/−0）· `B3_test_config.log`（13/13） |
| **B-4** | Test Fixture Carrier（testkit + conftest 双 DSN 链） | **PASS** | `B4_gate.log`（23/23） |
| **B-5** | Documentation / Deployment Sync（4 载体） | **PASS** | `B5_gate.log`（39/39） |
| **B-6** | FINAL Security Verification（本轮 · 独立复算） | **PASS** | `B6_final_gate.log`（**67/67**） |

---

## §2 BB-S01…BB-S08 最终安全矩阵（本轮独立执行，非引用旧结果）

| 项 | 场景 | 结果 | 实测证据 |
|---|---|---|---|
| **BB-S01** | 两键齐设（migration = `uap_migrator` DSN · runtime = `uap_app` DSN） | ✅ **PASS** | `alembic upgrade head` exit 0（at-head no-op），经 `env.py` 解析 + 角色断言 |
| **BB-S02** | runtime source = `DATABASE_URL` | ✅ **PASS** | `load_settings_from_env` 解析出该键；runtime 引擎以之连接 |
| **BB-S03** | `DATABASE_URL` 有效 + migration 键**空** | ✅ **PASS** | `alembic upgrade head` **exit ≠ 0**；异常类型 = **`env_py.MigrationIdentityError`**（逐字记录）；错误文本含「runtime-only and is deliberately NOT used as a fallback」；`uap_app` 未出现在异常前文（runtime DSN 值从未抵达 runner） |
| **BB-S04** | migration 键有效 + `DATABASE_URL` **ABSENT** | ✅ **PASS** | `alembic upgrade head` exit 0；`testkit.migration_dsn()` 返回 migration DSN（不受 runtime 缺失影响） |
| **BB-S05** | migration path 不读 `DATABASE_URL` | ✅ **PASS** | **AST 级**：`env.py` 的 env 读取集合（别名解析后）= {`UAP_MIGRATION_DATABASE_URL`, `UAP_MIGRATION_LOCK_MODE`, `UAP_MIGRATION_LOCK_TIMEOUT_SECONDS`} —— **无 runtime 键**；每个 env-read 实参都解析进 `UAP_MIGRATION_*` 命名空间（**含别名走私检查**）；源码中 0 处 `os.getenv` |
| **BB-S06** | runtime path 不读 migration 键 | ✅ **PASS** | **AST 级**：`settings.py` env 读取不含 migration 键 · `Settings.model_fields` **不含**该键（实测 `False`）· `infrastructure/database/config.py` 0 env 读取且**文件未改** · `testkit.runtime_dsn()` 仅读 `DATABASE_URL`（别名解析后）· `conftest` 不 setdefault migration 键 |
| **BB-S07** | effective migration identity | ✅ **PASS** | `current_user = uap_migrator` · `session_user = uap_migrator`（实测 SELECT）；**非** `uap_app` / `postgres` / 旧 `uap`；role assertion 仍在 `run_migrations_online` 中被调用且未弱化（AST 验证调用点 + `MigrationIdentityError` + current_user/session_user 比对） |
| **BB-S08** | effective runtime identity | ✅ **PASS** | `current_user = uap_app` · `session_user = uap_app`；**非** `uap_migrator` |

> **BB-S07 的一个重要限定**：`uap_migrator` 当前**无 schema `CREATE`**（BATCH-A `OI-G-3`），因此「以 `uap_migrator` 身份执行迁移」的完整证明形态是「对 **at-head** 库执行 `alembic upgrade head` ⇒ no-op 成功」——这足以证明**解析链 + 连接身份 + 角色断言**，但**不**证明 DDL 执行能力（那是 BATCH-C 前置 `OI-G-3` 的范畴）。本报告不把 no-op 误述为「已验证 DDL 路径」。

---

## §3 负向探针（cross-fallback 全覆盖）

| 探针 | 场景 | 期望 | 实测 |
|---|---|---|---|
| N-1 | 仅 `DATABASE_URL`（migration 键空串） | FAIL-CLOSED | ✅ exit ≠ 0 · `MigrationIdentityError` |
| N-2 | 仅 `DATABASE_URL`（migration 键 **unset**） | FAIL-CLOSED | ✅ 同上（B-1 P3 已验，本轮复验于 BB-S03） |
| N-3 | **角色断言失败分支**：URL user = `uap` 但经 libpq `options=-crole=uap_migrator` 使生效角色为 `uap_migrator` | 必须拒绝 | ✅ `MigrationIdentityError: effective migration role 'uap_migrator' does not match the role named in the migration URL 'uap' (session_user='uap')`（对照：无 override ⇒ 成功） |
| N-4 | `make_config(url="   ")` | FAIL-CLOSED | ✅ `MigrationDSNError` |
| N-5 | runtime 侧：migration 键在 + runtime 键缺 ⇒ `runtime_dsn()` 返回显式 `RUNTIME_DSN`（**非** migration DSN） | 无交叉 | ✅ |

---

## §4 静态边界（AST / 精确 pattern，非裸子串）

| 对象 | 结论 |
|---|---|
| `migrations_alembic/env.py` | env 读取（AST，别名解析后）= `UAP_MIGRATION_DATABASE_URL` + 两个 lock 旋钮；**runtime 键 0 次**；无 `os.getenv`；每个 env-read 实参都落在 `UAP_MIGRATION_*` 命名空间（**别名走私检查**通过）|
| `config/settings.py` | env 读取不含 migration 键；`Settings.model_fields` 不含之；`DATABASE_URL` 字段/校验器/脱敏路径不变（B-3 diff = +5 注释）|
| `infrastructure/database/config.py` | 0 env 读取 migration 键；文件**逐字节未改**（BATCH-B OUT）|
| `tests/integration/alembic_testkit.py` | `migration_dsn()` 仅读 migration 键（**别名解析后**）；`runtime_dsn()` 仅读 runtime 键；**无任何函数同时读两键**（无交叉身份路径）；`make_config()` 保留 `attributes["url"]` + 空 URL FAIL-CLOSED |
| `tests/conftest.py` | runtime 键照旧 setdefault；migration 键**不** setdefault；新增双 fixture |
| `alembic.ini` | 可执行 `sqlalchemy.url` = **0 行**；旧 dev DSN 未以可执行形式重现；非可执行示例为注释 |

**散文级语义扫描**（去粗体 + 空白折叠 + ±1 行窗口）：两份 README、`env.py`、`conftest.py` 中 `fallback` 命中 **affirmative = 0** —— 全部为否定/描述式（"NOT a migration fallback"、"no fallback in either direction"、"不存在任何方向的 fallback"）。

---

## §5 配置链一致性（最终态）

```text
.env.example            DATABASE_URL=（空）           = runtime application database
                        UAP_MIGRATION_DATABASE_URL=（空）= Alembic migration database
docker-compose.yml      api → DATABASE_URL（runtime only，migration 键绝不注入）
                        无 migration service/entrypoint（OI-BB-5 冻结；带外执行方式已文档化）
README.md               双独立导出（占位符 DSN）+ "Alembic does NOT use DATABASE_URL" 逐字声明
migrations_alembic/README.md  「Migration 身份（独立于 runtime）」节 + 解析顺序 + 双向无 fallback + FAIL-CLOSED
alembic.ini             无可执行 DSN；注释说明解析顺序与 FAIL-CLOSED
```

**与实现一致**：`env.py` 解析顺序 = ① `UAP_MIGRATION_DATABASE_URL` → ② `config.attributes["url"]`（tests/CI 显式覆盖）→ ③ `MigrationIdentityError`。

---

## §6 受保护对象回归（全部 UNCHANGED）

```text
0007 SHA              = 9e0105b9dc4281755a313b6477cc755e07f4b356403af169e69529698b8ec1ef
C2 MD5                = 6867874166ae36966763c1026ab2af19
C2 trigger inventory  = 31|O|0
PDL SHA               = a83fde5c5760525233f4c56043bd39b11eaa950520be2b27ed4790c90673ef56
Contract SHA          = 2c1fec371de5ab3b…（未改）
Decision Record SHA   = 002e25091f484bee…（未改）
roles                 = 4（uap + uap_seed/uap_migrator/uap_app）
ownership residual    = 0（178/178 → uap_migrator）
uap_app grants        = 5
formal uap tables     = 0
0016 / 0017           = ABSENT / ABSENT
alembic head          = 0015_p12_indexes（单头）
HEAD                  = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e（未动）
commit / tag / push   = 0 / 0 / 0（tags 8 · remote none）
```

---

## §7 轮次相对 Git 验证（基于 BATCH-B 实施轮起始快照，86 项）

```text
NEW      = 9 个授权载体（env.py · settings.py · alembic.ini · .env.example · docker-compose.yml ·
           README.md · migrations_alembic/README.md · alembic_testkit.py · conftest.py）
MODIFIED = []（未触碰任何前序脏文件）
DELETED  = []
```

⇒ **只有 BATCH-B 的 9 个授权载体发生变化；无范围外对象被改**。前序历史脏文件（P10–P12 的 16 个测试文件等）**未被误判**为本批改动（它们在快照中早已存在且 sha 未变）。

---

## §8 Integration Test 状态

```text
integration suite = **NOT EXECUTED**（by design）
原因：tests/integration 下 19 个测试文件调用 reset_test_database()
      ⇒ DROP/CREATE DATABASE 会摧毁 BATCH-A 已建立的 ownership state（178 对象 → uap_migrator）
本轮实际执行：configuration/security probes = PASS（67 项 harness 断言）
             unit tests = PASS（tests/unit 全过；test_config.py 13/13）
             integration suite = NOT EXECUTED by design
```

**本报告不声称 "integration tests all passed"。** 完整 integration 回归属 BATCH-C/D 的测试基建范畴（届时需先解决 ownership 保留问题）。

---

## §9 OI 最终核对

| 编号 | 状态 |
|---|---|
| `OI-BB-11` | registered / **unchanged**（`attributes["url"]` = 程序化 override carrier；FAIL-CLOSED = 「migration 键与 attributes 均缺失」；如需"仅认 env 键"须改范围外测试，另行授权） |
| `OI-BB-13` | registered / **unchanged**（`set_main_option` 对含 `%` 的 URL 触发 configparser 插值错误 —— 既有行为；本轮负向验证已用非 `%` 形式完成同等覆盖） |
| `OI-BB-5` | resolved / **unchanged**（NO EXISTING CI CARRIER / NO CREATION AUTHORIZED） |
| **`OI-BB-14`（新增）** | **`migrations_alembic/env.py` 不可作为模块导入**（模块级即执行 alembic 迁移，alembic 设计使然）。对后续 BATCH-C 测试基建的约束：**不得** `import migrations_alembic.env` 来单测解析逻辑；如需单测 `_resolve_url`/`_assert_effective_role`，须将逻辑提取到可导入模块或经 alembic 命令行探针。本轮 F0 探针因此改用 AST 验证 |

**无未登记的新工程问题。** 本轮发现的所有失败均为 **harness 口径缺陷**（见 §11），未发现 BATCH-B 实现本身的安全缺陷。

---

## §10 变更面（本轮 B-6）

```text
本轮修改 = **0**（B-6 是只读最终核验；无任何源码/配置/测试/文档修改）
本轮新增 = 0 个仓库文件（harness 位于 %TEMP%；证据留档于 ../uap-stage3-evidence/batch_b/）
BATCH-B 全程累计 = 9 个授权载体（见 §7 NEW 清单）
```

---

## §11 自证缺陷（如实披露 · 全为 harness 口径缺陷）

```text
真实缺口（工程问题）= **0**

harness 口径缺陷 = **3 类 / 6 项断言**（首跑 60/66 → 65/67 → **67/67**；2 次复跑）：

① **AST 谓词错误（4 项连带）**：`os.environ.get(...)` 的 func.value 是 **ast.Attribute**
   （os.environ），不是 ast.Name —— 初版谓词 `isinstance(f.value, ast.Name) and f.value.id == "environ"`
   恒 False ⇒ env 读取集合为空 ⇒ BB-S05a/S05d/S06e/S06f 四项假 FAIL。
   修正 = 正确识别 `os` → `environ` → `get` 链（含 Subscript 形态）。

② **断言预期未考虑合法事实（2 项连带）**：env.py 还读取两个**既有的** lock 旋钮
   （UAP_MIGRATION_LOCK_MODE / …_TIMEOUT_SECONDS），且 migration 键经**常量别名**
   MIGRATION_URL_ENV 读取 ⇒ 「== {migration key}」这类预期必然失败。
   修正 = 断言改写为**真实安全性质**：
     · migration 路径的 env 读取集合中**不含 runtime 键**，且全部落在 UAP_MIGRATION_* 命名空间；
     · testkit 两侧函数各自只读己方键（别名解析后），并**新增**「无函数同时读两键」的交叉断言。

③ **别名未剥离包装（2 项连带）**：`_env_names_in` 对 Name 实参返回 `<var:NAME>`，
   而常量表键是裸 NAME ⇒ `_const.get('<var:…>')` 恒 miss。修正 = 剥离包装后再解析。

另登记 **F0 设计更正**：`migrations_alembic/env.py` **不可 import**（导入即执行迁移）⇒
"异常类型可导入" 探针改为 **AST ClassDef 验证** + 真实 alembic 失败输出（BB-S03b）。
该事项已升格为 **OI-BB-14**（对 BATCH-C 测试基建的约束）。

通则重申（教训 51/68/74）：**凡 token 可能以否定式/自引用/别名形态合法出现，断言前必须先做归属裁决**；
本轮 6 项失败**无一**是 BATCH-B 实现的缺陷。
```

---

## §12 BATCH-B FINAL GATE

```text
BATCH-B FINAL SECURITY VERIFICATION = PASS

BB-S01 = PASS   BB-S02 = PASS   BB-S03 = PASS   BB-S04 = PASS
BB-S05 = PASS   BB-S06 = PASS   BB-S07 = PASS   BB-S08 = PASS

effective migration identity = uap_migrator（current_user 与 session_user 一致）
effective runtime identity   = uap_app（current_user 与 session_user 一致）
FAIL-CLOSED negative probe   = PASS（MigrationIdentityError · 逐字错误边界已记录）
cross-fallback negative probes = PASS（双向 5 项，含角色断言失败分支）
Alembic static DSN result      = 0 可执行 sqlalchemy.url · 旧 dev DSN 未重现
settings runtime boundary      = migration 键不在 model_fields · runtime 键语义不变
testkit/conftest boundary      = 双 DSN 单向读取（AST 别名解析后）+ 无交叉路径 + attributes carrier 保留
protected-object result        = 0007/C2/PDL/Contract/DecisionRecord/roles/ownership/grants 全 UNCHANGED
round-relative scope           = NEW = 9 授权载体 · MOD = [] · DELETED = []
integration tests              = NOT EXECUTED（by design · 19 文件会 reset_test_database）
unit tests                     = PASS
new OI                         = OI-BB-14（env.py 不可导入 ⇒ BATCH-C 测试基建约束）
HEAD                           = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e（未动）
commit = 0      tag = 0      push = 0      0016 = ABSENT      0017 = ABSENT      C2 = UNCHANGED
```

---

## §13 仍禁止 / 下一步

```text
## 本轮与 BATCH-B 全程均未做
C2 rewrite · CREATE/ALTER/DROP ROLE · GRANT/REVOKE · ALTER OWNER · 0016 migration 创建 ·
alembic upgrade/downgrade（除 at-head no-op 身份探针外无任何 schema 变更）·
runtime cutover（运行中进程未重启，配置分离在重启后才对运行进程生效）·
P13 · BATCH-C · BATCH-D · commit · tag · push

## HARD STOP
BATCH-B FINAL = PASS ⇒ 停止。
等 Human 逐字：BATCH-C IMPLEMENTATION START AUTHORIZED
（下一阶段处理 BATCH-C / 0016 Trust Boundary + CC-7 —— 含 OI-G-3 的 schema CREATE 前置
  与 OI-BB-14 的测试基建约束。）
```

**END OF OPEN-P10-1 BATCH-B FINAL EXECUTION REPORT（2026-09-27 · B-1…B-6 全 PASS · `BATCH-B FINAL SECURITY VERIFICATION = PASS` · `BATCH-C/D = NOT AUTHORIZED` · `0016/0017 = ABSENT` · `commit/tag/push = 0`）**
