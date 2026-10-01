# P18 DEPENDENCY MAP

# PLATFORM CONTROL PLANE / TENANT-SPACE LIFECYCLE

```text
性质   = PREP 附件 + FINAL FORM（P18 Human Decision Freeze 后定稿）
基线   = UAP-V0.1.16-P17-IDENTITY-TENANT-SPACE-RUNTIME（9fe282b0）
状态   = FINAL（决策已冻结 · 见 PDL 附录 Z / P18 Implementation Contract）
```

---

## 1. 决策继承链（Decision inheritance）

```text
P13  authorization vocabulary（permissions 12 · acl_subject_types 3 · platform_admin seed）
      ↓ 继承：词表冻结 / 不得新增 permission
P14  database trust boundary（6 个 uap* 主体 · uap_runtime 最小面 · default ACL 0）
      ↓ 继承：结构写不得落在 uap_runtime
P15  event / consumer foundation（Production Allowlist = EMPTY）
      ↓ 继承：P18 不得激活 event/handler
P16  agent runtime（Agent ≠ User · ToolGate 单一授权路径 · head = 0018）
      ↓ 继承：结构生命周期与 agent 面互不交叉
P17  identity / tenant / space runtime（context · membership · canonical authorization ·
     resource projection precondition · audit atomicity）
      ↓ 继承：runtime 语义不得改动；P18 只在 runtime 之前插入结构段
P18  control plane / tenant-space lifecycle（本轮 PREP · 待裁定）
```

## 2. 跨阶段不变量（不可继承性速查）

| 不变量 | 来源 | P18 的处置 |
|---|---|---|
| permissions = 12（词表冻结） | P13 | 不得新增；结构生命周期不得变成新 permission taxonomy |
| uap_runtime 最小面（56） | P14 | 不得扩大（收窄需单独决策） |
| default ACL = 0 · public PUBLIC grants = 0 | P14 | 保持 |
| Production Event Allowlist = EMPTY · Handlers = 0 | P15/P16 | 保持 |
| migration head = 0018（P17 无 migration） | P16/P17 | P18 默认 migration = NONE |
| 资源投影是授权前置条件（缺失 ⇒ DENY） | P17 | 结构 provisioning 必须同时投影 |
| membership 变更 + 审计原子 | P17 | 结构变更同样要求原子 |
| cross-tenant / cross-space = DENY | P17 | 控制面 API 必须同样防跨域与枚举 |
| Core → Domain = 0 | 全局 | P18 不得引入 core → control plane / API / infra |

## 3. 模块依赖方向（提案 · 待冻结）

```text
（提案）控制面
  HTTP（若裁定暴露）
        ↓
  Control Plane Use Case（授权 · 事务边界 · 审计编排）
        ↓
  Control Plane Provisioning Capability（services/control_plane/provisioning.py · P17 已存在）
        ↓
  Control Plane Persistence / Repository（结构对象 + 资源投影）
        ↓
  Control Plane DB Principal（uap_bootstrap 或专用主体 · 待裁定）

（现状 · 不得改动）
  P17 Runtime：API → Use Case → identity_runtime / authorization → repository → infrastructure

（禁止）
  Core → Domain / Service / Infrastructure / API
  runtime → 控制面 capability（P17 守卫已禁止：runtime 路径不得调用 provisioning）
  控制面 → runtime 业务路径（控制面不得依赖 membership 运行时语义做结构判定）
```

## 4. 数据依赖图（结构对象 → 授权前置）

```text
tenants ──（RESTRICT）──> spaces
   │                        │
   │（CASCADE）              │（CASCADE）
   ├──> roles(tenant)        ├──> roles(space)
   ├──> tenant_memberships   └──> memberships(space)
   └──> memberships(space)

tenants ──（RESTRICT）──> resources（tenant/space/member 集合投影）
spaces  ──（RESTRICT）──> resources（space/member 集合投影）

roles ──（RESTRICT）<── tenant_memberships / memberships（role 不得先删）
audit_logs：无结构外键（append-only · 历史事实不随删除消失）
platform_state：单例 · 与结构无 FK
platform_memberships：user(CASCADE) · role(RESTRICT)
```

```text
推论：
1. 只要存在 space 或 resource 行，tenant 就**无法硬删除**（RESTRICT）。
2. 删除 role 会破坏 membership（RESTRICT）——结构删除顺序被 DB 强制。
3. 硬删除 tenant 会 CASCADE 掉 roles / tenant_memberships / memberships，
   但不会删除 audit_logs（历史保留）。
4. 资源投影必须与结构对象同事务（投影失败不得留下半个结构）。
```

## 5. 授权依赖（两层决策不得互相替代）

```text
Layer 1（P18 待定义）：actor 是否可以执行**控制面结构操作**
   · 复杂度：结构对象在创建前不存在 resource 行 ⇒ 无法用对象自身资源做决策
   · 候选：既有 canonical permission + 平台/控制面 scope（D06）
Layer 2（P17 已冻结）：actor 是否可以在**既有结构中**管理 membership
   · member.read / member.admin + canonical resource（projection）
两层不得互相替代：
   · Layer 2 的 member.admin ≠ tenant.create / space.create
   · Layer 1 的授权成功不得自动授予 Layer 2 的运行时权限
   · 任何授权失败不得回落到平台管理员或 bootstrap（§27）
```

## 6. 安全依赖

```text
控制面安全 = 授权（actor）+ 主体边界（DB principal）+ 审计（actor 与 principal 分离）
             + 事务原子性 + 防枚举 + 幂等
必须同时成立；缺一即为 release blocker 级风险

依赖既有安全资产（不得重建）：
  · canonical AuthorizationService（唯一授权引擎）
  · audit_logs append-only 触发器（历史不可篡改）
  · constraints/triggers（role scope shape · membership role scope · resource tenant/space 一致性 ·
    platform bootstrap gate · last-admin 保护 · audit 不可变）
  · scripts/privileges.materialize()（官方授权物化；P18 若新增控制面授权必须纳入同机制）
```

## 7. 未来模块依赖

```text
Company / Commercial / Entertainment / Industry Templates
        ↓ 依赖
   稳定的 tenant/space 生命周期 + 隔离语义 + 初始管理员模型（P18）
        ↓ 依赖
   P17 上下文/授权/membership 运行时（已发布）

Future Event Runtime
        ↓ 依赖
   稳定的结构事实（谁创建/何时创建/证据来源），否则 tenant.created / space.created 语义模糊
   ⇒ P18 必须先固定结构生命周期；但**不得激活** event/handler
```

## 8. 测试依赖

```text
P18 测试必须建立在既有基线上（不得回归）：
  P17 = 97/0 · P16 = 33/0 + 8/0 · P15 = 65/0 · architecture guards = 57/0
  forbidden tests = 0 · OI-G-4 = 0 · Core → Domain = 0
  formal DB（uap）必须保持不变；测试使用一次性隔离库 + 官方 migrations + 官方授权物化
新增测试类别（PREP 提案）：
  tenant create/read/update/lifecycle/cross-scope/duplicate/unauthorized
  space   create/read/update/lifecycle/foreign tenant/duplicate/unauthorized
  provisioning（tenant/space + resource + initial admin）· failure（resource/membership/audit/
  authorization/DB）· bootstrap gate 不可绕过 · DB principal 边界（§68–§70）
```

---

## 9. FINAL FORM（FROZEN · 2026-10-01）

### 9.1 阶段依赖链（final）

```text
P13  canonical permissions / role model
      ↓
P14  DB security principals
      ↓
P15  audit / event foundation
      ↓
P16  Agent Runtime
      ↓
P17  identity / tenant / space runtime
      ↓
P18  control-plane lifecycle
      ↓
future business modules
```

### 9.2 数据库职责分层（final · 四层不可混同）

```text
uap_migrator  = schema authority
uap_bootstrap = one-time platform bootstrap authority
uap_control   = structural control-plane authority（P18 新增 · 最小写面 · 无 DELETE）
uap_runtime   = ordinary runtime authority（保持不变 56 grants）
uap_app       = readiness / audit append surface（不变）
uap_seed      = 命名存在 · 无权限 · 未使用（不变）
```

### 9.3 应用路径分层（final · 两条路径不得混为一谈）

```text
结构路径：Actor → Control Plane Authorization（platform_admin + platform scope + resource=None）
          → Control Plane Use Case（授权 · 事务 · 审计）→ uap_control
运行路径：Actor → P17 Context → Canonical Authorization → 业务 / Agent 执行 → uap_runtime
横切    ：audit_logs（append-only）· correlation · lifecycle/context gate（先 gate 后授权）
```

### 9.4 结构依赖（final）

```text
tenant provisioning ⇔ tenant 行 + tenant resource + tenant membership collection resource +
                      tenant administrator role + role_permissions + initial tenant membership + audit
space  provisioning ⇔ space  行 + space  resource + space  membership collection resource +
                      space administrator role + role_permissions + initial space membership + audit
（同一逻辑事务；任一步失败 ⇒ 全量回滚；逻辑删除不物理删除 projection）
```

### 9.5 安全债登记（final）

```text
F-P18-S-01  uap_runtime 保留 P14 遗留的 resources INSERT/UPDATE
            状态：DEFERRED HARDENING DEBT（非 P18 acceptance blocker · 本版不撤销）
            约束：P18 运行时实现不得使用；不是权限扩张；未来独立 hardening decision 处理
F-P18-D-01  space administrator role 形状以冻结 DB 约束为准（tenant_id NULL · space_id 非空；
            tenant 归属经 spaces.tenant_id 表达）
F-P18-D-02  tenant membership 重邀请语义不变（future independent decision）
```

**END OF P18 DEPENDENCY MAP（FINAL FORM · 决策已冻结 · 依赖链 / 四层主体 / 两条路径 / 结构依赖 / 安全债；2026-10-01）**
