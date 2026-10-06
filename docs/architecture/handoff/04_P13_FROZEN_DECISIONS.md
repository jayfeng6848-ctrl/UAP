# 04_P13_FROZEN_DECISIONS — P13 冻结决策（逐字 · 不得重新解释）

> 权威 = `docs/architecture/PLATFORM_DECISION_LOG.md`（sha256[:16] `a83fde5c57605252`）；下表为 PDL 决策表逐字摘录（FROZEN）。

| ID | 冻结内容（逐字摘录） |
|---|---|
| `D-P13-01` | permissions canonical seed list = **12 项**（取代 13 项草稿）· `manage→admin` · `write→update` · 排除 `system.*` · **无 deny 行** |
| `D-P13-02` | System role ownership（`platform_admin` 归 0005，P13 仅校验存在；tenant/space 四角色因无 bootstrap tenant ⇒ P13 **零播种**） |
| `D-P13-03` | `acl_subject_types` seed 走 **migration-controlled path**；runtime INSERT = FORBIDDEN；C2 保持 |
| `D-P13-04` | **仅注册** `agent` subject type；不得创建 agents / agent_versions / agent_permissions / tool_executions —— **Option A** |
| `D-P13-05` | **不创建 bootstrap tenant**（`tenants = 0`）；不得虚构 slug / name / owner / administrator identity —— **Option B** |
| `D-P13-06` | identity row = allowed；plaintext password / credential secret = forbidden（可登录性由 onboarding 提供） |
| `D-P13-07` | P13 = **0** `platform_memberships`；首个平台管理员只经既有 bootstrap CLI / 状态机 —— **Option A（no platform_memberships）** |
| `D-P13-08` | **不创建** `tenant_memberships` / `memberships` —— **Option B（no tenant memberships）** |
| `D-P13-09` | seed 顺序 = SEED_STRATEGY §1 十步序为**唯一拓扑**（step 4 / 6 / 9 因本轮决策为空操作） |
| `D-P13-10` | 幂等 = 既有 precedent（`WHERE NOT EXISTS` / 冲突即**显式失败**）；**禁**统一 `ON CONFLICT DO NOTHING` |
| `D-P13-11` | seed 在 **39 triggers 全部启用**下执行；**禁** DISABLE / DROP / ALTER TRIGGER 与绕过 C2 |
| `D-P13-12` | 降级 = **FAIL-CLOSED**；**禁** `DELETE WHERE key IN (...)`；**禁**新增 ownership marker 列 —— **Option C** |
| `D-P13-13` | credentials = 0 · plaintext secrets = 0 · fabricated passwords = 0 |
| `D-P13-14` | runtime 数据保护 = natural-key filtering + FK protection + `D-P13-12` fail-closed + pre-downgrade 验证；**不新增** schema marker |

## D-P13-01 的 12 个 permission seeds（canonical · 逐字）

```text
tenant.read      tenant.admin      space.read      space.admin
member.read      member.admin      resource.read   resource.update
resource.delete  agent.execute     tool.execute    audit.read
```

## D-P13-15（B-1 Amendment · Trust Boundary Precondition）

```text
Purpose（语义）= 允许未来受信 migration context 建立 system registry seed，
                 前提是数据库身份隔离已经成立。
Does NOT authorize = migration（0016）· C2 change · implementation
```

即：`D-P13-15` 只是方向冻结；**0016 的创建与执行、C2/CC-7 改写、实施本身均须各自独立授权**（该授权已通过 `OPEN_P10_1_BATCH_C_DECISION_RECORD.md` 部分落地为 BATCH-C 范围，见 05/06）。

## P13 执行顺序（冻结）

```text
OPEN-P10-1 → P13 B-1 Amendment（已完成 = D-P13-15）→ P13 Implementation（0017_p13_seed）
```

**P13 Implementation = NOT STARTED**（0017 ABSENT）。
