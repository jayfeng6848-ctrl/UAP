# P20 COMPANY DOMAIN IMPLEMENTATION CONTRACT（DRAFT · 未授权实现 · 未冻结）

```text
性质     = IMPLEMENTATION CONTRACT DRAFT（供 Implementation Authorization 使用的设计契约）
状态     = 未冻结；实现仍为 NOT AUTHORIZED（本轮不创建任何代码/测试/迁移/数据）
基线     = UAP-V0.1.17-P18-CONTROL-PLANE（08a0485b）+ PDL 附录 AC/AD/AE/AF + 0019_p20_company（ACCEPTED）
约束来源 = 附录 AF（D-P20D-01…11）· Phase 0 只读基线（本轮实测）
```

## 0. 本轮范围与前置

```text
本轮生成  = 本契约 + Phase 2 缺口报告 + 授权准备报告（全部为文档）
本轮禁止  = 修改 Python 代码 · 创建 domain/service/repository · 修改 manifest 或架构守卫 ·
            API · Worker · Event · 修改 migration 或数据库 · GRANT/REVOKE · seed role permission ·
            commit / tag / push
实现前置  = ① 权限授予方式裁定（GAP-G1）② 集合资源投影归属裁定（GAP-G2）
            —— 二者未定则实现轮无法产出可运行（可授权）的域
```

## 1. Domain Boundary（`domains/company/`）

```text
允许（纯契约，无 I/O）：
  * entity contract（Employee / Assignment 的不可变数据形状）
  * value object（EmployeeNo / Lifecycle / AssignmentRole 等受限取值）
  * domain invariant（§2 的转换表与不变量，纯函数）
  * interface definition（ports：仓储/投影 Protocol）
  * error taxonomy（域错误码常量）

禁止：
  * ORM / SQLAlchemy / psycopg / 任何 SQL 文本
  * infrastructure / services / apps 导入
  * 授权实现（不得出现角色、许可、ACL 求值逻辑 → 唯一引擎在 services.authorization）
  * schema / DDL / "create table" 文本
  * 事件发布或 producer

建议模块布局（实现轮创建；本轮不创建）：
  domains/company/__init__.py         （已存在）
  domains/company/entities.py         Employee · Assignment（frozen dataclass）
  domains/company/values.py           EMPLOYEE_STATUS · ASSIGNMENT_STATUS · ASSIGNMENT_ROLES · 转换表
  domains/company/ports.py            EmployeeRepository / AssignmentRepository / ResourceProjectionPort
  domains/company/errors.py           域错误码
  domains/company/manifest.py         **本轮与实现轮均不得修改**（需 GAP-G3 授权）

硬约束依据（既有守卫 · 本轮实测 14 passed）：
  G-4：domains 不得 import services / infrastructure
  domains 文本不得包含 "create table" / "sqlalchemy"
  守卫断言所有域 manifest 为 placeholder（status=placeholder · tables=[]）→ 变更需 GAP-G3 授权
导入白名单：仅标准库 + core.*
```

## 2. Service Boundary（`services/company/`）

```text
负责：
  * use case orchestration（授权 → 门禁 → 校验 → 写入 → 审计 → 提交）
  * authorization invocation（调用唯一引擎 AuthorizationService）
  * transaction boundary（RuntimeDatabase.transaction 拥有提交/回滚）
  * audit coordination（同事务写 audit_logs）
  * resource projection coordination（集合资源的 ensure/读取）

禁止：
  * event publishing（不写 events、不建 producer/handler）
  * hidden permission logic（不得自建角色/许可/ACL 判定；不得绕过引擎）
  * DDL / migration / GRANT（结构变更只属于迁移层）
  * 直接对外暴露传输语义（API 属 apps 层，本轮与实现轮均不创建）

建议模块布局（实现轮创建；本轮不创建）：
  services/company/__init__.py
  services/company/errors.py          CompanyError + ErrorCode（§7）
  services/company/repository.py      EmployeeRepository / AssignmentRepository 的 SQLAlchemy 实现
  services/company/projection.py      ResourceProjectionPort 的实现（集合资源 ensure/读取）
  services/company/use_cases.py       10 个用例（§4）

分层理由：G-4 禁止域层 import services/infrastructure ⇒ 任何触库/触授权引擎的代码只能在
services 层；与 P16 `services/agent/`、P18 `services/use_cases/control_plane.py` 同型。
```

## 3. Repository Contract（仅接口 · 不实现）

```text
共同约束（全部方法）：
  * 第一个参数为 session（由服务层事务拥有）；仓储**不 commit**
  * 每个查询必须携带 tenant 谓词（禁止仅按 id 的跨租户查找）
  * 返回映射/行对象或 None；不返回 ORM 实体给域层
  * 违反唯一/CHECK/FK 约束时抛出底层异常，由服务层映射为稳定错误码（§7）
```

```python
# domains/company/ports.py（契约示意）
class EmployeeRepository(Protocol):
    def insert(self, session, *, tenant_id: str, employee_no: str, display_name: str,
               title: str | None, hired_at: datetime | None) -> str: ...
    def get(self, session, *, tenant_id: str, employee_id: str) -> Mapping | None: ...
    def find_by_no(self, session, *, tenant_id: str, employee_no: str) -> Mapping | None: ...
    def update_profile(self, session, *, tenant_id: str, employee_id: str,
                       display_name: str | None, title: str | None) -> int: ...   # rowcount
    def bind_user(self, session, *, tenant_id: str, employee_id: str,
                  user_id: str | None) -> int: ...                              # 支持绑定与解绑（D-5）
    def set_status(self, session, *, tenant_id: str, employee_id: str, expect: str,
                   status: str, terminated_at: datetime | None) -> int: ...      # 条件更新

class AssignmentRepository(Protocol):
    def insert(self, session, *, tenant_id: str, employee_id: str, space_id: str,
               assignment_role: str) -> str: ...
    def get(self, session, *, tenant_id: str, assignment_id: str) -> Mapping | None: ...
    def find_active(self, session, *, tenant_id: str, employee_id: str,
                    space_id: str) -> Mapping | None: ...
    def update_role(self, session, *, tenant_id: str, assignment_id: str,
                    assignment_role: str) -> int: ...
    def end(self, session, *, tenant_id: str, assignment_id: str,
            expect: str, ended_at: datetime) -> int: ...                         # 条件更新

class ResourceProjectionPort(Protocol):
    def collection(self, session, *, tenant_id: str, resource_type: str) -> str | None: ...
    def ensure_collection(self, session, *, tenant_id: str, resource_type: str) -> str: ...
    # ensure_collection 的**调用时机与所有者** = GAP-G2（未定；禁止在本轮或实现轮自行选定）
```

```text
禁止：在 domains/company/** 内出现 sqlalchemy / psycopg / SQL 文本；
     在仓储层实现授权、审计或投影的隐式补建（投影见 §5 与 GAP-G2）。
```

## 4. Use Case Matrix（10 个用例 · 实现轮范围）

```text
通用执行顺序（每用例一致，不得前移/跳过）：
  1) 授权（唯一引擎 · 非 ALLOW 即拒）
  2) 上下文门禁（tenant active；涉及 space 时 space active）
  3) 输入校验 + 域不变量/生命周期校验
  4) 结构写入（同一事务）
  5) 审计（同一事务 · append-only）
  6) COMMIT（RuntimeDatabase.transaction）
```

| # | 用例 | 权限键 | 动作 | 资源目标（D-P20D-02） | 授权点 | 审计 action | 事务 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | create_employee | `company_employee.create` | create | tenant 集合资源 `company_employee` | 步骤 1（写前） | `company_employee.create` | 单事务（含投影 ensure，见 G2） |
| E2 | read_employee | `company_employee.read` | read | 集合资源（V1 无实例资源） | 步骤 1（读前） | 无（默认不写） | 只读事务 |
| E3 | update_employee | `company_employee.update` | update | 集合资源 | 步骤 1 | `company_employee.profile.update` | 单事务 |
| E4 | suspend_employee | `company_employee.update` | update | 集合资源 | 步骤 1 | `company_employee.suspend` | 单事务 |
| E5 | terminate_employee | `company_employee.update` | update | 集合资源 | 步骤 1 | `company_employee.terminate` | 单事务 |
| E6 | bind_employee_user | `company_employee.update` | update | 集合资源 | 步骤 1 | `company_employee.user.bind` | 单事务 |
| A1 | create_assignment | `company_assignment.create` | create | tenant 集合资源 `company_assignment` | 步骤 1（写前） | `company_assignment.create` | 单事务（含投影 ensure，见 G2） |
| A2 | read_assignment | `company_assignment.read` | read | 集合资源 | 步骤 1 | 无 | 只读事务 |
| A3 | update_assignment | `company_assignment.update` | update | 集合资源 | 步骤 1 | `company_assignment.role.update` | 单事务 |
| A4 | end_assignment | `company_assignment.update` | update | 集合资源 | 步骤 1 | `company_assignment.end` | 单事务 |

```text
每用例的拒绝条件（统一）：
  无授权 / 引擎非 ALLOW / 引擎异常 ⇒ AUTHORIZATION_DENIED（fail-closed）
  tenant 非 active ⇒ TENANT_NOT_ACTIVE；space 缺失或非 active ⇒ SPACE_NOT_FOUND / SPACE_NOT_ACTIVE
  跨租户目标 ⇒ DENY（引擎 cross-tenant 判定，不返回业务数据）
  状态转换非法 ⇒ *_LIFECYCLE_CONFLICT（域层判定，不落到 DB）

未纳入本轮矩阵的权限键（V1 不使用 · 见 GAP-G8）：
  company_employee.list · company_assignment.list（本轮矩阵未含 list 用例）
  company_employee.delete · company_assignment.delete（D-P20D-03 RESERVED）
  company_employee.admin（D-P20D-04 RESERVED）
  ⇒ 11 条权限行中 6 条被使用、5 条不使用（需 Human 确认该范围，见 GAP-G8）
```

## 5. Resource Projection Contract

```text
目标：让 Company 对象进入既有 Authorization Engine（引擎按 resources 行解析资源）。

resource_type（已冻结 · 来自 0019 权限行）
  company_employee · company_assignment

natural_key（本契约确定 · AF 已将取值授权给实现契约）
  company_employee  → 保留键 `employees`
  company_assignment→ 保留键 `assignments`
  依据：`uq_resources_natural (tenant_id, resource_type, natural_key) WHERE natural_key IS NOT NULL
        AND deleted_at IS NULL`；两种类型各自命名空间，故保留键不冲突

tenant scope
  resources.tenant_id = Company 对象所属 tenant（必填）
  resources.space_id  = NULL（集合资源为 tenant 级）
  resources.classification = INTERNAL（默认）· status = active · deleted_at = NULL

instance scope
  V1 = **无实例资源**（D-P20D-02 明确排除）；因此 ACL（resource_permissions）在 V1 不参与 Company 判定

授权目标构造（实现轮）
  ResourceRef(type="company_employee"|"company_assignment", id=<集合资源 id>, tenant_id=<上下文 tenant>)
  tenant_id/space_id 一律取自已验证上下文；不得使用请求体字段放宽判定

投影缺失语义
  缺失 = DENY（禁止运行时自愈补建，沿用 P17-AUTH-Q1）

禁止（本轮）
  不创建任何 resources 行、不创建任何 company 业务行、不执行任何 DML

未定（GAP-G2 · 阻断）
  ensure_collection 的调用者与时机：① 业务首写同事务自建 ② 控制面 provisioning 扩展
  ③ 运维 backfill + 业务路径只读。三种方案对"缺失即 DENY"与"同事务"约束的满足方式不同，
  必须由 Human 裁定。
```

## 6. Audit Contract

```text
写入范围：**仅上表标注审计 action 的 6 个变更用例**（E1/E3/E4/E5/E6 + A1/A3/A4；共 8 条动作，
          其中 E1 覆盖 create，A1 覆盖 create）——只读用例（E2/A2）不写审计。

写入时机：与业务写入**同一事务**；任一步失败 ⇒ 业务与审计一起回滚。

字段映射（audit_logs 实测列）：
  id            = new_event_id()（UUIDv7）
  occurred_at   = now()
  actor_type    = 'user'；actor_id = 认证主体 users.id
  action        = §4 表中的审计 action 名
  resource_type = company_employee / company_assignment
  resource_id   = 对象 id（创建前为 NULL）
  tenant_id     = 对象 tenant；space_id = 分配相关用例的空间，否则 NULL
  result        = 'success'（V1 不记录拒绝/失败行）
  risk_level    = LOW（生命周期转换/终止 = MEDIUM）
  correlation_id= 调用方传入或生成
  metadata      = 白名单键（如 operation / from / to / fields）；**禁止**凭据、密钥、整行数据

禁止：写 events（不产生事件、不建 producer/handler、不建 event trigger）
禁止：审计失败被吞（审计不可用 ⇒ 事务失败）
```

## 7. Error Contract

```text
域错误（domains/company/errors.py · 纯常量）
  EMPLOYEE_LIFECYCLE_CONFLICT · ASSIGNMENT_LIFECYCLE_CONFLICT · INVALID_EMPLOYEE_NO ·
  INVALID_ASSIGNMENT_ROLE · EMPLOYEE_ALREADY_TERMINATED · ASSIGNMENT_ALREADY_ENDED

服务错误（services/company/errors.py · 对外稳定码）
  INVALID_INPUT · EMPLOYEE_NOT_FOUND · EMPLOYEE_NO_CONFLICT · EMPLOYEE_USER_CONFLICT ·
  ASSIGNMENT_NOT_FOUND · ASSIGNMENT_CONFLICT · TENANT_NOT_ACTIVE · SPACE_NOT_FOUND ·
  SPACE_NOT_ACTIVE · AUTHORIZATION_DENIED · RESOURCE_NOT_PROVISIONED · AUDIT_UNAVAILABLE

DB 约束 → 稳定码映射（实现轮完成；不得把约束名/SQL 抛给调用方）
  uq_company_employees_no            → EMPLOYEE_NO_CONFLICT
  uq_company_employees_user          → EMPLOYEE_USER_CONFLICT
  uq_company_assignments_active      → ASSIGNMENT_CONFLICT
  触发器 tg_company_assignment_tenant_consistency → 视为内部一致性错误（映射为不透明失败码，
                                        绝不回显触发器消息）
  ck_company_*                       → INVALID_INPUT（或对应生命周期码）

禁止泄露：SQL 文本 · 约束/触发器名 · 堆栈 · 跨租户存在性线索 · 数据库用户名/DSN
```

## 8. Test Contract（未来测试 · 本轮不创建测试文件）

```text
L1 域单元测试（无数据库）：生命周期转换、不变量、值对象合法性、错误码常量
L2 服务测试（一次性隔离库）：每用例的 ALLOW/DENY、门禁、幂等/并发、审计行、事务回滚
L3 授权集成测试：权限键 ↔ action ↔ resource_type 匹配；缺失授权 = DENY；
                  集合资源缺失投影 = DENY（按 G2 裁定后的语义断言）
L4 仓储集成测试：tenant 谓词强制、约束冲突 → 稳定错误码、rowcount 语义、无跨租户查找
L5 边界/守卫测试：domains 纯度（禁 ORM/services/infrastructure）、单一授权引擎、
                  无事件、0019 未被修改（哈希）

要求：
  * 显式 allowlist 运行；禁止目录级 sweep
  * tests/unit/test_generate_build_info.py 执行数 = 0（冻结禁令）
  * 共享测试库策略见 GAP-G7 裁定
  * 本轮**不创建任何测试文件**
```

## 9. 实现顺序建议（供授权时裁定）

```text
STEP 1  domains/company/ 纯契约（entities / values / ports / errors）
STEP 2  services/company/ 仓储与投影实现（依赖 GAP-G2 裁定）
STEP 3  services/company/use_cases.py（授权 → 门禁 → 校验 → 写入 → 审计）
STEP 4  权限授予（依赖 GAP-G1 裁定；平台侧才可能出现 ALLOW）
STEP 5  测试（§8）与证据（一次性隔离库）
STEP 6  manifest/守卫同步（依赖 GAP-G3 授权）

说明：STEP 1–3 可在 G1/G2 未定时编码，但**不可判定为可用**（所有用例恒 DENY）。
```

## 10. 可追溯性（契约 ↔ 冻结决策）

| 契约条款 | 冻结依据 |
| --- | --- |
| §1 域纯度 / 禁 ORM | D-P20D-11 · 既有守卫 G-4 |
| §2 服务层编排 / 无事件 | D-P20D-08 · D-P20D-09 |
| §3 端口与实现分离 | D-P20D-11 |
| §4 用例与权限键 / delete·admin 不使用 | D-P20D-03 · D-P20D-04 · D-P20S-08 |
| §4 bind_user 不产生授权 | D-P20D-05 |
| §5 集合资源 / 无实例资源 | D-P20D-02 |
| §5 缺投影 = DENY | 附录 AF.2 D-P20D-02 后果① |
| §6 审计同事务 / 无事件 | D-P20S-11 · D-P20D-09 |
| §4 生命周期门禁（tenant/space active） | D-P20D-06（不修改 P18；不自动级联） |
| 未纳入矩阵的 list/delete/admin | GAP-G8（需确认范围） |

**END OF P20 COMPANY DOMAIN IMPLEMENTATION CONTRACT（DRAFT · 8 个契约域 + 10 个用例 + 3 个端口 · 未实现 · 未授权 · 待 GAP-G1/G2 裁定；2026-10-02）**
