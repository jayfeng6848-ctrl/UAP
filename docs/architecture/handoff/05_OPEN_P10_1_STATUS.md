# 05_OPEN_P10_1_STATUS — OPEN-P10-1 完整状态

## 角色拓扑（RM-D · 实测 2026-09-27）

集群级非 `pg_%` 角色 = **4**：

```text
uap           superuser=true（集群引导/deployment-ops authority，D-OP101-04；BATCH-A 台账原文）
uap_seed      NOSUPERUSER·NOCREATEDB·NOCREATEROLE·NOREPLICATION·NOBYPASSRLS·LOGIN
uap_migrator  同上（全部 false）
uap_app       同上（全部 false）
```

用户级 `pg_auth_members` = **0**（既有成员关系全为 PG 内建）；`pg_default_acl` = 0。

## BATCH-A（角色 / 所有权 / 授权面）= **PASS**

```text
三角色建立 + 幂等复跑 3/3 NOOP                     （A1）
最小 membership = 空集；7 组禁止关系否定断言成立    （A2）
所有权 178/178（35 表含 3 子分区 + 0 残留索引 + 22 函数）
  uap → uap_migrator；pg_class/pg_proc/pg_type 零残留；无 mixed ownership
  逐对象 WHO/WHAT/OLD/NEW/WHY 台账 178 行           （A3）
uap_app runtime 边界 = 恰 5 项显式授权：
  SCHEMA public USAGE（不授 CREATE）
  alembic_version SELECT
  audit_logs + 当期分区 各 INSERT/SELECT            （A4）
V-1…V-9 会话探针 15/15：
  uap_app 不能 DDL · 不能 SET ROLE · 不能 SET SESSION AUTHORIZATION
  uap_migrator/uap_seed 显式授权 = 0                （A5）
```

## BATCH-B（migration/runtime 配置分离）= **FINAL SECURITY VERIFICATION = PASS**

```text
B-1 PASS  env.py 重写（单一解析键 UAP_MIGRATION_DATABASE_URL + attributes override + FAIL-CLOSED
          MigrationIdentityError + 角色断言 _assert_effective_role）· alembic.ini 移除可执行 DSN
B-2 PASS  真实 CLI 探针（成功/失败分支）※ 见 08：该探针为 at-head no-op，掩盖了后发现的 P0 缺陷
B-3 PASS  settings.py 仅注释（DATABASE_URL = RUNTIME-ONLY）
B-4 PASS  testkit 双 DSN fixture（migration_dsn FAIL-CLOSED / runtime_dsn）23/23
B-5 PASS  文档 4 载体同步（.env.example/compose/README/migrations README）39/39
B-6 PASS  独立安全核验 67/67（AST 级边界 + 负向探针）
```

形成的最终安全边界（双向禁 fallback）：

```text
runtime   = DATABASE_URL → settings.DATABASE_URL → uap_app
migration = UAP_MIGRATION_DATABASE_URL → uap_migrator（env.py FAIL-CLOSED）
```

## BATCH-C（Trust Boundary / 0016 + CC-7）= **BLOCKED**

```text
DECISION       = REGISTERED（8/8 必需 + 3/3 补充；载体 OPEN_P10_1_BATCH_C_DECISION_RECORD.md）
PRE-FLIGHT     = PASS（P01…P20 · 契约冻结 · OI-DC-1=INLINE · OI-DC-2=窗口期 runbook）
0016 文件      = CREATED（静态审计 PASS）
0016 执行      = FAILED-TO-PERSIST（env.py P0 缺陷 · 见 08_CURRENT_BLOCKER.md）
窗口状态       = 已回收（uap_migrator CREATE = false · 基线完整恢复）
```

## BATCH-D（integration / 终验）= **NOT AUTHORIZED**

`CF-C-4 = C`：integration/reset 冲突延后 BATCH-D；19 个会 `reset_test_database()` 的测试文件禁跑（见 10）。
