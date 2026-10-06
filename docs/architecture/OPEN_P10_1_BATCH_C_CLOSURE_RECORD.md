# OPEN_P10_1_BATCH_C_CLOSURE_RECORD

> UAP · OPEN-P10-1 · BATCH-C（Trust Boundary / 0016 + CC-7）实施收口
> 状态：STRICT READ-ONLY 验收 · 零工程变更 · 未 commit / 未 tag / 未 push
> 日期：2026-09-27 · 本文件位于 Agent 工作区，不在 UAP 仓库内（待 Human 指示是否落入 docs/architecture/）

---

## 1. BATCH-C Scope

```text
目标   = Trust Boundary 落地：0016_open_p10_1_trust_boundary（CC-7 函数改写）+ P0 env.py 事务归属修复
决策   = OPEN_P10_1_BATCH_C_DECISION_RECORD.md（sha256[:16] 9efbc3fe031387d0）
契约   = OPEN_P10_1_IMPLEMENTATION_CONTRACT.md（sha256[:16] 2c1fec371de5ab3b）
CF     = CF-C-1=A · CF-C-2=A · CF-C-3=A · CF-C-4=C（integration 延后 BATCH-D）· CF-C-5=B · CF-C-6=A · CF-C-7=CONFIRM
```

## 2. 0016 Implementation

```text
file          = migrations_alembic/versions/0016_open_p10_1_trust_boundary.py
sha256        = 10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544（未变）
revision      = 0016_open_p10_1_trust_boundary（30 chars ≤ 32）
down_revision = 0015_p12_indexes
branch_labels = None · depends_on = None
scope         = CC-7 only（op.execute：升级写入 CC-7 变体；downgrade 恢复 0007 pre-image）
             无 GRANT / REVOKE / ALTER / OWNER / CREATE TABLE / INSERT（P13 seed 为 0）
```

## 3. P0 env.py Correction

```text
pre-image  = cc569fd54e5e769e6651a76f0ff8a8c5658a1d1168f0c9065f53fa173ac98ed6
post-image = 577f0d0e018b5859696e61b4f405ab2b4f6a9d991b423591adc2330bc9ff040a
diff       = +4 / -0；唯一语义新增 connection.rollback()
详见 P0_FIX_ACCEPTANCE_RECORD.md
```

## 4. Privilege Window

```text
#1  CREATE pre  = false
    GRANT CREATE ON SCHEMA public TO uap_migrator（grantor = uap · D-OP101-04）
    CREATE during = true · identity probe = uap_migrator / uap_migrator
#2  REVOKE -> CREATE pre = false -> GRANT -> CREATE during = true -> upgrade #2
    REVOKE -> CREATE final = false
    final nspacl = {pg_database_owner=UC/pg_database_owner,=U/pg_database_owner,uap_app=U/pg_database_owner}（与窗口前逐字一致）
窗口记忆点：GRANT/REVOKE 均为 orchestration 动作，未写入任何 migration 文件（CF-C-5=B）
```

## 5. Transaction Evidence（真实事务生命周期）

插桩方式：`PYTHONPATH` + `sitecustomize` 注入真实 `alembic` CLI 进程（仓库零改动），覆盖
DBAPI（`psycopg.Connection.commit/.rollback`）+ SQLAlchemy 事件（begin/commit/rollback）+ `MigrationContext.begin_transaction()` 返回类型。

三份日志（`work/upgrade1_instrument.log` · `work/downgrade_instrument.log` · `work/upgrade2_instrument.log`）逐项一致：

```text
assertion rollback        = observed（DBAPI_ROLLBACK：新增 connection.rollback()）
transaction begin         = observed（SA_BEGIN · ALEMBIC_BEGIN_TX returned=_ProxyTransaction）
_in_external_transaction  = False（缺陷特征消失）
migration SQL             = observed（SQL_CC7 · CREATE OR REPLACE FUNCTION ...）
version bookkeeping SQL   = observed（SQL_VER · UPDATE alembic_version）
COMMIT                    = observed（SA_COMMIT + DBAPI_COMMIT）
post-commit persistence   = observed（独立新连接/新进程复读一致）

未再出现的缺陷特征：
  _in_external_transaction=True  出现次数 = 0
  nullcontext 作为外层事务      = 0（仅出现的 nullcontext 为 per-migration 路径且 _in_external_transaction=False）
  no COMMIT                    = 0
  rollback on close 致版本蒸发  = 0
```

## 6. Upgrade / Downgrade 序列

```text
upgrade #1   0015 -> 0016   PASS（在线 · 非 --sql · 非 at-head no-op）
downgrade    0016 -> 0015   PASS
upgrade #2   0015 -> 0016   PASS（可重复性证明，非一次性偶然成功）

每次均：version 表前移 + 副作用落库 + COMMIT 证据
```

## 7. CC-7 Fingerprints

```text
pre-image   = 6867874166ae36966763c1026ab2af19（0007 原始体）
post-image  = 185e95be8bc4304edbcd3f4d5cda1eff（CC-7 变体）
downgrade 恢复 = 6867874166ae36966763c1026ab2af19（精确逐字恢复，独立 session 验证）
upgrade #2 再次形成同一 post-image = 185e95be8bc4304edbcd3f4d5cda1eff

不变式：owner = uap_migrator · language = plpgsql · prosecdef = false · provolatile = v
        signature = () RETURNS trigger · pronargs = 0
trigger：tg_acl_subject_types_protect · tgenabled = 'O' · tgparentid = 0 · tgisinternal = false
```

## 8. Security Regression

```text
S1 wrong migration role          -> MigrationIdentityError · exit=1
S2 missing migration DSN         -> MigrationIdentityError（FAIL-CLOSED，无 fallback）· exit=1
S3 valid migration DSN + current -> 0016_open_p10_1_trust_boundary · exit=0
S4 DSN separation                -> env.py 只读 UAP_MIGRATION_DATABASE_URL；settings.py 只读 DATABASE_URL
                                    runtime 连接实测 current_user = uap_app
S5 advisory lock fail mode       -> MigrationLockError（持锁时）· exit=1；释放后 exit=0
```

## 9. Protected-Object Regression

```text
0007     9e0105b9dc4281755a313b6477cc755e07f4b356403af169e69529698b8ec1ef   unchanged
PDL      a83fde5c5760525233f4c56043bd39b11eaa950520be2b27ed4790c90673ef56   unchanged
Contract 2c1fec371de5ab3bc91a077e2879109afc2fc801bd32a6f3b95cfce1cd0c5931   unchanged
Record   9efbc3fe031387d0e0c30c629b34b22351815bb8e5911ea8c7d4a1fda1734882   unchanged
0016     10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544   unchanged
0017     ABSENT

roles                 = 4（uap super；uap_seed/uap_migrator/uap_app 六项属性全 false，canlogin=t）unchanged
ownership             = pg_class 156 + pg_proc 22 = 178 · residual 0
uap_app grants        = 5（alembic_version:SELECT · audit_logs:INSERT/SELECT · audit_logs_202609:INSERT/SELECT）
default_acl           = 0
user memberships      = 0
C2 trigger            = enabled（non-internal）
registry rows         = 0 · agents 族 = 0
parent triggers       = 39（非内部合计 40）
正式库 uap            = 0 表
```

## 10. Known Discrepancy（登记，未修复）

```text
ID（提案）  = OI-G-4   ← 沿用现有 OI 编号体系；编号最终以 Human 确认为准
对象        = scripts/generate_build_info.py 与其测试 tests/unit/test_generate_build_info.py
现象        = 测试硬编码 REV = "0015_p12_indexes"，而 derive_head() 实测返回 0016_open_p10_1_trust_boundary
            -> test_derives_the_unique_head_from_the_repository_graph FAILED
定性        = 测试/构建工具的「期望值滞后」；自 BATCH-C 创建 0016 文件起即不成立
归属        = 非 P0 env.py 修复引入（该测试为离线；不读 env.py、不连库）
当前状态    = 未修复（不在 BATCH-C 收口 scope 内，本轮禁止修改代码）
建议归属    = BATCH-D / maintenance scope
附加说明    = 同文件另有 6 条 ERROR，源于沙箱禁止写 %TEMP%\pytest-of-19217（环境噪声，非代码缺陷）
```

## 11. Integration Limitation

```text
integration suite = NOT EXECUTED
原因 = CF-C-4=C：19 个含 reset_test_database() 的文件会 DROP/CREATE 数据库，摧毁 BATCH-A ownership 基线
已执行（targeted, 非 reset）：
  tests/unit + tests/architecture（排除 test_generate_build_info.py） = 217 passed
  tests/security（排除 tests/security/test_authorization_security.py） = 5 passed
未执行：
  tests/integration/**（18 个）+ tests/security/test_authorization_security.py = 共 19 个文件
  tests/unit/test_generate_build_info.py（见 §10 既有 discrepancy）
```

## 12. Final DB State

```text
alembic_version = 0016_open_p10_1_trust_boundary
uap_migrator CREATE = false（窗口已关闭）
registry rows = 0 · agents 族 = 0
C2 = CC-7 post-image（185e95be8bc4304edbcd3f4d5cda1eff）
```

> 即：0016 已落地，但 P13 尚未执行。

## 13. Git

```text
HEAD = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e · branch = main · tags = 8 · remote = 0
dirty = 104（68 ?? + 36 M + 0 D）
round 允许修改 = migrations_alembic/env.py（唯一）
BATCH-C 既定 artifact = 0016_open_p10_1_trust_boundary.py（内容未变）
未出现：0017 · P13 files · PDL/Contract/Decision Record 修改
commit = 0 · tag = 0 · push = 0
```

---

```text
BATCH-C IMPLEMENTATION = ACCEPTED
BATCH-C CLOSURE = PASS

注意：BATCH-C CLOSURE PASS 不等于允许进入 P13。
```

