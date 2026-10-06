# 02_ARCHITECTURE_BOUNDARY — 架构与边界

## 分层

```text
apps → agent → services → intelligence → core → infrastructure
domains（旁挂，可 → core）
```

- `core → domains` **禁止**；`domains → core` 允许；
- core 禁行业词汇（restaurant/menu/employee/family/company…）；
- core / intelligence 禁直接 import 厂商 SDK，只经 Provider Adapter（AI 厂商 = `ai_providers` 数据行，非代码分支）；
- Agent 禁直连 DB：`Agent → Policy → Tool → Service → Database`；
- `services/` = 服务层与业务持久化唯一归属（`D-PLAT-01/03`）；
- **仅写在文档的规则必须落为 `tests/architecture` 测试**（无测试 = 非强制）；
- **Core → Domain 越界 = 0 · Guard = 9 passed**（AST 守卫历史验收，见 DEPENDENCY_RULES.md 与 tests/architecture）。

## 七类边界

| 边界 | 规则 |
|---|---|
| Core | 零行业词汇 · 零 Domain 依赖 · 纯机制 |
| Domain | 可用 core；自带 schema 语义；经 services 持久化 |
| Infrastructure | DB/外部 IO 实现；被 core 以上各层经接口使用 |
| Migration | Alembic 单链（0011 之后为 protected chain）；历史迁移不可改写 |
| Runtime | `uap_app` 身份；不持 DDL；5 项显式授权封顶 |
| Authorization/ACL/Policy | 默认 deny · deny 优先 · FAIL CLOSED · `Agent → Policy → Tool → Service → DB` |
| AI Gateway | `ai_providers` 数据行驱动；HIGHLY_CONFIDENTIAL 禁降级（DB CHECK） |

## ⭐ 当前阶段最重要的安全边界：migration identity 与 runtime identity 分离

```text
DATABASE_URL                → runtime   → settings.DATABASE_URL → uap_app（仅运行时）
UAP_MIGRATION_DATABASE_URL  → Alembic migration → uap_migrator（仅迁移）
```

严格（BATCH-B 冻结语义）：

```text
DATABASE_URL               ↛ migration fallback（env.py 不读它）
UAP_MIGRATION_DATABASE_URL ↛ runtime fallback（settings 不读它）
```

env.py（`migrations_alembic/env.py`）解析链：`config.attributes["url"]` → `UAP_MIGRATION_DATABASE_URL` → 缺失即 RAISE `MigrationIdentityError`（FAIL-CLOSED）；连接后 `_assert_effective_role`（env.py:95）校验 `current_user == URL 所指角色`，不符即 RAISE。**双向禁 fallback 不得在任何"顺手修复"中被破坏。**

> ⚠️ 当前该文件存在 P0 缺陷（断言时序导致升级不持久），见 `08_CURRENT_BLOCKER.md`；修复未授权前不得触碰 env.py。

## 数据层铁律（CORE_DOMAIN_MODEL.md）

- ID = UUIDv7（应用层）· 时间列仅 `timestamptz(3)` UTC · 分区表 PK 含 `occurred_at`；
- Resource = 注册表 + 域表共享主键 1:1；禁无外键多态弱引用；
- 授权 = RBAC(平台∪租户∪空间) + ABAC + resource ACL；**默认 deny · deny 优先 · 错误即拒绝**；
- `events` = transactional outbox；`audit_logs` 不可变；无全局 soft delete；
- 业务删除 FK `RESTRICT`；保留期 audit 365d / events 30d / 其他 90d。
