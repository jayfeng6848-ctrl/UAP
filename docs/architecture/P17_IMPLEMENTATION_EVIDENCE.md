# P17 IMPLEMENTATION EVIDENCE

```text
阶段        = P17 IMPLEMENTATION → VALIDATION → EVIDENCE（NO RELEASE）
状态        = COMPLETE（Wave 3–6 已实现并验证；F-P17-I-01/02/03 = RESOLVED）
基线        = UAP-V0.1.15-P16-AGENT-RUNTIME
              HEAD = origin/main = 42a4f61c20fe119af77ab822e24c8028ce653e3d
              tree = 242c82f3a2ac90a53fe3ed2b908baf5c1bdf0528
权威        = PDL 附录 W（P17 Freeze）+ 附录 X（P17 AUTHORIZATION GAP RESOLUTION）
              + P17_IDENTITY_TENANT_SPACE_RUNTIME_IMPLEMENTATION_CONTRACT.md（§1–§12）
日期        = 2026-10-01
```

---

## 1. Human Decision（本轮适用）

```text
P17 Authorization Model = OPTION A（复用既有 12 canonical permissions · 不扩展 P13）
Q1 = Control Plane / Bootstrap 负责 canonical resources provisioning
Q2 = admin 单动作（read/list → member.read；create/update/delete → member.admin）
Q3 = platform_admin + tenant-scoped role + space-scoped role
Q4 = scope 不互通
Q5 = space 成员管理要求 operator 同时具备 tenant + space membership
F-P17-I-01 / I-02 / I-03 = RESOLVED（原始 observation 保留于 GAP RECORD）
```

---

## 2. Implementation scope

```text
IN（本轮交付）
  Wave 1  Tenant / Space / Membership 仓储（scope 强制 · 无通用访问器）
  Wave 2  RuntimeContextResolver（identity → tenant → space → role context）
  Wave 3  canonical authorization 集成（MembershipAuthorizer → 既有 AuthorizationService）
  Wave 4  membership 变更 + 审计（同一事务 · 授权失败零写入）
  Wave 5  API（tenant read · space read · tenant/space membership read+write）
  Wave 6  Agent scope（consume P17 context resolver · P16 语义未改动）
  +       Control Plane / Bootstrap resource provisioning capability
OUT（未实现 · 属 control plane / 未来决策）
  tenant/space create/update/delete · platform membership mutation ·
  role / permission / ACL administration · Production Event · Handler · migration · schema
```

---

## 3. Files changed（untracked · 未 commit · worktree sha256 前 16 位）

```text
services/identity_runtime/__init__.py          bd9fd7d7451061e7
services/identity_runtime/errors.py            be6ad3c798d2829b
services/identity_runtime/repository.py        9e7c26c22ff4c80f
services/identity_runtime/resolver.py          3ef1089395255a07
services/identity_runtime/membership.py        34106fd3d1d230d5
services/identity_runtime/resource_types.py    0408591694dbcc2f
services/identity_runtime/authorization.py     02130ec1387268b9
services/identity_runtime/agent_scope.py       a6c8a9cafd72dd8e

services/control_plane/__init__.py             d74acb88d7298cb1
services/control_plane/provisioning.py         25233254b7600626

services/use_cases/identity_runtime.py         f868fd0884fb7c38
services/use_cases/__init__.py                 2c3b6bd54d2c303e
apps/api/routes/identity_runtime.py            d2634db911825efb
apps/api/main.py                               ee485da235de6201
apps/api/error_mapping.py                      6824a79cfe473d63

tests/unit/test_p17_identity_runtime.py                    bcafb78f28dc97d5
tests/architecture/test_p17_boundaries.py                  24bdd589d409b380
tests/integration/test_p17_context_resolution.py           f4183b301a4d8772
tests/integration/test_p17_membership_atomicity.py         1f1df10dc4dc53d0
tests/integration/test_p17_authorization.py                8c1fbb4c7c641775
tests/integration/test_p17_api.py                          09ca3d610d8130df
tests/integration/test_p17_agent_scope.py                  e646ac65cdc35216

docs/architecture/P17_MEMBERSHIP_AUTHORIZATION_GAP_RECORD.md   eb3bef3368f17fa3
docs/architecture/P17_IMPLEMENTATION_EVIDENCE.md               014304ecf79b2262
docs/architecture/P17_IDENTITY_TENANT_SPACE_RUNTIME_IMPLEMENTATION_CONTRACT.md 53b469d189e1a5ed
docs/architecture/PLATFORM_DECISION_LOG.md                     c747657000d9f9fd（append 附录 X）
```

```text
Hash 说明：worktree（未跟踪/未提交）sha256 前 16 位，仅供本轮对照，不是 release payload hash。
Release hash 必须以 committed blob 为准（F-RP-06）。
历史 dirty 文件与既有冻结文档未被改写（附录 A–W 零改写）。
```

---

## 4. Resource projection（P17-AUTH-Q1）

```text
module  = services/control_plane/provisioning.py（capability · 非 HTTP surface）
kinds   = tenant · space · member-collection（tenant 级 / space 级）· agent
grammar = 既有 resources 契约：resource_type + tenant_id + space_id
          + natural_key 的既有部分唯一键 (tenant_id, resource_type, natural_key)
          （未发明 composite key / 未发明 resource hierarchy / 未发明 parent inheritance）
原子性  = object creation 与 projection 在同一 caller-owned transaction（§76）
幂等    = ensure_resource_projection / ensure_agent_projection（重复调用零新增）
backfill= backfill_resource_projections（显式、手动、非自动、非 runtime 请求路径）
runtime = 只消费：uap_runtime 对 tenants / spaces 无写权限 ⇒ 物理上无法 self-provision
```

实测（P17 授权测试库）：

```text
tenant 存在 → tenant resource 存在           PASS
tenant 存在 → tenant membership collection   PASS
space  存在 → space resource 存在            PASS
space  存在 → space membership collection    PASS
重复 provisioning → resources 行数不变        PASS
```

---

## 5. Canonical authorization integration（Wave 3）

```text
bridge   = services/identity_runtime/authorization.py → AuthorizationService（唯一引擎）
mapping  = read/list → member.read ；create/update/delete → member.admin
resource = canonical membership collection（tenant 级 / space 级 · 缺失即 DENY）
subject  = 已认证 actor + 其 membership-derived roles（既有 SubjectResolver）
no role-name check · no is_admin · no platform_admin fallback · no 新 authorization engine
```

授权门形态（use case 内 · 单一实现 `_authorize_membership`）：

```text
1) P17 context resolution（tenant membership；space 操作另需 space membership）
2) canonical ALLOW required
3) 若无 membership context：仅当同一 canonical engine 在「移除 tenant/space context」的问法下仍
   ALLOW（= 显式平台 scope 授权，或已 provisioning 的 ACL）才放行；否则回带原 context 拒绝码
```

---

## 6. Context resolution（Wave 2 · 不变）

```text
tests/integration/test_p17_context_resolution.py = 11 passed / 0 failed
固定顺序 actor → tenant membership → tenant 可读 → (space 属 tenant) → space membership → role context
输出 ResolvedContext（context ≠ authorization ALLOW）
```

---

## 7. Membership mutation + audit（Wave 4）

```text
tests/integration/test_p17_membership_atomicity.py = 5 passed / 0 failed
create/update/delete → membership 行 + audit 行（独立连接验证）
delete → audit 保留 role_before（不依赖已删除行）
audit 失败 ⇒ membership 变更回滚（独立连接确认无残留）
授权失败（跨租户 / 跨空间 / 缺 membership / 角色 scope 不符 / 资源缺失）⇒ 零写入
写前服务端校验：user 存在 · tenant 存在 · role 可分配 · role scope 与 membership scope 一致 ·
  role.tenant_id/space_id 与目标一致 · space 属目标 tenant · target user 已属 target tenant ·
  rowcount = 1
```

---

## 8. API（Wave 5）

```text
router = apps/api/routes/identity_runtime.py（transport only · 已注册于 apps/api/main.py）
GET    /tenants · /tenants/{id} · /tenants/{id}/spaces
GET    /tenants/{id}/members · POST · PATCH /{user_id} · DELETE /{user_id}
GET    /tenants/{id}/spaces/{sid}/members · POST · PATCH /{user_id} · DELETE /{user_id}
target 一律来自 path（无 X-Current-Tenant / X-Current-Space）
handler 无 SQL · 无角色名比较 · 无 is_admin；仅 authenticate_actor → use case → error mapping
错误映射：授权族（含资源未 provisioning）→ 403；duplicate → 409；其余校验 → 422/404
跨租户拒绝不泄露 foreign tenant/space/member 细节（API 测试断言响应体不含）
```

---

## 9. Agent integration（Wave 6）

```text
module = services/identity_runtime/agent_scope.py（consume P17 context resolver）
agent tenant = agents.tenant_id（tenant-scoped 查询 · 无 id-only lookup）
agent space  = agents.space_id；非空时 runtime space 必须完全相同
owner = context only（非授权来源）
P16 runtime 未修改（services/agent/* · apps/api/routes/agent_runs.py 零改动）
```

---

## 10. Test results（真实数据库 · uap_runtime 身份 · 显式 allowlist）

```text
P17 单元（test_p17_identity_runtime.py）                 18 passed / 0 failed
P17 边界守卫（test_p17_boundaries.py）                   11 passed / 0 failed
P17 上下文集成（test_p17_context_resolution.py）          11 passed / 0 failed
P17 原子性集成（test_p17_membership_atomicity.py）         5 passed / 0 failed
P17 授权集成（test_p17_authorization.py）                 19 passed / 0 failed
P17 API 集成（test_p17_api.py）                           10 passed / 0 failed
P17 Agent 集成（test_p17_agent_scope.py）                  7 passed / 0 failed
---------------------------------------------------------------
P17 allowlist 合计                                        81 passed / 0 failed

P16 单元 + 架构 + 安全                                     33 passed / 0 failed
P16 集成（6 scenarios + R-1 durability）                    8 passed / 0 failed
P15 显式 allowlist                                         65 passed / 0 failed
架构守卫（tests/architecture）                              57 passed / 0 failed
forbidden tests（tests/unit/test_generate_build_info.py）     执行次数 = 0
Core → Domain                                              0
```

矩阵覆盖：PASS-1…PASS-5 · N1…N17（N14–N17 以 runtime 对 registry 的写尝试被数据库拒绝实现）·
resource absence fail-closed · provisioning→ALLOW · provisioning 幂等 · projection consistency ·
API 正/负路径 · secret/泄露断言。

测试库（均为一次性 · 运行后 DROP）：`uap_p17_test` · `uap_p17_atomic_test` · `uap_p17_auth_test` ·
`uap_p17_api_test` · `uap_p17_agent_test`。fixture 仅使用官方 `scripts.privileges.materialize()`，
无私有 GRANT。

---

## 11. Security findings

```text
F-P17-I-01 / I-02 / I-03        RESOLVED（OPTION A · 见 GAP RECORD §0 与 PDL 附录 X）
authorization bypass            0（无第二套引擎；无 fallback；无 handler 侧放行）
cross-tenant bypass             0（N1/N3/N6/N12 · 探针与集成双重证据）
cross-space bypass              0（N2/N5/N7/N13）
visibility bypass               0（N11：link/tenant 均不构成授权）
owner→agent permission inherit  0（P17 agent scope + canonical agent 独立性）
resource absent                  DENY（fail closed · 正式测试保留）
secret leakage                  0（evidence 不含 DSN / 口令 / token）
unexpected privilege expansion  0
```

已记录的既有语义（非缺陷 · 非新增继承）：

```text
core.permission.scope.scope_covers 冻结语义中，TENANT scope 的 grant 覆盖该 tenant 内资源（含其 space 资源）。
因此「tenant+space 双成员资格 + tenant 角色含 member.admin」的 operator 可以管理该 tenant 内该 space 的成员——
与 Q5 双成员资格要求一致，且不违反 Q4（跨租户仍 DENY；缺 space membership 仍 DENY）。
已在 Implementation Contract §12 与 PDL 附录 X 记录。
```

---

## 12. Privilege / schema / DB verification

```text
uap_runtime role_table_grants = 56（P17 前后一致 · delta = 0）
uap_app = 5 · uap_migrator = 245 · uap* roles = 6
permissions = 12（未新增 · P13 未改写）
migration = NONE · schema = UNCHANGED · 新表 = 0
正式库 uap = public 表 0（prestate == poststate）
冻结基线库 uap_b1_test = tenants 0 · spaces 0 · roles 1 · resources 0 · permissions 12（未改动）
一次性测试库全部 DROP，环境无残留
```

---

## 13. Git

```text
HEAD = 42a4f61c20fe119af77ab822e24c8028ce653e3d（= origin/main · 未变动）
tags = 14（UAP-V0.1.15-P16-AGENT-RUNTIME 未改动）
staged = 0
历史 dirty 文件原样保留（未 clean / 未 reset / 未 restore / 未 add .）
commit / tag / push = NO
```

---

## 14. Status

```text
P17 IMPLEMENTATION = PASS（Wave 0–6 + 测试 + evidence 完成）
P17 ACCEPTANCE     = NOT YET EXECUTED（需独立 Gate）
P17 RELEASE        = NOT AUTHORIZED（需独立 Release Preparation → Release Integrity Gate）
Production Event Allowlist = EMPTY · Production Handlers = 0
P18                = NOT STARTED
HARD STOP          = ACTIVE
```

**END OF P17 IMPLEMENTATION EVIDENCE（Wave 3–6 完成 · OPTION A 授权模型 · 81/0 P17 · 33/0 P16 · 8/0 P16 集成 · 65/0 P15 · 57/0 guards · 未 commit / tag / push；2026-10-01）**
