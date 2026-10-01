# P17 ACCEPTANCE EVIDENCE

```text
阶段        = P17 ACCEPTANCE GATE（NO RELEASE）
结论        = P17 ACCEPTANCE = PASSED
基线        = UAP-V0.1.15-P16-AGENT-RUNTIME
              HEAD = origin/main = 42a4f61c20fe119af77ab822e24c8028ce653e3d（tag 14）
权威        = PDL 附录 W（P17 Freeze）· 附录 X（Authorization Gap Resolution）
              · P17 Implementation Contract §1–§12
日期        = 2026-10-01
```

---

## 1. Acceptance scope

```text
验证对象 = P17 PLATFORM IDENTITY / TENANT / SPACE RUNTIME（平台上下文基座）
链路     = User → Identity → Tenant Membership → Tenant → (Space Membership → Space)
           → Role Context → Authorization
验证面   = 功能 · 安全 · 授权 · 事务 · Agent 集成 · P16/P15/P14 回归 · 架构 · DB/权限完整性
```

## 2. Decision baseline

```text
P17-D01=A D02=A D03=A D04=C D05=B D06=A D07=B D08=B D09=A D10=C D11=A D12=REJECT
D13=A D14=security-first          （附录 W · 未改写）
Authorization resolution           = OPTION A（附录 X）
Q1 Control Plane / Bootstrap resource provisioning
Q2 read/list = member.read ；create/update/delete = member.admin
Q3 platform_admin + tenant-scoped + space-scoped roles
Q4 scope 不互通
Q5 space 成员管理要求 operator tenant membership + space membership
```

## 3. Authorization resolution（实测）

```text
engine    = services/authorization.AuthorizationService（唯一引擎；未新增第二套）
mapping   = membership 操作 → (resource_type = member, action = read|admin)
resource  = canonical membership collection（tenant 级 space_id NULL / space 级 space_id S）
缺失资源   = DENY（fail closed）
无 membership context 时 = 仅当同一引擎在移除 tenant/space context 后仍 ALLOW（显式平台 scope
            授权或已 provisioning 的 ACL）才放行 —— 非 fallback
权限词表   = 12 → 12（未扩展）
```

## 4. Resource model

```text
projection  = services/control_plane/provisioning.py（Control Plane / Bootstrap）
kinds       = tenant · space · member collection（tenant/space 级）· agent
一致性      = tenant resource.tenant_id = tenant.id
              space resource.tenant_id = space.tenant_id · space_id = space.id
              tenant collection (tenant_id, member, space NULL)
              space collection  (tenant_id, member, space S)
幂等        = ensure_resource_projection / ensure_agent_projection（重复调用零新增）
原子性      = object + projection 同一 transaction；projection 失败 ⇒ object 回滚（实测）
资源缺失    = member.read / member.admin 均 DENY；runtime 不 auto-create（resources 行数不变）
backfill    = backfill_resource_projections（显式 / 手动 / 非 runtime 路径）
```

## 5. Context resolution

```text
固定顺序 = actor → tenant membership → tenant 可读 → (space 属该 tenant) → space membership → role
多租户   = U ∈ A 且 U ∈ B；显式选择 A → A；显式选择 B → B（无 first/default/last/global fallback）
tenant-only context 与 tenant+space context 均支持
context ≠ authorization（ResolvedContext 不含任何 ALLOW/DENY）
测试     = tests/integration/test_p17_context_resolution.py（11/0）
```

## 6. Membership operations

```text
tenant membership : read/list · create · update · delete（服务端校验 + rowcount=1 + 审计）
space  membership : read/list · create · update · delete
写前校验 = user 存在 · tenant 存在 · role 可分配 · role scope 与 membership scope 一致 ·
           role.tenant_id/space_id 与目标一致 · space 属目标 tenant · target user 已属目标 tenant
rowcount = 0 不得静默接受（实测：不存在/已删除的 membership → MEMBERSHIP_NOT_FOUND，零写入）
重复     = 显式冲突（无 upsert / 无静默幂等）
授权失败 = 零写入（跨租户 / 跨空间 / 缺 membership / 角色 scope 不符 / 资源缺失 / 权限不足）
```

## 7. Audit atomicity

```text
create / update / delete → membership 行 + audit 行（独立连接验证）
delete → audit 保留 role_before（审计事实不依赖已删除行）
audit 失败 ⇒ membership 变更回滚（独立连接确认无残留）
audit 内容 = actor · tenant · space(适用) · target user · role_before/after · action · correlation · 时间
             metadata key 集合 ⊆ {action, target_user_id, role_before, role_after}
             不含 password / token / Authorization header / credential / SQL / stack / secret
correlation = 复用既有 request context（x-correlation-id → use case → mutation → audit，一对一）
差异说明   = 与 P16「execution failure → durable FAILED」语义不同，本轮两者均独立成立
```

## 8. Agent integration

```text
agent tenant = agents.tenant_id（tenant-scoped 查询 · 无 id-only lookup）
agent space  = agents.space_id；非空时 request space 必须相同，否则 DENY
actor tenant = agent tenant 否则 DENY；owner 仅作 context，不构成授权来源
owner inheritance = 0（owner 持有 agent 资源 ACL allow，agent 侧仍 DENY）
Agent/User 分离  = 分别由 canonical engine 判定；最终执行仍需 P16 frozen 的 AND（P16 6/6 复验）
P16 runtime 代码 = 零改动
```

## 9. API

```text
router = apps/api/routes/identity_runtime.py（transport only · 已注册 main.py）
实际路由（实测枚举）：
  GET  /tenants                                        GET  /tenants/{tenant_id}
  GET  /tenants/{tenant_id}/spaces                     GET  /tenants/{tenant_id}/members
  POST /tenants/{tenant_id}/members                    PATCH/DELETE /tenants/{tenant_id}/members/{user_id}
  GET  /tenants/{tenant_id}/spaces/{space_id}/members   POST 同路径
  PATCH/DELETE /tenants/{tenant_id}/spaces/{space_id}/members/{user_id}
不存在（实测断言）：tenant/space CRUD · platform-memberships · roles · permissions ·
                   resource-permissions · /spaces · /memberships
target 一律来自 path；无 X-Current-Tenant / X-Current-Space；handler 无 SQL / 无角色名比较 / 无 is_admin
真实 HTTP 证据：POST → 201 + DB mutation 1 + audit 1（同 correlation）；
                PATCH → 200 + audit(role_before/after)；DELETE → 204 + audit 保留 role_before
```

## 10. Security negatives / positives

| 场景 | 结果 | 证据 |
|---|---|---|
| 跨租户（N1/N3/N6/N12） | DENY · 零写入 | test_p17_authorization.py · API 403 |
| 跨空间 / 伪造 space（N2/N5/N7/N13） | DENY · 零写入 | 同上 |
| 缺 tenant membership | DENY（MEMBERSHIP_REQUIRED） | 同上 |
| 角色 scope 不符（N9） | DENY（ROLE_SCOPE_MISMATCH）· 零写入 | 同上 |
| target user 不在目标 tenant（N8） | DENY（TARGET_NOT_IN_TENANT）· 零写入 | 同上 |
| visibility（link / tenant）不构成授权（N11） | DENY | 同上 |
| 资源缺失（member.read 与 member.admin） | DENY（RESOURCE_NOT_PROVISIONED）· 无 auto-create | acceptance |
| platform_memberships / roles / permissions / role_permissions / acl_subject_types / platform_state / resource_permissions 写尝试 | 数据库拒绝（SQLAlchemyError）· 行数不变 | acceptance + authorization |
| 平台授权移除后（无 fallback） | DENY | acceptance |
| 正路径：tenant membership read/create/update/delete | ALLOW + 审计 | authorization + acceptance |
| 正路径：space membership read/create/update/delete | ALLOW + 审计 | authorization + acceptance |
| 正路径：显式 platform authority | ALLOW（非 fallback） | authorization + API |
| 正路径：Q5 Case A（tenant+space 成员 + member.admin） | ALLOW | acceptance |

## 11. Test results（真实数据库 · uap_runtime 身份 · 显式 allowlist · 无 skip/xfail/deselect）

```text
tests/unit/test_p17_identity_runtime.py                 18 passed
tests/architecture/test_p17_boundaries.py               11 passed
tests/integration/test_p17_context_resolution.py        11 passed
tests/integration/test_p17_membership_atomicity.py       5 passed
tests/integration/test_p17_authorization.py             19 passed
tests/integration/test_p17_api.py                       10 passed
tests/integration/test_p17_agent_scope.py                7 passed
tests/integration/test_p17_acceptance.py                16 passed   ← 本轮新增 Acceptance 专项
-------------------------------------------------------------------
P17 合计                                                97 passed / 0 failed / 0 skipped

P16 单元 + 架构 + 安全                                   33 passed / 0 failed
P16 集成（6 scenarios + R-1 durability）                  8 passed / 0 failed
P15 显式 allowlist                                       65 passed / 0 failed
架构守卫（tests/architecture）                            57 passed / 0 failed
tests/unit/test_generate_build_info.py                   执行次数 = 0（forbidden = 0 · OI-G-4 = 0）
Core → Domain                                            0
```

## 12. Mutation matrix（实测一致）

| Operation | P17 runtime | Execution |
|---|---|---|
| tenant read / space read | YES | uap_runtime（membership-scoped） |
| tenant membership read/create/update/delete | YES | uap_runtime（canonical authorization） |
| space membership read/create/update/delete | YES | uap_runtime（canonical authorization） |
| tenant create/update/delete · space create/update/delete | NO | control-plane / bootstrap capability |
| platform_membership mutation | NO | 数据库拒绝（bootstrap/control-plane） |
| role / permission / role_permission / acl_subject_type / platform_state mutation | NO | 数据库拒绝（read-only） |
| resource_permissions（ACL）mutation | NO | 数据库拒绝（consume only） |

## 13. Regression / privilege / schema / DB

```text
P14 security regression : uap_runtime = 56 · uap_app = 5 · uap_migrator = 245 · uap* roles = 6
                          pg_default_acl = 0 · public schema PUBLIC grants = 0
                          tenants = SELECT only · spaces = SELECT only
P17 privilege delta     = 0（56 → 56）
Schema                  = UNCHANGED（new tables = 0 · schema modification = 0）
Migration               = NONE（migration files 止于 0018；fresh DB → upgrade head ⇒ 0018_p16_agent_runtime）
                          P17 migration files added = 0 · 无 0019
Production Event        = Allowlist EMPTY（production_allowlist().is_empty = True）· Handlers = 0
Formal DB（uap）        = prestate == poststate（public 表 0 · 无任何 seed/test data）
冻结基线 uap_b1_test     = tenants 0 · spaces 0 · roles 1 · resources 0 · permissions 12（未改动）
Temporary DBs           = uap_p17_test · uap_p17_atomic_test · uap_p17_auth_test · uap_p17_api_test ·
                          uap_p17_agent_test · uap_p17_acceptance_test · uap_p17_head_probe
                          全部 DROP（现存库仅 uap / uap_b1_test / uap_test）
```

## 14. Architecture

```text
Core → Domain = 0（test_dependency_rules PASS）
P17 守卫 = services/identity_runtime 仅写 tenant_memberships / memberships / audit_logs；
          无 GRANT/REVOKE/DDL；不构造 Decision；仅引用 canonical services.authorization；
          非传输层；无通用无作用域访问器；space 读取不以 visibility 为访问谓词；
          runtime 路径不得 provisioning；control_plane 非传输层且不依赖 runtime 行为模块
方向 = API → Use Case → Identity Runtime / Authorization → Repository → Infrastructure
```

## 15. Git

```text
HEAD = 42a4f61c20fe119af77ab822e24c8028ce653e3d（= origin/main · 未变动）
tags = 14 · staged = 0
P16 / P15 历史实现（services/agent · services/consumer · tests/integration/test_p16* ·
                    tests/integration/test_p15* · 0018）在 git diff 中零改动
本轮触碰的既有 tracked 文件仅 3 个（P17 集成所必需·非 P16/P15 实现）：
  apps/api/main.py（注册 P17 router）· apps/api/error_mapping.py（P17 错误映射）·
  services/use_cases/__init__.py（导出 P17 use cases）
commit = NO · tag = NO · push = NO
```

## 16. Historical findings（原始 observation 保留）

```text
F-RP-06（P15 manifest hash basis）              = CLOSED（历史）
F-P16-I-01…I-06                                  = 历史，未改写
F-P17-I-01（无 member 写权限）                    = OPEN → RESOLVED BY HUMAN DECISION（OPTION A）
F-P17-I-02（tenant/space/membership 无 resource） = OPEN → RESOLVED BY ARCHITECTURAL DECISION
F-P17-I-03（仅 platform_admin 有 role_permissions）= OPEN → RESOLVED BY PROVISIONING MODEL
原始 observation（resources=0 探针 · permissions 12 · 无其他 role_permissions）保留于
P17_MEMBERSHIP_AUTHORIZATION_GAP_RECORD.md，未删除、未改写为「从未出现」
```

## 17. Golden acceptance invariants（30 条 · 全部成立）

```text
1 User 为平台主体 ✓   2 多租户 ✓   3 tenant membership 显式 ✓   4 space membership 显式 ✓
5 tenant membership 不隐含任意 space ✓   6 tenant/space scope 不互通 ✓
7 cross-tenant DENY ✓   8 cross-space DENY ✓   9 visibility ≠ authorization ✓
10 context ≠ authorization ✓   11 resource existence 为授权前置 ✓   12 resource scope 为授权输入 ✓
13 member.read = read/list ✓   14 member.admin = membership mutation ✓   15 权限词表未扩展 ✓
16 platform membership 不在 runtime 变更面 ✓   17 system objects 对 runtime 只读 ✓
18 ACL 只读（consume）✓   19 tenant/space 结构写属 control-plane ✓   20 runtime 不自 provisioning ✓
21 membership 变更 + 审计原子 ✓   22 agent 不继承 user 权限 ✓   23 agent tenant/space 来自 agent 记录 ✓
24 既有 canonical AuthorizationService 为唯一引擎 ✓   25 无新 privilege ✓   26 无新表 ✓
27 无新 migration ✓   28 Production Event EMPTY ✓   29 Handlers = 0 ✓   30 Core → Domain = 0 ✓
```

**END OF P17 ACCEPTANCE EVIDENCE（P17 ACCEPTANCE = PASSED · 97/0 P17 · 33/0 + 8/0 P16 · 65/0 P15 · 57/0 guards · privilege delta 0 · formal DB unchanged · 未 commit / tag / push；2026-10-01）**
