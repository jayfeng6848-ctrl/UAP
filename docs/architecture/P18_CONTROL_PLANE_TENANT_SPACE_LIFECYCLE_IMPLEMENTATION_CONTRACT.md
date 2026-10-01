# P18 CONTROL PLANE / TENANT-SPACE LIFECYCLE — IMPLEMENTATION CONTRACT

```text
状态        = FROZEN（由 P18 Human Decision Freeze 冻结 · 2026-10-01）
派生自      = PDL 附录 Y（P18 PREP）+ 附录 Z（P18 HUMAN DECISION FREEZE）
              + P18_HUMAN_DECISION_PREP.md（勘验）+ P18_CONTROL_PLANE_GAP_RECORD.md（缺口与裁定）
基线        = UAP-V0.1.16-P17-IDENTITY-TENANT-SPACE-RUNTIME（commit 9fe282b0 · tree de420083）
优先级      = 本文件不得与 P13/P14/P15/P16/P17 冻结语义冲突；
              若文本描述与既有冻结 DB 约束冲突，以**冻结 DB 约束**为准并记录澄清
              （见 P18_CONTROL_PLANE_GAP_RECORD.md §6 F-P18-D-01）
实现授权    = AUTHORIZED（但本轮 NOT STARTED）
```

---

## 1. 范围

```text
IN
  tenant lifecycle（provision · read · metadata update · lifecycle transition）
  space  lifecycle（provision · read · metadata update · lifecycle transition）
  provisioning（结构对象 + canonical resource projection + 初始管理员）
  初始角色 provisioning（非 system · 作用域匹配 · 绑定既有 canonical permission）
  control-plane authorization（platform_admin-only · 复用既有 AuthorizationService）
  control-plane API（独立命名空间 · 无物理删除端点）
  audit · atomicity · idempotency · error model · privilege ceiling · test matrix

OUT
  修改 P13/P14/P15/P16/P17 冻结语义 · 新 permission（保持 12）· 扩大 uap_runtime
  migration / 新表 / schema 变更 · Production Event / Handler 激活
  ACL（resource_permissions）管理 · 业务模块（Company / Commercial / Entertainment）
  tenant membership 重邀请语义修复 · resource GC
```

---

## 2. 控制面边界（Control Plane ≠ Runtime）

```text
CONTROL PLANE = structural authority（创建/供给/结构化管理平台容器）
RUNTIME       = operational authority（在已供给的容器内运行）

四层数据库安全主体职责（永久冻结，不得混淆）：
  uap_migrator  = schema authority
  uap_bootstrap = one-time platform bootstrap authority
  uap_control   = structural control-plane authority
  uap_runtime   = ordinary runtime authority

禁止：uap_migrator ≠ control plane · uap_bootstrap ≠ general control plane ·
      uap_control ≠ runtime · uap_runtime ≠ control plane
```

## 3. uap_control（P18-D01）

```text
新建专用控制面主体 uap_control；不得复用 uap_bootstrap / uap_runtime / uap_app / uap_migrator
role hardening（遵循 P14 既有约定）：
  LOGIN = YES · SUPERUSER = NO · CREATEDB = NO · CREATEROLE = NO · REPLICATION = NO ·
  BYPASSRLS = NO · INHERIT = NO（除非既有安全约定另有要求）
  NO SET ROLE uap_migrator · NO SET ROLE uap_bootstrap · NO role escalation
应用连接时即为 uap_control；不得通过 SET ROLE 自我提权
```

### 3.1 写面 ceiling（P18-D13）

```text
allowed writes：
  tenants            INSERT, UPDATE
  spaces             INSERT, UPDATE
  roles              INSERT
  role_permissions   INSERT
  tenant_memberships INSERT
  memberships        INSERT
  resources          INSERT
  audit_logs         INSERT
forbidden writes（明确拒绝）：
  任何 DELETE（tenants/spaces/roles/role_permissions/tenant_memberships/memberships/resources）
  permissions · acl_subject_types · resource_permissions · platform_memberships · platform_state ·
  credentials · identities · sessions · devices · ai_request_logs · tool_executions · events
  audit_logs UPDATE / DELETE
```

### 3.2 读面 ceiling

```text
需要的读面：users · tenants · spaces · roles · permissions · role_permissions ·
            tenant_memberships · memberships · platform_state · platform_memberships · resources
具体 SELECT 必须由实际 repository 查询图推导；禁止 GRANT SELECT ON ALL TABLES
```

### 3.3 版本化授权来源（P18-D13 · PREP STOP-3）

```text
全部 P18 控制面授权必须具备**版本化、可审计**的物化来源：
  复用 scripts/privileges 机制，新增 CONTROL_PLANE（P18）基线；
  PostgreSQL 角色创建与表授权是两个独立步骤，均需版本化来源
禁止：private GRANT · 手工 psql 创建且无 source · 未记录的权限
月度分区：audit_logs_202610 等分区必须由官方物化覆盖 uap_control INSERT（不得 private GRANT）
```

---

## 4. 租户生命周期（P18-D02）

```text
状态集合 = 既有 schema 状态，不新增：provisioning · active · suspended · archived · deleted

状态迁移（冻结）：
  provisioning → active        （仅由成功的 provisioning 完成）
  active       ↔ suspended
  active       → archived
  suspended    → archived
  archived     → active
  archived     → deleted
  deleted      = terminal logical tombstone（deleted → 任何状态 = DENY）

provisioning 语义 = transactional provisioning state only：
  BEGIN → tenant = provisioning → 全部必需 provisioning → tenant = active → COMMIT
  正常情况下外部只观察到 active；任意失败 ⇒ ROLLBACK（tenant 行不得残留）

物理删除：Tenant physical DELETE = NEVER in P18（不提供 DELETE，也不以 cascade 模拟）
  理由：spaces/resources = RESTRICT；roles/memberships = CASCADE ⇒ 物理删除会形成危险的历史级联
  保留：audit · membership history · role history · resource projection
```

## 5. 空间生命周期（P18-D02 · Q18）

```text
状态集合 = 既有 schema 状态：active · archived · deleted（P18 不定义 space suspended；
            schema 不支持，且不引入 schema 变更）
状态迁移（冻结）：
  create（事务内）→ active
  active   ↔ archived
  archived → deleted
  deleted  = terminal（deleted → 任何状态 = DENY）
无 space provisioning 状态（create 语义为事务内直接 active）
物理删除：不提供（同 tenant 理由：resources.space_id = RESTRICT）
Space 不能脱离 Tenant 存在（tenant_id NOT NULL + FK RESTRICT）
```

## 6. 首个管理员（P18-D03 / P18-D04）

### 6.1 Tenant 首个管理员

```text
initial_admin_user_id = 显式必需输入（不得由 owner/actor/platform_admin 自动推断；
                         tenants 无 owner_id 列）
被指定 User 必须：exists + active
不要求：已属该 tenant（tenant 尚未存在）· 不要求 platform membership
允许：platform administrator 为普通 User U provisioning Tenant T，随后 U 成为 T 的首个管理员
```

### 6.2 Space 首个管理员

```text
initial_space_admin_user_id = 显式必需输入
被指定 User 必须：exists + active + **已是目标 tenant 的有效成员**
不得自动创建 tenant membership（space bootstrap 不绕过 tenant 前置条件）
控制面可以建立第一个 space membership = provisioning authority（非 P17 runtime 授权绕过）
```

## 7. 初始角色（P18-D05）

```text
P18 仅可为生命周期自举创建**非 system** 的作用域管理员角色（tenant administrator / space administrator）
禁止：arbitrary role creator · system role 创建 · system role 修改 · permission 修改

tenant administrator role：
  is_system = false · scope = TENANT · tenant_id = 目标 tenant · space_id = NULL
  绑定既有 canonical permission：member.read · member.admin · tenant.admin

space administrator role：
  is_system = false · scope = SPACE · space_id = 目标 space
  tenant 归属由 spaces.tenant_id 表达（冻结触发器要求 SPACE 角色 tenant_id IS NULL —
  见 GAP RECORD §6 F-P18-D-01）
  绑定既有 canonical permission：space.admin · member.read · member.admin

No new permissions（permissions 保持 12）；角色 key/name 必须遵循既有 schema/unique convention；
不得以 role name 字符串执行授权判断

角色不可变性（provisioning 之后）：
  P18 不提供 role UPDATE / DELETE、role_permissions UPDATE / DELETE
  未来若需 custom roles ⇒ 必须新开 Human Decision

retry：若发现既有角色，仅当 exactly matching 才可复用；否则 CONFLICT（不得覆盖）
```

## 8. 资源投影（P18-D02 · Q20）

```text
严格复用 P17 已冻结的 canonical 表示，不得发明新 resource grammar：
  tenant 对象        → resources(resource_type='tenant', tenant_id=T, space_id NULL)
  space  对象        → resources(resource_type='space',  tenant_id=T, space_id=S)
  tenant membership 集合 → resources(resource_type='member', tenant_id=T, space_id NULL)
  space  membership 集合 → resources(resource_type='member', tenant_id=T, space_id=S)
幂等键：natural_key（既有部分唯一索引）
成功 provisioning 必须同时成立：
  tenant 行 + tenant resource + tenant membership collection resource
  space  行 + space  resource + space  membership collection resource
  （scope：tenant_id / space_id 必须一致）
投影失败 ⇒ 整个事务回滚（不得留下 tenant/space 存在但 resource 缺失的状态）
逻辑删除不物理删除 projection；resources retained；P18 不实现 resource GC
控制面只 INSERT projection，不 DELETE；不得写 resource_permissions（ACL 在 P18 之外）
```

---

## 9. 控制面授权（P18-D06）

```text
P18 结构操作 = platform_admin-only（第一版不允许 tenant/space admin 执行结构操作）
唯一授权引擎 = 既有 AuthorizationService（**不得**创建 ControlPlaneAuthorizationEngine）

pre-resource structural authorization（冻结）：
  existing AuthorizationService + explicit platform scope + resource = NULL
  要求：authenticated actor + 显式 PLATFORM membership + role = platform_admin + permission = admin
  才允许 structural provisioning

如果既有引擎当前无法表达 platform scope + resource = None：
  仅允许对既有 AuthorizationService 做**最小 additive capability**
  必须先用真实 DB + canonical service 证明该入口可安全、可重现
  否则 STOP；绝对不得写 platform-admin `if` 分支，不得创建第二套授权系统

禁止：授权失败 → 回落 platform_admin / bootstrap；role name 字符串判权；owner_id 隐式授权；
      SET ROLE 提权；DB principal 取代 actor 判定
```

### 9.1 控制面操作白名单（超出即拒绝）

```text
tenant provision · tenant metadata update · tenant lifecycle transition
space  provision · space  metadata update · space  lifecycle transition
initial role provisioning · initial membership provisioning · resource projection · audit
```

## 10. 平台引导边界（P18-D07）

```text
既有一次性平台 bootstrap 保持不变
platform_state = uninitialized ⇒ P18 tenant/space structural provisioning = DENY
不得由 P18 自动初始化平台；必须先经既有 bootstrap 路径完成 uninitialized → initialized
platform_memberships 仍在普通 P18 生命周期 API 之外；uap_bootstrap 保持既有 bootstrap 绑定能力，
且 P18 **不扩大** uap_bootstrap 权限
last platform_admin protection（P11）保持不变，P18 不绕过
```

## 11. 幂等（P18-D08）

```text
natural-key idempotency + exact-match replay + conflict on mismatch
tenant：natural key = 既有 slug unique(lower)
space ：natural key = 既有 (tenant_id, key)
role / role_permissions / resource projection / initial membership：使用既有 natural 唯一性
同请求重试 ⇒ 相同逻辑结果（exact replay）；同 key 不同不可变身份 ⇒ CONFLICT（不得静默覆盖）
不新增 dedup table / idempotency_keys 等辅助表
```

## 12. 原子性（P18-D09）

```text
ONE LOGICAL TRANSACTION：
  tenant provisioning = platform authorization → tenant row → tenant resource →
                        tenant member collection resource → tenant admin role → role_permissions →
                        initial tenant membership → audit → COMMIT
  space  provisioning = platform authorization → space row → space resource →
                        space member collection resource → space admin role → role_permissions →
                        initial space membership → audit → COMMIT
任一失败（resource / role / role_permissions / membership / audit / DB）⇒ ROLLBACK EVERYTHING
最终不得出现：orphan tenant / orphan space / orphan role / orphan membership / orphan projection
audit 失败 ⇒ provisioning 回滚（与 P16「execution failure → durable FAILED」语义明确区分）
```

## 13. API（P18-D10）

```text
authenticated dedicated control-plane namespace（不进入 P17 runtime 命名空间；命名遵循仓库既有 convention）
能力：
  Tenant: provision · read · metadata update · lifecycle transition
  Space : provision · read · metadata update · lifecycle transition
  Membership: 仅 initial membership provisioning（普通 membership 变更仍属 P17 runtime）
禁止：物理删除端点（DELETE /…/tenants/{id} · DELETE /…/spaces/{id}）⇒ 使用 PATCH lifecycle/state
禁止：通用数据库 CRUD
安全：即使命名空间为 /control/... 也**不是** trusted internal endpoint；
      必须 authenticated + explicit platform-admin authorization
防枚举：授权先于对象细节披露；不得泄露 foreign tenant 存在性/名称/space/resource
错误模型：复用既有 application error conventions（允许 additive P18 错误类型，
          不得创建并行错误框架）；PostgreSQL 错误不得原样返回（无 constraint/SQL/stack/DB detail）
```

## 14. 审计（P18-D11）

```text
所有安全敏感结构操作必须审计，至少：
  tenant provision / metadata update / suspend / archive / restore / delete
  space  provision / metadata update / archive / restore / delete
  initial role provisioning · initial membership provisioning · resource projection
审计 actor = 真实认证平台主体（不得以 uap_control / uap_bootstrap / uap_migrator 替代）
内容：actor · target · tenant · space(适用) · operation · before/after lifecycle state(适用) ·
      correlation · timestamp
禁止：password · session token · credential plaintext · secret · SQL · stack trace · raw Authorization header
DB principal = database authority；Actor = application authority；两者持续分离
```

## 15. 运行时影响（P18-D14 派生规则）

```text
仅 ACTIVE Tenant 可建立正常运行上下文；仅 ACTIVE Space 可建立正常 space 上下文
  tenant = suspended / archived / deleted ⇒ P17 runtime context = DENY
  space  = archived / deleted            ⇒ space context = DENY
  顺序：lifecycle/context gate → existing authorization（不是第二套授权）

Agent（P16）：
  Agent.tenant_id = T 且 T 非 ACTIVE ⇒ Agent Run admission = DENY
  space-scoped agent 要求 Space = ACTIVE
  不得因 tenant archived 而让 Agent 继续正常运行

Membership runtime（P17）：
  tenant suspended/archived/deleted ⇒ 常规 P17 membership 操作 = DENY
  space  archived/deleted           ⇒ 常规 P17 space membership 操作 = DENY
  不删除 membership history · 不做 cascade cleanup

Owner / visibility：
  spaces.owner_id = metadata / business reference（不是授权，不是自动管理员，不产生权限继承）
  tenant 无 owner 语义
  visibility（private/tenant/link）= 可发现性/呈现元数据（不是授权；不得绕过 tenant/space membership）
  visibility 仅可经认证的控制面操作 + 审计修改；不改 membership / role / ACL

资源保留：逻辑删除不物理删除 projection（依赖 lifecycle gate 使授权失败）
唯一键/重邀请：继续继承 P17（removed membership 仍占用唯一键 ⇒ re-invite = MEMBERSHIP_DUPLICATE）
              P18 不修复（future independent decision）
```

## 16. 事件边界（P18-D12）

```text
Production Event Activation = REJECT
Production Event Allowlist = EMPTY · Handlers = 0
即使 tenant/space 创建/归档/删除，也只写 audit，不发布 production event
不激活：tenant.created · space.created · tenant.archived · space.deleted
事件由后续独立 Human Decision 决定
```

## 17. 权限与安全基线（P18-D13）

```text
uap_runtime：保持 56（tenants/spaces = SELECT only）；P18 不扩大
uap_app = 5 · uap_migrator = 245 · default ACL = 0 · public schema PUBLIC grants = 0
新增：uap_control（见 §3 的写/读 ceiling 与禁止面）
F-P18-S-01：uap_runtime 仍持有 resources INSERT/UPDATE（P14 残留）——
            DEFERRED HARDENING DEBT · 非 P18 acceptance blocker · 本版不撤销 ·
            **P18 运行时实现不得使用该权限**
migration = NONE（head 保持 0018_p16_agent_runtime）· new tables = 0 · schema unchanged
Core → Domain = 0
```

## 18. 测试契约

```text
执行身份：全部真实 DB 控制面测试以 uap_control 运行；不得用 superuser / uap_migrator
          执行控制面业务操作；测试库为一次性隔离库（full migration chain + 官方授权物化 + 官方 provisioning）

正路径：tenant provision · space provision（tenant 已存在）· tenant metadata update ·
        space visibility update · suspend ⇒ 运行时不可用 · restore ⇒ 运行时恢复 ·
        archive ⇒ 运行时不可用 · archived → deleted ⇒ terminal
        initial tenant admin：tenant + role + member.read/member.admin + membership + resources + audit 齐备
        initial space admin：space + role + member.read/member.admin/space.admin + membership +
                             resources + audit 齐备 且 initial user 已属 tenant
安全负路径（至少 N1–N20）：
  N1 非 platform 用户 → 控制面 API        N2 tenant admin → create tenant
  N3 tenant admin → create space          N4 space admin → create tenant
  N5 space admin → tenant lifecycle       N6 agent → 控制面 API
  N7 worker → 控制面 API                  N8 uap_runtime → tenant INSERT
  N9 uap_runtime → space INSERT           N10 uap_runtime → role INSERT
  N11 uap_runtime → role_permissions INSERT  N12 uap_control → permissions WRITE
  N13 uap_control → resource_permissions WRITE  N14 uap_control → platform_memberships WRITE
  N15 uap_control → migrator escalation（SET ROLE / CREATE ROLE / DDL = 拒绝）
  N16 uninitialized platform → tenant provision
  N17 cross-tenant structural target      N18 forged initial_admin_user
  N19 invalid role scope                  N20 resource projection omission
半初始化注入：resource / role / membership / audit 失败 ⇒ 对象缺席（无 orphan）
重试：同 key 同请求 ⇒ exact idempotent；同 key 不同不可变身份 ⇒ conflict
生命周期：tenant（active↔suspended · active→archived · archived→active · archived→deleted ·
          deleted→* DENY）· space（active↔archived · archived→deleted · deleted→* DENY）
运行时回归：suspended/archived/deleted ⇒ P17 context DENY；space archived/deleted ⇒ space context DENY；
            P16 Agent Run admission DENY（lifecycle inactive）
回归基线：P17 全部通过（97 + 经批准新增生命周期用例）· P16 33/0 + 8/0 · P15 65/0 ·
          architecture guards 全部通过 · forbidden tests = 0 · OI-G-4 = 0 · Core → Domain = 0
测试治理：显式 allowlist；禁止 pytest/tests/ 目录级；禁止 skip/xfail/deselect 掩盖失败
正式库：uap prestate == poststate；P18 测试绝不针对正式库执行
```

## 19. 实现顺序（下一轮 · 已授权但本轮不启动）

```text
第 1 步（先验证，不写业务代码）：
  证明既有 AuthorizationService 可执行 platform-scope + resource=None 授权
  核验实际 role / role_permissions schema、resource schema
  核验 uap_control 精确权限需求与版本化授权路径
  若 resource=None 无法安全且可重现 ⇒ STOP（不得发明 platform-admin if 分支）
第 2 步：Wave 1 控制面持久化 → Wave 2 provisioning 事务 → Wave 3 生命周期 →
        Wave 4 API → Wave 5 测试
```

## 20. 明确禁止（汇总）

```text
改 P13–P17 冻结语义 · 新增 permission · 扩大 uap_runtime · 新表 / migration / schema 变更 ·
激活 production event / handler · ACL 管理 · 修复 tenant 重邀请 · 业务模块 ·
uap_control 任何 DELETE · uap_control 写 permissions/resource_permissions/platform_* ·
SET ROLE 提权 · 授权失败回落 · role name 判权 · owner_id 隐式授权 · runtime 自建 resource ·
通用 CRUD 化 · 绕过 lifecycle gate · 手工无源授权
```

**END OF P18 CONTROL PLANE / TENANT-SPACE LIFECYCLE IMPLEMENTATION CONTRACT（FROZEN · P18-D01…D14 + Q14…Q20 · Formal DB unchanged · 无实现 / 无 migration / 无 commit；2026-10-01）**
