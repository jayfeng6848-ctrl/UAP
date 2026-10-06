# P20 COMPANY DOMAIN DEPENDENCY MAP（设计提案 · 未冻结 · 未实现）

```text
性质 = Company 域契约的依赖方向设计 + 现有架构守卫的硬约束核对
依据 = 只读勘验：tests/architecture/test_dependency_rules.py（63 项守卫中的依赖规则）
```

## 1. 平台既有方向（硬约束 · 守卫强制）

```text
core  →  （不依赖任何上层）          守卫 G-1/G-2：core 不得 import domains/apps/services/infrastructure/
                                              agent/intelligence/sqlalchemy/psycopg
domains → core（仅此）               守卫 G-4（hard）：domains 不得 import services / infrastructure
domains → 无 schema / 无持久化       守卫：domains 文本中不得出现 "create table" / "sqlalchemy"
domain manifest = placeholder        守卫：所有域 manifest 必须 status=placeholder · tables=[]
services → core / services / infrastructure / intelligence
apps   → services（guards 禁止 apps 直接持有业务持久化）
```

## 2. 由此推出的落点结论（强约束，不是偏好）

```text
L1 纯契约（实体、值对象、端口 Protocol、错误码、生命周期表）→ **domains/company/**
   理由：不触库、不依赖 services/infrastructure，符合 G-4 与"无 schema/无 sqlalchemy"守卫。

L2 用例编排（授权 → 校验 → 写入 → 审计 → 提交）→ **services/company/（或 services/use_cases/company.py）**
   理由：requires AuthorizationService（services）、RuntimeDatabase（infrastructure）、audit writer；
   若放在 domains/ 将直接违反 G-4（硬失败）——与 P16 `services/agent/`、P18 `services/use_cases/control_plane.py` 同型。

L3 传输层（apps/api/routes/company.py）→ 本轮与实现轮均未授权；仅登记为未来落点。

L4 迁移与 DDL → 只属于 migrations_alembic（0019 已完成）；域与用例层永不建表、永不 DDL。
```

## 3. 允许 / 禁止导入矩阵（Company 域相关模块）

| 模块（提案路径） | 允许 import | 禁止 import |
| --- | --- | --- |
| `domains/company/contracts.py`（实体/值对象） | 标准库 · `core.*` | `services` · `infrastructure` · `apps` · `sqlalchemy` · `psycopg` |
| `domains/company/ports.py`（仓储/审计/授权端口 Protocol） | 标准库 · `core.*` · 上述 contracts | 同上（端口不得引用实现） |
| `domains/company/errors.py` | 标准库 | 同上 |
| `services/company/repository.py` | `core.*` · `services.reads` · `sqlalchemy` · `infrastructure.runtime.errors` | `apps` · 不得自建事务 |
| `services/company/use_cases.py` | 上述 · `services.authorization` · `services.audit.writer` · `infrastructure.database.runtime` | `apps` · 不得新建第二授权引擎 |
| `apps/api/routes/company.py`（未授权） | `services.company` · `services.context` | 直接 SQLAlchemy 业务持久化 |

## 4. 需要同步变更的架构守卫（重要 · 实现轮的前置条件）

```text
W1 `test_domain_manifests_are_placeholders` 断言每个域 manifest 满足 `status == "placeholder"`
   且 `tables == []`。Company 域一旦落地实体/表映射，**该守卫必然失败**。
   ⇒ 实现轮必须由 Human Decision 明确授权修改该守卫（改为"已实现域白名单"之类的显式规则），
     不得静默放宽或删除。
W2 `test_domains_define_no_schema_or_persistence`（文本级禁止 "create table" / "sqlalchemy"）
   与 L1/L2 结论一致 ⇒ 契约层保持纯 Python，无需修改该守卫。
W3 `test_core_never_imports_domains` / `test_core_imports_only_core` 不得被绕过：
   Company 契约若需要新的 core 能力（例如资源类型常量），必须由 core 侧定义，
   不得让 core 反向引用 `domains.company`。
W4 新增 P20 守卫（建议）：禁止 `services/company/**` 出现第二套授权/角色评估；
   禁止域/服务层出现 `SET ROLE`、动态 SQL、跨租户无谓词查询。
```

## 5. 依赖方向图（Company 落地后）

```text
apps/api/routes/company.py            （未授权 · 未来）
        │
services/company/use_cases.py         （编排：授权/校验/写入/审计 · 事务拥有者）
        ├── services/authorization    （唯一授权引擎）
        ├── services/audit/writer.py  （audit_logs 追加）
        ├── services/reads.py         （SafeReader · 只读基类）
        └── infrastructure/database/runtime.py（事务边界 · principal 断言）
                │
domains/company/contracts.py + ports.py     （纯契约：实体、不变量、端口、错误码）
                │
core/*（tenant/space/membership/permission/resource/audit 契约）

迁移层：migrations_alembic/versions/0019_p20_company.py（已完成 · 不可改）
```

## 6. 本轮结论

```text
D1 Core → Domain = 0 在 Company 落地路径上**可保持**（域只依赖 core，core 不反向引用域）。
D2 与既有守卫的冲突点只有一处（W1 placeholder 断言），且必须在实现轮显式处理。
D3 本文件不创建任何模块、不修改任何守卫；仅为设计约束登记。
```

**END OF P20 COMPANY DOMAIN DEPENDENCY MAP（纯契约置 domains/company · 编排置 services/company · 唯一守卫冲突点 = W1 placeholder 断言；2026-10-02）**
