# 07_REVISION_AND_MIGRATION_RULES — revision 解析与迁移规则

## 历史授权标签 ≠ Alembic revision

```text
0016_open_p10_1_database_trust_boundary   ← 39 字符：历史 canonical identity 标签
                                            （RV-A 裁定后永久降级，不得作 revision/文件名）
0016_open_p10_1_trust_boundary            ← 实际 Alembic revision（30 字符）
```

（裁定来源：`OPEN_P10_1_REVISION_RESOLUTION_RECORD.md` · `REQ-4 = RV-A`）

## 契约（不可违反）

```text
filename == revision                        0016_open_p10_1_trust_boundary(.py)
revision ≤ 32 chars                         30 ✓
down_revision = 0015_p12_indexes
branch_labels = None · depends_on = None
single head（无分支/无多头/无 duplicate）
历史迁移 0001–0015 不可改写；更正只可新增 migration
alembic_version.version_num = varchar(32)（39 字符串物理不可插入，活体实测过）
```

## 当前链（.py ×16）

```text
0001_baseline → 0002_b1_0_infrastructure → 0003_b1_1_root_identity → 0004_b1_2_tenant_space
→ 0005_b1_3_authorization → 0006_b1_3_bootstrap_state → 0007_b1_4_resource_acl → 0008_b1_5_tool_registry
→ 0009_timestamp_precision → 0010_b1_6_ai_gateway → 0011_p09_agent_tool_permission
→ 0012_authz_enforcement → 0013_p10_event_audit → 0014_p11_triggers → 0015_p12_indexes
→ [0016_open_p10_1_trust_boundary]   ← 文件已建；DB 版本仍 0015（执行未持久化，见 08）
```

## P13

```text
0017_p13_seed   ← 已裁定归属（D-OP101-03），由后续 P13 Implementation Contract 正式登记
0017 当前状态   = ABSENT
```

## 执行命令（契约）

```text
CLI 连接：UAP_MIGRATION_DATABASE_URL = postgresql+psycopg://uap_migrator:<pw>@localhost:5432/uap_b1_test
          （方言必须 postgresql+psycopg —— venv 无 psycopg2；testkit/README 同族）
升级目标：alembic upgrade 0016_open_p10_1_trust_boundary   （钉自己的 revision，不用 head）
正式库 uap：本轮不得首次执行 migration（0 表为守卫基线）
```

## 环境事实（实测）

```text
角色口令 = 角色名（BATCH-A 约定；rolpassword 非空）
pg_hba：容器内 local socket = trust；宿主 TCP 经 docker bridge 源 IP ≠ 127.0.0.1 → 落 scram 规则 → 需口令
env.py FAIL-CLOSED：解析链 attributes["url"] → UAP_MIGRATION_DATABASE_URL → RAISE MigrationIdentityError
⚠️ env.py 存在 P0 缺陷使在线 upgrade 不持久 —— 见 08_CURRENT_BLOCKER.md（修复未授权）
```
