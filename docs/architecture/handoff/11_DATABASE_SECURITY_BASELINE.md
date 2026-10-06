# 11_DATABASE_SECURITY_BASELINE — 数据库安全基线（2026-09-27 实测）

> 目标库 = `uap_b1_test`（唯一处于迁移链头）。实测口径：psql 只读查询；证据见 12。

## 角色与属性

| 角色 | superuser | createdb | createrole | replication | bypassrls | 说明 |
|---|---|---|---|---|---|---|
| `uap` | true | true | true | true | true | 集群引导 / deployment-ops authority（D-OP101-04） |
| `uap_seed` | false | false | false | false | false | RM-D 种子角色（未使用） |
| `uap_migrator` | false | false | false | false | false | **唯一 migration execution identity** |
| `uap_app` | false | false | false | false | false | 唯一 runtime identity |

- 用户级 `pg_auth_members` = **0**（成员关系全为 PG 内建）
- 口令 = 角色名（BATCH-A 约定；`rolpassword` 非空；勿写入任何项目文件）
- `pg_default_acl` = **0**

## schema 特权（关键）

```text
uap_migrator CREATE on public = false   ← 默认态（窗口期才为 true，结束必须回收）
uap_app      CREATE on public = false
uap_app      USAGE on public = true（5 项授权之一）
public nspacl = {pg_database_owner=UC, =U, uap_app=U}
```

### OI-G-3 的决定性证据（为何 CREATE 是 0016 真实前置）

```text
CREATE TABLE          → denied（uap_migrator）
CREATE OR REPLACE 自有既有函数 → denied（uap_migrator）
```

即：**即使函数 owner 是自己，替换定义仍需要 schema CREATE** ⇒ 0016（CC-7 改写）执行前必须临时 GRANT，验证后必须 REVOKE（CF-C-5=B）。

## 所有权与授权

```text
pg_class（public，p/r/i/I）= 156，全部 owner = uap_migrator（残留 0）
pg_proc（public）          = 22， 全部 owner = uap_migrator
uap_app 显式授权（非 owner 合成行口径）= 恰 5 项：
  SCHEMA public USAGE · alembic_version SELECT · audit_logs(+当期分区) INSERT/SELECT
uap_migrator / uap_seed 显式授权 = 0
```

## C2（Trust Boundary 现行体）

```text
函数  = public.enforce_acl_subject_types_protect()（0007:78 首建；触发器 tg_acl_subject_types_protect）
md5(pg_get_functiondef) = 6867874166ae36966763c1026ab2af19（pre-image 指纹）
owner = uap_migrator · LANGUAGE plpgsql · prosecdef = false · provolatile = v
语义  = runtime INSERT denied · DELETE denied · key UPDATE denied（registry = migration-controlled）
留档  = uap-stage3-evidence/cc7_c2_functiondef_preflight.sql
```

## 触发器 / 数据面

```text
父级触发器（tgparentid=0 且 NOT tgisinternal）= 39（克隆 40 行）
acl_subject_types 行数 = 0（P13 前必须保持）
agents / agent_versions / agent_permissions / tool_executions 行数 = 0
```

## 库与其他

```text
uap        = 0 表（formal；守卫 test_sec4_formal_database_untouched 要求保持）
uap_b1_test= 唯一链头库（@0015；0016 未持久化）
uap_test   = pytest 默认库（conftest DATABASE_URL）
Docker     容器名 = uap-postgres（PG16-alpine）；pg_hba：容器内 socket trust；宿主 TCP 经 bridge → scram（需口令）
```

## 不可触碰清单（绝对）

```text
roles 4 个及其属性 · 178 ownership 拓扑 · uap_app 恰 5 项授权 · pg_default_acl=0
C2 函数/触发器语义 · 39 父级触发器启用状态 · 正式库 uap 的 0 表状态
```
