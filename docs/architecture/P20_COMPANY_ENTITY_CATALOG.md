# P20 COMPANY ENTITY CATALOG（**FROZEN** · PDL 附录 AD）

```text
性质 = 提案级实体目录（NOT FROZEN · 未实施）
```

## T1 company_employees（提案）

| 字段 | 类型 | 约束 | 归属 | 可变 | 敏感 | 说明 |
|---|---|---|---|---|---|---|
| id | uuid | PK default uap_uuid_v7() | company | 不可变 | 否 | 员工业务实体 id |
| tenant_id | uuid | NOT NULL · FK→tenants(id) RESTRICT | company | 不可变 | 否 | 组织根（A2） |
| user_id | uuid | NULL · FK→users(id) RESTRICT | platform | 可变 | 否 | 平台身份引用（Employee ≠ User） |
| employee_no | text | NOT NULL · CHECK `^[A-Za-z0-9._-]{1,64}$` | company | 不可变 | 否 | 组织内工号（业务标识） |
| display_name | text | NOT NULL | company | 可变 | 否 | 展示名 |
| title | text | NULL | company | 可变 | 否 | 职务（自由文本 · 非授权来源） |
| status | text | NOT NULL · CHECK ∈ {active, suspended, terminated} | company | 可变 | 否 | 生命周期 |
| hired_at | timestamptz | NULL | company | 可变 | 否 | 入职时间 |
| terminated_at | timestamptz | NULL | company | 可变 | 否 | 离职时间（terminated 时必填） |
| created_at / updated_at | timestamptz | NOT NULL default now() | company/platform | 自动 | 否 | 时间戳 |

## T2 company_assignments（提案）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | uuid | PK default uap_uuid_v7() | 分配 id |
| tenant_id | uuid | NOT NULL · FK→tenants(id) RESTRICT | 冗余租户键（用于隔离与索引） |
| employee_id | uuid | NOT NULL · FK→company_employees(id) **CASCADE** | 员工删除随删分配 |
| space_id | uuid | NOT NULL · FK→spaces(id) RESTRICT | 部门（= space · A2） |
| assignment_role | text | NOT NULL · CHECK ∈ {member, lead} | 业务分配角色（**非授权来源**） |
| status | text | NOT NULL · CHECK ∈ {active, ended} | 分配状态 |
| started_at | timestamptz | NOT NULL default now() | 开始 |
| ended_at | timestamptz | NULL | 结束（ended 时必填） |
| created_at / updated_at | timestamptz | NOT NULL default now() | 时间戳 |

## 不新增的实体（明确排除）

```text
departments（= spaces · A2）· companies（= tenants · A2）·
company_users（= users · A3：员工复用平台身份）· company_roles / company_permissions（复用 canonical）·
company_memberships（= memberships · P17 管理空间成员资格）
```

**END OF P20 COMPANY ENTITY CATALOG（FROZEN · PDL 附录 AD；2026-10-01）**
