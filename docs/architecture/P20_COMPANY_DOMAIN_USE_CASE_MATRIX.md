# P20 COMPANY DOMAIN USE-CASE MATRIX（设计提案 · 未冻结 · 未实现）

```text
性质 = 用例 → 权限 → 授权目标 → 审计 → 拒绝条件 的单一映射表（配套 P20_COMPANY_DOMAIN_CONTRACT.md §4）
说明 = 表内所有 permission key 均取自 0019 已冻结的 11 行；未新增任何 action / permission / 角色
```

## 1. 命令（写）

| UC | 用例 | 权限键 | action | resource_type | 授权目标 | 需要的 grant scope | 审计 action | DB 影响 | 关键拒绝条件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | create_employee | `company_employee.create` | create | company_employee | 集合资源（D-2 备选：pre-resource） | TENANT（集合）或 PLATFORM（pre-resource） | `company_employee.create` | INSERT 1 行 | 无授权 · tenant 非 active · employee_no 冲突 · 格式非法 |
| C2 | update_employee_profile | `company_employee.update` | update | company_employee | 实例资源 | 覆盖该实例的 TENANT/SPACE grant 或 ACL | `company_employee.profile.update` | UPDATE display_name/title | 无授权 · 未找到 · 无字段变更 |
| C3 | link_employee_user | `company_employee.update` | update | company_employee | 实例资源 | 同上 | `company_employee.user.link` | UPDATE user_id | 无授权 · 目标 user 不存在/非 active（D-4） · (tenant,user) 冲突 |
| C4 | suspend_employee | `company_employee.update` | update | company_employee | 实例资源 | 同上 | `company_employee.suspend` | UPDATE status | 无授权 · 未找到 · 转换非法（非 active） |
| C5 | reactivate_employee | `company_employee.update` | update | company_employee | 实例资源 | 同上 | `company_employee.reactivate` | UPDATE status | 无授权 · 未找到 · 转换非法（非 suspended） |
| C6 | terminate_employee | `company_employee.update` | update | company_employee | 实例资源 | 同上 | `company_employee.terminate` | UPDATE status + terminated_at | 无授权 · 未找到 · 终态再终止 · tenant 非 active |
| C7 | create_assignment | `company_assignment.create` | create | company_assignment | 集合资源（D-2 备选：pre-resource） | TENANT（集合）或 PLATFORM（pre-resource） | `company_assignment.create` | INSERT 1 行 | 无授权 · 员工/空间不存在或跨租户 · 空间非 active（D-6） · 有效分配重复 · 员工非 active（D-3） |
| C8 | change_assignment_role | `company_assignment.update` | update | company_assignment | 实例资源 | 覆盖该实例的 grant 或 ACL | `company_assignment.role.update` | UPDATE assignment_role | 无授权 · 未找到 · 分配已 ended · 角色值非法 |
| C9 | end_assignment | `company_assignment.update` | update | company_assignment | 实例资源 | 同上 | `company_assignment.end` | UPDATE status + ended_at | 无授权 · 未找到 · 转换非法（已 ended） |

```text
未映射（保留）：company_employee.delete · company_assignment.delete（无物理删除，见 GAP-3）·
                company_employee.admin（语义未定义，见 GAP-4）
```

## 2. 查询（读）

| UC | 用例 | 权限键 | action | resource_type | 授权目标 | 审计 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Q1 | read_employee | `company_employee.read` | read | company_employee | 实例资源 | 默认不写（D-7） | 未授权与不存在返回同一拒绝码 |
| Q2 | list_employees | `company_employee.list` | list | company_employee | 集合资源 | 默认不写 | tenant 内过滤 + 分页（D-8） |
| Q3 | read_assignment | `company_assignment.read` | read | company_assignment | 实例资源 | 默认不写 | 需同一 tenant |
| Q4 | list_assignments | `company_assignment.list` | list | company_assignment | 集合资源 | 默认不写 | 过滤 employee_id / space_id / status |

## 3. 与平台权限行的对应关系（0019 已冻结）

```text
company_employee.read   → Q1        company_assignment.read   → Q3
company_employee.list   → Q2        company_assignment.list   → Q4
company_employee.create → C1        company_assignment.create → C7
company_employee.update → C2 C3 C4 C5 C6   company_assignment.update → C8 C9
company_employee.delete → （保留 · 未映射）
company_employee.admin  → （保留 · 未映射）
company_assignment.delete → （保留 · 未映射）

覆盖率：11 行中 8 行被本提案使用；3 行（2×delete + 1×admin）语义待裁定（D-3）。
```

## 4. 授权目标的判定规则（供实现轮使用）

```text
R1 目标对象已存在（有 id）→ 实例资源：resource = ResourceRef(type=<resource_type>, id=<对象 id>, tenant_id=<上下文 tenant>)
R2 目标对象不存在（创建）→ 二选一：
   (a) 集合资源：resource = ResourceRef(type=<resource_type>, id=<集合资源 id>, tenant_id=<上下文 tenant>)
   (b) pre-resource：resource = None + action.resource_type = <resource_type>（仅 PLATFORM scope 可用，P18-D06 先例）
R3 任何情况下都不得跳过授权直接读/写业务行（A7）。
R4 目标与上下文 tenant 不一致 ⇒ 引擎 DENY，不返回业务数据。
```

## 5. 未决项（阻断实现轮）

```text
* D-2 资源投影策略未定 ⇒ R1/R2 的具体形态未定（GAP-2）
* D-5 角色授予模型未定 ⇒ 上述授权目标当前无任何角色携带（role grants = 0，GAP-1）
* D-3 delete/admin 语义未定 ⇒ 3 条权限行无用例（GAP-3 / GAP-4）
* D-4 user 链接校验未定 ⇒ C3 前置条件未定（GAP-5）
* D-6 space 生命周期规则未定 ⇒ C7 前置条件与归档行为未定（GAP-7）
```

**END OF P20 COMPANY DOMAIN USE-CASE MATRIX（9 命令 + 4 查询 · 8/11 权限行被映射 · 3 行待裁定 · 无新增 action/permission；2026-10-02）**
