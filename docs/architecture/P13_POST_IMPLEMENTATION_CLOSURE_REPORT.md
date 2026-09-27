# UAP — P13 POST-IMPLEMENTATION CLOSURE REPORT

> ## 轮次与边界
>
> ```text
> 轮次      = P13 POST-IMPLEMENTATION CLOSURE（只读审计 + 证据固化）
> 性质      = 实施闭环证据建立；不含代码 / 迁移 / DB 变更
> 本轮未做  = 未创建 migration · 未修改 0017 / 0016 / env.py · 未改 PDL 冻结正文 ·
>             未改 Contract 决策正文 · 未改 Matrix 验收结果 · 无新 DDL / DML ·
>             未 commit / tag / push · 未触及 P14 / P15
> 本文件    = 新增（append-only 新增文件，不删除任何历史）
> ```

---

# 1. Baseline（§2）

```text
HEAD            = 034ee97c315e5d483acb7ac4b7e8e0eb992ef10e
branch          = main
dirty           = 110（modified 36 · untracked 74）
tags            = 8 · remote = 0
migration files = 17（0001 … 0017）
migration head  = 0017_p13_seed
alembic_version = 0017_p13_seed

0017 sha256 = 1251f0b10f79719379d452798baddfee2df0c2363ae0e56e3182ac36e3773a3e
0016 sha256 = 10284d98de6be342d485f09b7a23d4ef02bcae58467d9f3fc5248cc8cb6e2544
env.py sha  = 577f0d0e018b5859696e61b4f405ab2b4f6a9d991b423591adc2330bc9ff040a
```

---

# 2. Migration Artifact Audit（§3）

```text
file            = migrations_alembic/versions/0017_p13_seed.py（235 行）
revision        = 0017_p13_seed
down_revision   = 0016_open_p10_1_trust_boundary
branch_labels   = None
depends_on      = None
filename == revision = true
```

范围核对（扫描结果）：

```text
存在的动作（仅这三类目标表）：
  INSERT INTO public.acl_subject_types   （:90）
  INSERT INTO public.permissions         （:103）
  INSERT INTO public.role_permissions    （:142）
  DELETE FROM public.role_permissions    （:219 · downgrade 路径）
  DELETE FROM public.acl_subject_types   （:229 · downgrade 路径）
  DELETE FROM public.permissions         （:233 · downgrade 路径）

不存在（扫描命中 = 0）：
  create_table · create_index · create_foreign_key · create_check_constraint ·
  create_unique_constraint · add_column · alter_column · drop_* ·
  CREATE TABLE / ALTER TABLE / CREATE INDEX / CREATE FUNCTION / CREATE TRIGGER / DROP
```

---

# 3. Decision Traceability（§4）

追溯链与落点：

```text
D-AUTH-18（canonical subject vocabulary = USER / ROLE / AGENT）
  → Contract §21.5（INSERT acl_subject_types = 3 行 user / role / agent）
  → Matrix SEED-N1（count = 3 · 集合精确 {user, role, agent}）
  → 0017 :90（registry seed）
  → 证据：独立会话实测 registry keys = ['agent','role','user']，count = 3

D-P13-04（register-only agent subject）
  → Contract §9 / §21.5
  → Matrix SEED-N8（agents 族 = 未变）
  → 0017（无 agents 族写入）
  → 证据：agents / agent_versions / agent_permissions / tool_executions = 0

D-P13-01（12 canonical allow permissions）
  → Contract §21.2（逐行 12 项）
  → Matrix SEED-N2（count = 12 · 无 deny / 无 system.* / 无 manage / write）
  → 0017 :103
  → 证据：permissions = 12 · is_system 全 true · action ∈ canonical 12 verb

IMPL-02 = A（role_permissions = platform_admin × 12 × allow）
  → Contract §21.2（精确清单）
  → Matrix SEED-N3（count = 12）
  → 0017 :142
  → 证据：role_permissions = 12 · 全部 (platform_admin, *, allow)

IMPL-01 = A（users 不创建）
  → Contract §21.1
  → Matrix SEED-N4
  → 0017（无 users 写入）
  → 证据：users = 0

IMPL-03 = A（不写 audit_logs）
  → Contract §21.3
  → Matrix SEED-N5
  → 0017（无 audit_logs 写入）
  → 证据：audit_logs = 0

IMPL-04 = C（downgrade FAIL-CLOSED · 仅移除 migration-owned）
  → Contract §21.4
  → Matrix DOWNG-N1..N4
  → 0017 downgrade()（五重前置检查 + RAISE + 0 DELETE 语义）
  → 证据：downgrade 实测移除 27 行（12+3+12），users 全程无 DELETE

D-P13-02（platform_admin 归 0005 · 只读校验）
  → Contract §10 / §21.5
  → 0017 _platform_admin_id()（找不到即 RAISE）
  → 证据：roles 计数始终 = 1 · P13 零 roles 写入

D-P13-05 / 07 / 08（零 tenant / space / membership / PM）
  → Matrix SEED-N7
  → 0017（无写入）
  → 证据：tenants / spaces / memberships / platform_memberships = 0

D-P13-09（十步唯一拓扑）/ D-P13-10（幂等）
  → 0017 upgrade 顺序 registry → permissions → role_permissions
  → 每条 seed 语句带 WHERE NOT EXISTS；冲突 = 显式失败（禁 ON CONFLICT DO NOTHING）
  → 证据：扫描无 ON CONFLICT；at-head 重跑 = no-op，计数不变

D-P13-11（39 triggers 全启用下执行）
  → 0017 无 DISABLE / ALTER / DROP TRIGGER
  → 证据：父级触发器 = 39 未变 · C2 md5 = 185e95be8bc4304edbcd3f4d5cda1eff 未变

D-P13-12 / D-P13-14（FAIL-CLOSED · 不新增 ownership marker）
  → 0017 downgrade 前置检查（baseline 精确相等 / users=0 / 无 resource_permissions 依赖）
  → 证据：无 seed_batch / migration_owned / seed_origin 列（schema 计数未变）

D-P13-15 + D-OP101-05（CC-7 受信迁移边界）
  → B-1 Amendment §14.1/§14.2（canonical statement）
  → 0017 以 uap_migrator 身份执行 registry 写（受信分支放行）
  → 证据：migration 身份 INSERT 可用；runtime（uap_app）三表 INSERT 全 DENIED
```

```text
Decision → Contract → Matrix → Migration → Evidence 链 = COMPLETE（无断链）
```

---

# 4. Database Final State（§5）

```text
alembic_version      = 0017_p13_seed
acl_subject_types    = 3      {user, role, agent}
permissions          = 12     D-P13-01 canonical
role_permissions     = 12     platform_admin × 12 × allow
users                = 0
audit_logs           = 0
roles                = 1（platform_admin · 未变）
tenants = 0 · spaces = 0 · platform_memberships = 0 · resource_permissions = 0
agents = 0 · agent_versions = 0 · agent_permissions = 0 · tool_executions = 0
events = 0 · platform_state = 1（uninitialized）
```

---

# 5. Protected Object Regression（§6）

```text
对象                        measured        reference       result
env.py sha256               577f0d0e…       577f0d0e…       UNCHANGED
0016 sha256                 10284d98…       10284d98…       UNCHANGED
C2 md5                      185e95be8bc4304edbcd3f4d5cda1eff   同前   UNCHANGED
C2 trigger tgenabled        O               O               UNCHANGED
pg_class public             156             156             UNCHANGED
pg_proc public              22              22              UNCHANGED
parent triggers             39              39              UNCHANGED
roles count                 4               4               UNCHANGED
user memberships            0               0               UNCHANGED
ownership residual          0               0               UNCHANGED
uap_app grants              5               5               UNCHANGED
default_acl                 0               0               UNCHANGED
uap_migrator CREATE         false           false           UNCHANGED
formal db uap tables        0               0               UNCHANGED

P09 对象（agents 族）    = 存在 · 0 行 · 未变
P10 对象（events / audit_logs）= 存在 · 0 行 · 未变
P12 对象（索引面）        = pg_class 计数未变（无新增索引）
```

---

# 6. 事务证据（Implementation Evidence 回溯）

```text
upgrade #1   exit=0 · SA_COMMIT + DBAPI_COMMIT observed · version 0016 → 0017
downgrade    exit=0 · SA_COMMIT + DBAPI_COMMIT observed · version 0017 → 0016
upgrade #2   exit=0 · SA_COMMIT + DBAPI_COMMIT observed · version 0016 → 0017
at-head 重跑  exit=0 · no-op · 计数不变

三次运行中 ALEMBIC_BEGIN_TX 均返回 _ProxyTransaction 且 _in_external_transaction=False
（env.py P0 修复语义保持 · 无 external-transaction swallow / 无 rollback-on-close / 无 missing commit）

persistence = PROVEN（每次均由独立新进程 + 新连接复读一致）
日志留档（仓库外）：work/p13_upgrade1.log · work/p13_downgrade.log · work/p13_upgrade2.log
```

---

# 7. 本轮工程变更

```text
DDL = 0 · DML = 0 · migration execution = 0
0017 内容 = 未修改（sha 1251f0b1…）
新增文件 = 本报告 + P13_RELEASE_PREP_GATE_REPORT.md
commit = 0 · tag = 0 · push = 0
```

---

# 8. 结论

```text
P13 POST-IMPLEMENTATION CLOSURE = PASS
P13 IMPLEMENTATION = ACCEPTED（闭环证据完整）
```

> 本报告不产生任何授权。下一步须等待 Human 的 `COMMIT AUTHORIZATION`。

---

**END OF P13 POST-IMPLEMENTATION CLOSURE REPORT（2026-09-27 · migration head = 0017_p13_seed · closure evidence = COMPLETE · commit/tag/push = 0）**
