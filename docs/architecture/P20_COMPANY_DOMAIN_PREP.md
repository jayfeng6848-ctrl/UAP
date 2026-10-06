# P20 COMPANY DOMAIN PREP — 只读分析 + Domain 契约设计

```text
阶段     = P20 COMPANY DOMAIN PREP（READ-ONLY ANALYSIS + CONTRACT DESIGN）
基线     = UAP-V0.1.17-P18-CONTROL-PLANE（08a0485b）+ 0019_p20_company（ACCEPTED · 未提交）
冻结权威 = PDL 附录 AC（首业务模块）· AD（schema）· AE（OPT-2）
本轮性质 = 只读勘验 + 契约设计文档；**不实现任何代码、不建表、不改 migration、不建 API/Worker/Event**
产物     = 本文件 + 6 份配套文档（§4 索引）
```

## 1. 只读勘验基线

```text
git HEAD          = 08a0485 release: UAP v0.1.17 P18 control plane · staged = 0
工作区            = 29 modified（全部历史脏）+ 116 untracked（含 4 份 P20 证据/迁移产物）
0019_p20_company  = 已验收（P20 MIGRATION ACCEPTANCE REPORT · 10/10 PASS）
company 代码引用    = 0（全仓 rg：`company_employee|company_assignment` 仅出现在 0019 迁移文件内）
P20 测试           = 0（tests/ 下无任何 P20 用例）
domains/company/  = placeholder（manifest.py: status=placeholder · tables=[] · entrypoints=[]）
共享测试库         = uap_b1_test = 0017_p13_seed（未迁移；permissions 12 · company 表 0）
正式库 uap         = 0 public 表（未触碰）
```

## 2. 契约必须适配的既有平台机制（实测事实）

```text
F1 授权是**资源行驱动**的：`AuthorizationService` → `ResourceResolver.resolve()` 读 `resources.id`；
   行不存在 = DENY（F-P17-I-02 / P17-AUTH-Q1），绝不自动补建。
F2 RBAC 匹配三元组：存储 action 规范化后等于请求 action **且** `permissions.resource_type`
   等于资源行的 `resource_type`（不一致 = 不匹配）。公司 11 条权限行的 resource_type 已冻结为
   `company_employee` / `company_assignment`，因此**资源类型名已被冻结语义约束**。
F3 作用域：`scope_covers()` 只认 PLATFORM / TENANT / SPACE 三种**存储** grant；
   SPACE grant 要求 `resource.space_id` 精确相等；TENANT grant 只要求 tenant 相等。
F4 SUBJECT：USER 主体必须携带 `users.id`（`SubjectResolver` 以 users.id 解析）；AGENT 是独立主体。
   员工（Employee）是**被治理对象**，不是授权主体 —— Employee ≠ User 在授权层同样成立。
F5 ACTOR 的角色来源：`role_ids_for_user` 读 `platform_memberships` / `tenant_memberships` / `memberships`。
F6 运行时 DB 边界：`RuntimeDatabase.transaction()` 拥有事务，仓储不 commit；principal 断言要求
   `uap_runtime`（fail-closed）。
F7 现有 `uap_runtime` 权限面已覆盖 Company 契约所需的全部平台表：
   `resources` = INSERT/SELECT/UPDATE · `audit_logs` = INSERT/SELECT · `spaces`/`tenants` = SELECT ·
   `permissions`/`role_permissions` = SELECT · company 两表 = INSERT/SELECT/UPDATE（0019 授权）。
   ⇒ **本轮契约不需要任何新的 GRANT**（这是 E 选项成立的前提）。
F8 审计先例（P18）：在同一事务内 `INSERT INTO audit_logs`，action 形如 `tenant.provision` /
   `space.metadata.update`，字段 id/occurred_at/tenant_id/space_id/actor_type/actor_id/action/
   resource_type/resource_id/result/risk_level/correlation_id/metadata/created_at；
   `services/audit/writer.py` 提供同语义写入器（含 metadata 白名单）。
F9 生命周期门禁先例（P18-D14）：`require_active_agent_scope()` 要求 tenant（及其绑定 space）为 active；
   Company 用例需要同型的 active-scope 门禁（不得以 owner/platform 兜底）。
F10 资源投影先例：P17 用**集合资源**（`member`·每 tenant 一行 · natural_key 保留键），
   P16 用**实例资源**（resource id = 对象 id）。两者都在 `uq_resources_natural
   (tenant_id, resource_type, natural_key) WHERE natural_key IS NOT NULL AND deleted_at IS NULL` 约束内。
F11 SELF / RESOURCE 是**上下文谓词**，当前只在 `core.permission.scope` 与测试中存在；
   服务层 `Grant` 无谓词字段、`PolicyRule` 也无谓词字段 ⇒ **自助（self-service）授权当前不可表达**。
F12 无第二授权引擎：任何域代码必须调用既有 `AuthorizationService`，不得自建角色/许可评估。
```

## 3. 本阶段设计结论摘要（提案，未冻结）

```text
S1 职责边界：Company 域负责"员工与业务组织分配"的业务语义、不变量与用例编排；
   授权、审计、事务、持久化边界一律复用平台既有机制（F1–F12），不得复制。
S2 用例集合：员工 6 命令（create / update_profile / link_user / suspend / reactivate / terminate）
   + 2 查询（list / read）；分配 3 命令（create / change_role / end）+ 2 查询（list / read）。
   `delete`（两实体）与 `admin` 权限键的语义**未定**，列入决策输入（不得静默映射）。
S3 授权目标：每个用例明确声明授权目标（集合资源 / 实例资源 / pre-resource），
   并保持"先授权、后读数据、再写、最后审计"的顺序。
S4 结构隔离（DB）与应用 canonical 授权并存（D-P20S-06 两条腿），域层不重复实现租户隔离校验，
   但必须传对 tenant/space 上下文（跨租户 = 无允许路径）。
S5 无物理删除：终止 = 状态变更；`employee_id → company_employees` 的 CASCADE 仅在被父行硬删时可达，
   而运行时无 DELETE 权限 ⇒ 应用路径不可达（已在 0019 验收中记录）。
S6 事件：不产生、不消费（A7 / D-P20S-15 / P19-D01 OPTION D 不变）。
```

## 4. 交付物索引

```text
docs/architecture/P20_COMPANY_DOMAIN_PREP.md            ← 本文件（勘验 + 结论摘要）
docs/architecture/P20_COMPANY_DOMAIN_CONTRACT.md        ← Domain 契约设计（核心交付物）
docs/architecture/P20_COMPANY_DOMAIN_USE_CASE_MATRIX.md ← 用例 × 权限 × 审计 × 拒绝条件矩阵
docs/architecture/P20_COMPANY_DOMAIN_DEPENDENCY_MAP.md  ← 依赖方向与允许/禁止导入
docs/architecture/P20_COMPANY_DOMAIN_GAP_RECORD.md      ← 缺口登记（含阻断项）
docs/architecture/P20_COMPANY_DOMAIN_DECISION_INPUT.md  ← Human Decision 输入（选项与后果）
docs/architecture/P20_COMPANY_DOMAIN_TEST_MATRIX.md     ← 未来实现轮的验收测试矩阵（提案）
```

## 5. 本轮未做（边界声明）

```text
未创建 / 未修改任何 Python 代码（core / services / domains / infrastructure / apps）·
未新增表 / 列 / 约束 / 索引 / 触发器 / migration · 未 GRANT / REVOKE ·
未新增 permission / role / role grant / ACL subject type / canonical action ·
未新增 API 路由 / Worker / producer / handler · 未激活事件 ·
正式库与共享测试库未触碰 · 未 commit / tag / push
```

**END OF P20 COMPANY DOMAIN PREP（只读勘验 + 契约设计 · 12 项平台机制事实 F1–F12 · 6 项设计结论 S1–S6 · 未实现任何代码；2026-10-02）**
