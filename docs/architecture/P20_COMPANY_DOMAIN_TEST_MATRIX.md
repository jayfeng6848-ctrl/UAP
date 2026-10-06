# P20 COMPANY DOMAIN TEST MATRIX（实现轮验收测试矩阵 · 提案 · 当前未执行）

```text
性质 = 未来实现轮的测试设计（不是本轮执行结果）；本阶段未新增任何测试文件
输入 = P20_COMPANY_DOMAIN_CONTRACT.md（用例 C1–C9 / Q1–Q4）与 DECISION_INPUT（D-1…D-11）
要求 = 全部测试走显式 allowlist；禁止目录级全量 sweep；tests/unit/test_generate_build_info.py 保持 0 执行
```

## 1. 领域单元测试（无数据库）

| # | 断言 | 依据 |
| --- | --- | --- |
| U1 | 员工生命周期仅允许 active→suspended/terminated、suspended→active/terminated；terminated 为终态 | 契约 §3 · I4 |
| U2 | 分配生命周期仅允许 active→ended；ended 为终态 | 契约 §3 · I7 |
| U3 | 非法转换抛 EMPLOYEE_LIFECYCLE_CONFLICT / ASSIGNMENT_LIFECYCLE_CONFLICT（不落到 DB） | 契约 §3 |
| U4 | 输入校验：employee_no 格式、display_name 非空、assignment_role ∈ {member,lead} | 契约 §10 |
| U5 | 错误对象仅含 code + 安全消息（不含 SQL / 约束名 / 堆栈） | 契约 §9 T2 |
| U6 | 实体/dataclass 不依赖 sqlalchemy、不依赖 services/infrastructure | DEPENDENCY_MAP L1 |

## 2. 授权集成测试（一次性隔离库）

| # | 场景 | 期望 |
| --- | --- | --- |
| A1 | 无任何 Company 权限 → 任意用例 | AUTHORIZATION_DENIED（默认拒绝） |
| A2 | 持有对应 permission key（按 D-1 裁定的主体）→ 各用例 | ALLOW 并成功 |
| A3 | 持有 `read` 但请求 `update` | DENIED（action 不匹配） |
| A4 | 持有其它 resource_type 的同名 action | DENIED（resource_type 不匹配，F2） |
| A5 | SPACE-scope grant 访问无 space 绑定的员工资源 | DENIED（scope 不覆盖） |
| A6 | 跨租户资源 + 本租户上下文 | DENIED（cross-tenant，无允许路径） |
| A7 | 资源投影缺失（若 D-2 = A/B） | DENIED（不得自愈补建，P3） |
| A8 | 授权服务异常/不可用 | DENIED（fail-closed，A5） |
| A9 | 拒绝路径不返回业务行 | 断言响应/异常不含业务数据（A7） |

## 3. 上下文与生命周期门禁

| # | 场景 | 期望 |
| --- | --- | --- |
| L1 | tenant.status ≠ active → 任意用例 | TENANT_NOT_ACTIVE |
| L2 | space 不存在 / 非同租户 | SPACE_NOT_FOUND |
| L3 | 按 D-6 裁定：向非 active 空间新建分配 | SPACE_NOT_ACTIVE（拒绝） |
| L4 | 既有分配 + 空间归档（若 D-6 = A） | 既有分配不被改写（快照对比） |
| L5 | owner / platform_admin 兜底尝试 | 不产生放行（G3） |

## 4. 审计与事务

| # | 场景 | 期望 |
| --- | --- | --- |
| T1 | 每次成功变更 | audit_logs 恰好 +1 行，字段映射符合契约 §8 |
| T2 | 业务写入失败 | 审计与业务行**都不存在**（同一事务） |
| T3 | 审计写入失败（可用触发器/权限模拟） | 业务写入回滚（U4） |
| T4 | metadata 白名单 | 不出现凭据/密钥/整行数据 |
| T5 | 拒绝/失败路径 | 按 D-8 裁定（默认不写审计行） |
| T6 | 条件更新竞争（并发状态转换） | rowcount=0 → *_LIFECYCLE_CONFLICT，不静默覆盖 |

## 5. 隔离与安全

| # | 场景 | 期望 |
| --- | --- | --- |
| S1 | 跨租户按 id 直查员工/分配 | 查不到（tenant 谓词强制，T4） |
| S2 | 过滤参数注入尝试（employee_no 前缀 / cursor） | 参数绑定生效，无 SQL 注入面 |
| S3 | 分页越界（limit=0 / 1000 / 非法游标） | PAGINATION_INVALID（不返回部分结果） |
| S4 | 数据库约束违反（工号重复、双 active 分配、跨租户分配） | 映射为稳定错误码，不泄露约束名 |
| S5 | 运行时角色 DELETE / ALTER / TRUNCATE 尝试 | DENIED（0019 授权面未变） |
| S6 | 员工 user_id 绑定不产生任何授权 | 断言绑定后该用户仍无权访问（F4 / D-5） |

## 6. 边界与架构守卫（回归）

| # | 断言 | 依据 |
| --- | --- | --- |
| B1 | `domains/company/**` 不含 sqlalchemy / "create table" / services / infrastructure 导入 | 既有守卫 + DEPENDENCY_MAP L1 |
| B2 | Core → Domain = 0 保持 | 既有守卫 |
| B3 | 无第二授权引擎（不得自建角色/许可评估） | A6 / 建议新增守卫 W4 |
| B4 | 无第二权限词表（不新增 action / ACL subject type） | D-P20S-08 |
| B5 | 事件不变式：Allowlist EMPTY · Handlers 0 · Producers 0 · events 0 | A7 / D-P20S-15 |
| B6 | 0019 migration 未被修改（哈希比对） | 验收基线 |
| B7 | D-10 裁定后：placeholder 守卫按授权更新，且其它域仍为 placeholder | DEPENDENCY_MAP W1 |

## 7. 执行与证据要求（实现轮）

```text
E1 测试必须以显式 allowlist 运行（禁止 pytest / pytest tests 全量 sweep）
E2 tests/unit/test_generate_build_info.py 执行数 = 0（冻结禁令）
E3 数据库验证在一次性隔离库完成；共享测试库按 D-11 裁定处理；正式库 uap 只读
E4 证据需含：用例 → 权限 → 审计 的实测映射、拒绝矩阵、跨租户矩阵、错误码映射、
   审计行快照（before/after 计数）、隔离库 before/after 状态、守卫执行结果
E5 未授权项（API/Worker/Event）不得因"顺势"出现在实现轮之外
```

## 8. 本阶段（PREP）执行状态

```text
本轮 = 未新增任何测试文件 · 未执行任何测试（只读阶段）
既有基线（上一轮验收实测）：tests/architecture = 63 passed · 0019 隔离库矩阵 T1–T20 全符合预期
```

**END OF P20 COMPANY DOMAIN TEST MATRIX（提案 · 6 类共 39 条测试设计 U1–U6 / A1–A9 / L1–L5 / T1–T6 / S1–S6 / B1–B7 · 本轮未执行；2026-10-02）**
