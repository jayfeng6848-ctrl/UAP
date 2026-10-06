# P20 COMPANY DOMAIN CONTRACT（设计提案 · 未冻结 · 未实现）

```text
性质     = DOMAIN CONTRACT PROPOSAL（设计交付物，不是授权、不是实现）
状态     = 未冻结；实现前需 Human Decision（见 P20_COMPANY_DOMAIN_DECISION_INPUT.md）
基线     = 0019_p20_company（ACCEPTED）+ PDL 附录 AC / AD / AE
依赖事实 = P20_COMPANY_DOMAIN_PREP.md §2 的 F1–F12（全部来自只读勘验）
```

## 1. 定位与职责

```text
Company 域 = "组织内的员工（Employee）与其业务组织分配（Assignment）"的业务语义层。

本域负责：
  * 员工/分配的业务不变量与生命周期转换（§3）
  * 用例编排：授权 → 校验 → 结构写入 → 审计 → 提交（§4 / §9）
  * 面向平台其他层的契约（实体、仓储端口、用例签名、错误分类）

本域不负责（不得实现）：
  * 授权算法（唯一引擎 = services.authorization.AuthorizationService）
  * 数据库结构真实性（唯一权威 = 0019 migration 的约束/触发器）
  * 租户/空间生命周期本身（归 P18 Control Plane）
  * 成员资格语义（归 P17 membership；assignment ≠ membership）
  * 传输层（API）、后台执行（Worker）、事件（P19 未激活）
```

## 2. 术语与不变量

```text
Employee   = Company 业务实体（Employee ≠ User）；user_id 可选，指向平台身份 users.id
Assignment = 员工 ↔ 部门（= Space）的业务组织分配；**不产生** membership、角色或 ACL
Department = Space（D-P20S-01；无 departments 表、无层级）
```

| # | 不变量 | 强制层 |
| --- | --- | --- |
| I1 | 员工只属于一个 tenant；跨租户读写 = 无允许路径 | DB FK + 触发器 + 应用 tenant 上下文 |
| I2 | `employee_no` 在同一 tenant 内唯一 | DB `uq_company_employees_no` |
| I3 | 同一 `(tenant_id, user_id)` 至多一个员工身份（user_id 非空时） | DB 部分唯一索引（D-P20S-07） |
| I4 | 员工生命周期 = `active` / `suspended` / `terminated`；`terminated ⇔ terminated_at NOT NULL` | DB CHECK + 域转换表 |
| I5 | 分配 `tenant_id` = 员工 tenant = 空间 tenant | DB 触发器（OPT-2） |
| I6 | 同一 `(employee_id, space_id)` 至多一条有效分配（`ended_at IS NULL`） | DB 部分唯一索引 |
| I7 | 分配生命周期 = `active` / `ended`；`ended ⇔ ended_at NOT NULL` | DB CHECK + 域转换表 |
| I8 | 任何用例都不得产生 DELETE；终止/结束 = 状态变更 | 运行时无 DELETE 权限 + 域契约 |
| I9 | 授权先于数据披露；未授权不得因"找不到"而泄露存在性 | 用例顺序（§4） |

## 3. 生命周期转换（域层校验；DB 为其最后防线）

```text
Employee：  active   → suspended | terminated
            suspended→ active    | terminated
            terminated → （终态；重新雇佣 = 新建员工行，不复活旧行）

Assignment：active   → ended
            ended    → （终态；再次分配 = 新建分配行）

非法转换 = EMPLOYEE_LIFECYCLE_CONFLICT / ASSIGNMENT_LIFECYCLE_CONFLICT（不落到 DB 层报错）
```

## 4. 用例契约

固定执行顺序（与 P18 控制面一致，一步不得前移）：

```text
1) 授权（canonical AuthorizationService · 仅 ALLOW 才继续）
2) 上下文门禁（tenant active；涉及 space 时 space active — §6）
3) 输入校验 + 实体不变量 / 生命周期校验
4) 结构写入（同一事务）
5) 审计（同一事务 · audit_logs append-only）
6) COMMIT（由 RuntimeDatabase.transaction 拥有）
```

### 4.1 命令

| UC | 用例 | 权限键 | 动作 | 授权目标 | 主要副作用 | 审计 action |
| --- | --- | --- | --- | --- | --- | --- |
| C1 | `create_employee` | `company_employee.create` | create | 集合资源（或 pre-resource，见 D-2） | INSERT company_employees | `company_employee.create` |
| C2 | `update_employee_profile` | `company_employee.update` | update | 实例资源 | UPDATE display_name / title | `company_employee.profile.update` |
| C3 | `link_employee_user` | `company_employee.update` | update | 实例资源 | UPDATE user_id | `company_employee.user.link` |
| C4 | `suspend_employee` | `company_employee.update` | update | 实例资源 | status active→suspended | `company_employee.suspend` |
| C5 | `reactivate_employee` | `company_employee.update` | update | 实例资源 | status suspended→active | `company_employee.reactivate` |
| C6 | `terminate_employee` | `company_employee.update` | update | 实例资源 | status→terminated + terminated_at | `company_employee.terminate` |
| C7 | `create_assignment` | `company_assignment.create` | create | 集合资源（或 pre-resource） | INSERT company_assignments | `company_assignment.create` |
| C8 | `change_assignment_role` | `company_assignment.update` | update | 实例资源 | UPDATE assignment_role | `company_assignment.role.update` |
| C9 | `end_assignment` | `company_assignment.update` | update | 实例资源 | status→ended + ended_at | `company_assignment.end` |

```text
保留（本提案不映射）：company_employee.delete / company_assignment.delete（无物理删除）·
                      company_employee.admin（语义未定义）—— 见 D-3 与 GAP-3 / GAP-4。
```

### 4.2 查询

| UC | 用例 | 权限键 | 动作 | 授权目标 | 备注 |
| --- | --- | --- | --- | --- | --- |
| Q1 | `read_employee` | `company_employee.read` | read | 实例资源 | 未授权/不存在返回同一拒绝码（不泄露存在性） |
| Q2 | `list_employees` | `company_employee.list` | list | 集合资源 | tenant 内过滤（status / employee_no 前缀）；分页见 D-8 |
| Q3 | `read_assignment` | `company_assignment.read` | read | 实例资源 | — |
| Q4 | `list_assignments` | `company_assignment.list` | list | 集合资源 | 过滤 employee_id / space_id / status |

### 4.3 幂等与并发

```text
create_employee   ：自然键 (tenant_id, employee_no)。payload 完全一致的重放 → 返回既有对象
                    （replayed=true）；不一致 → EMPLOYEE_NO_CONFLICT。
create_assignment ：有效键 (employee_id, space_id, ended_at IS NULL)。完全一致重放 → 既有对象；
                    其余冲突 → ASSIGNMENT_CONFLICT。
状态转换          ：条件更新（UPDATE … WHERE id=… AND status=:expect）；rowcount=0 →
                    *_LIFECYCLE_CONFLICT（并发行变更不静默覆盖）。
```

## 5. 授权契约（唯一引擎）

```text
A1 每个用例调用一次 canonical 决策：AuthorizationService.authorize(AuthorizationRequest)。
   Subject = 认证后的平台用户（identity_id = users.id · subject_type = "USER" · actor_id 同值）。
A2 Action = 该用例的 action 名（§4）；resource_type 必须等于权限行 resource_type
   （company_employee / company_assignment），否则 RBAC 永不匹配（F2）。
A3 资源目标三选一（D-2 裁定）：集合资源 / 实例资源 / pre-resource（resource=None，仅 PLATFORM scope 可用）。
A4 tenant_id / space_id 必须来自已验证的运行时上下文；与资源不一致 ⇒ 引擎 DENY（cross-tenant）；
   不得用请求体字段放宽判定。
A5 引擎返回非 ALLOW（含 REQUIRES_APPROVAL、异常、不可用）⇒ 一律 AUTHORIZATION_DENIED，fail-closed。
A6 本域不得新增角色、权限、ACL subject type，也不得自建评估逻辑（F12）。
A7 先授权后披露：拒绝路径不返回业务行；错误不得泄露存在性。
```

## 6. 上下文与生命周期门禁

```text
G1 所有用例要求 tenant.status = active（复用 P18-D14 语义）；否则 TENANT_NOT_ACTIVE。
G2 涉及 space 的用例（C7–C9、Q3–Q4 带 space 过滤）要求 space 属于同一 tenant 且 status = active；
   否则 SPACE_NOT_FOUND / SPACE_NOT_ACTIVE。
G3 不得以 owner / creator / platform_admin 兜底通过门禁。
G4 归档/删除空间的既有分配如何处理 = D-6（默认：拒绝新建；既有分配不自动改写，保留历史事实）。
```

## 7. 资源投影契约（授权前提 · 待裁定）

```text
P1 实例资源方案：为每个 company_employee / company_assignment 建立 resources 行，
   resource_type = 权限行 resource_type，natural_key = 业务自然键，
   允许 resources.id = 业务对象 id（P16 agent 先例 F10）。
P2 集合资源方案：每 tenant 一行（自然键如 employees / assignments），与 P17 member 集合先例一致；
   该方案下实例级 ACL 授权不可用。
P3 投影与业务写入必须在同一事务内完成（P17-AUTH-Q1：缺投影 = DENY，不得自愈补建）。
P4 现有 uap_runtime 已具备 resources INSERT/UPDATE（F7）⇒ 本契约不要求任何新 GRANT。
P5 投影失败必须整体回滚（不允许"有员工、无投影"的中间态）。
```

## 8. 审计契约

```text
U1 每个成功变更写恰好一行审计（与业务写入同一事务）；拒绝/失败是否落审计 = D-7。
U2 字段映射（audit_logs 实测列 F8）：
   action         = §4 的审计 action 名
   resource_type  = company_employee / company_assignment
   resource_id    = 对象 id（创建前为空/NULL）
   tenant_id      = 对象 tenant；space_id = 分配相关用例的空间（否则 NULL）
   actor_type/actor_id = 认证主体；result = success|denied|error；risk_level = D-7 约定
   correlation_id = 调用方传入或生成；metadata = 白名单键（禁止凭据/密钥/整行数据）
U3 events 与 audit_logs 严格分离：本域不写 events、不建 producer、不建 handler。
U4 审计不可用 ⇒ 整个事务失败（不允许"改了但没有审计"）。
```

## 9. 事务与持久化契约

```text
T1 一个用例 = 一个事务（RuntimeDatabase.transaction）；仓储永不 commit（F6）。
T2 应用层做语义校验；数据库约束是最后防线，违反时映射为稳定错误码，
   绝不向上泄露 SQL、约束名或堆栈（沿用 P18 错误分类风格）。
T3 读取走 SafeReader（Wave-1 Repository._fetch_one/_fetch_all 为已知 D-01 缺陷，不得沿用）。
T4 所有查询必须携带 tenant 谓词；不得存在仅按 id 的跨租户查找。
T5 不使用 SET ROLE / 动态 SQL / 字符串拼接；参数一律绑定。
```

## 10. 错误分类（封闭集 · 提案）

```text
INVALID_INPUT · EMPLOYEE_NOT_FOUND · EMPLOYEE_NO_CONFLICT · EMPLOYEE_LIFECYCLE_CONFLICT ·
EMPLOYEE_USER_CONFLICT · ASSIGNMENT_NOT_FOUND · ASSIGNMENT_CONFLICT · ASSIGNMENT_LIFECYCLE_CONFLICT ·
TENANT_NOT_ACTIVE · SPACE_NOT_FOUND · SPACE_NOT_ACTIVE · AUTHORIZATION_DENIED ·
RESOURCE_NOT_PROVISIONED · AUDIT_UNAVAILABLE · PAGINATION_INVALID

约定：错误对象只携带 code + 安全消息；不携带 SQL / 约束名 / 堆栈 / 跨租户存在性线索。
```

## 11. 接口草案（签名示意 · 不实现）

```python
# 落点见 D-8（域契约 vs 服务编排）
@dataclass(frozen=True)
class Employee: ...      # id, tenant_id, user_id|None, employee_no, display_name,
                         # title|None, status, hired_at|None, terminated_at|None,
                         # created_at, updated_at
@dataclass(frozen=True)
class Assignment: ...    # id, tenant_id, employee_id, space_id, assignment_role,
                         # status, started_at, ended_at|None, created_at, updated_at

class EmployeeRepository(Protocol):
    def insert(self, session, *, tenant_id, employee_no, display_name, title, hired_at) -> str: ...
    def get(self, session, *, tenant_id, employee_id) -> Row | None: ...
    def list(self, session, *, tenant_id, status, prefix, limit, cursor) -> list[Row]: ...
    def set_status(self, session, *, tenant_id, employee_id, expect, status, terminated_at) -> int: ...
    def update_profile(self, session, *, tenant_id, employee_id, display_name, title) -> int: ...
    def link_user(self, session, *, tenant_id, employee_id, user_id) -> int: ...

def create_employee(db, *, actor_id, tenant_id, employee_no, display_name, title=None,
                    hired_at=None, correlation_id=None) -> Employee: ...
def terminate_employee(db, *, actor_id, tenant_id, employee_id, correlation_id=None) -> Employee: ...
def create_assignment(db, *, actor_id, tenant_id, employee_id, space_id,
                      assignment_role="member", correlation_id=None) -> Assignment: ...
# …其余同 §4
```

## 12. 与冻结决策的映射

| 冻结项 | 契约落点 |
| --- | --- |
| D-P20S-01 Department = Space | §2 术语；无 departments 表/层级 |
| D-P20S-02 两张业务表 | §3 模型仅 Employee / Assignment |
| D-P20S-03 Employee ≠ User | §2；F4（员工不是授权主体） |
| D-P20S-04 员工生命周期 | §3 转换表 + I4 |
| D-P20S-06 结构隔离 + 应用授权 | §5 + §7（两条腿，不复刻引擎） |
| D-P20S-07 user/tenant 一致性 | I3（DB 部分唯一） |
| D-P20S-08 canonical 12 actions | §4 全部动作取自既有 action；不新增 |
| D-P20S-09 无物理 DELETE | I8；delete 权限键待裁定（D-3） |
| D-P20S-11 审计 | §8（复用 audit_logs，无新表） |
| D-P20S-13 最小运行时权限 | §7 P4（无新 GRANT） |
| D-P20S-14 domains/company/ · Core→Domain=0 | §9 + DEPENDENCY_MAP |
| D-P20S-15 无生产事件 | §8 U3 |
| 附录 AE OPT-2 触发器 | I5（DB 强制；应用层不重复实现为第二校验引擎） |

**END OF P20 COMPANY DOMAIN CONTRACT（设计提案 · 未冻结 · 未实现 · 不变量 I1–I9 · 用例 C1–C9 / Q1–Q4 · 契约 A1–A7 / P1–P5 / U1–U4 / T1–T5 / G1–G4；2026-10-02）**
