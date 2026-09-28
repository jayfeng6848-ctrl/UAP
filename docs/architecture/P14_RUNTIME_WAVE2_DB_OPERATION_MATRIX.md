# UAP — P14 RUNTIME WAVE 2 DB OPERATION MATRIX

> ## 状态
>
> ```text
> 状态      = **IMPLEMENTATION INPUT**（实现输入 · 未实施 · 未授权）
> 依据      = P14_SECURITY_IMPLEMENTATION_GRANT_MATRIX.md（REQUIRED 面）·
>             P14_SECURITY_IMPLEMENTATION_REPORT.md §6/§12（精确行授权 51 + 6）·
>             Wave 1 FINAL ACCEPTANCE §12（活体 51 指纹独立复核）
> 身份      = 全部操作以 **uap_runtime** 执行（RUNTIME-G-01）
> 铁律      = 任何操作若需要**未列入**既有授权的 verb/object
>             ⇒ 登记 `SECURITY GRANT GAP` → **STOP** → 独立 Security Decision
>             （**不得**自动 GRANT；SEC-14 = EXACT LEAST-PRIVILEGE GRANT）
> ```

---

# 1. 已冻结的 runtime 授权面（本 Matrix 的可用集合 · 只读引用）

```text
对象             runtime 可用 verb        来源
----------------------------------------------------------------------------------------
users            SELECT · INSERT · UPDATE  SEC-P14（GRANT_MATRIX §1/§2）
identities       SELECT · INSERT · UPDATE
credentials      SELECT · INSERT · UPDATE  （**无 DELETE** · SEC-08）
devices          SELECT · INSERT · UPDATE
sessions         SELECT · INSERT · UPDATE · **DELETE**
audit_logs       SELECT · INSERT           （无 UPDATE/DELETE · 不可变）
events           SELECT · INSERT · UPDATE  （无 DELETE · SEC-07）
resources        SELECT · INSERT · UPDATE  （无 DELETE · SEC-07）
memberships      SELECT · INSERT · UPDATE · DELETE
tenant_memberships SELECT · INSERT · UPDATE · DELETE
tenants          SELECT only               （SEC-05）
spaces           SELECT only               （SEC-05）
roles · permissions · role_permissions · acl_subject_types   SELECT only
platform_state · platform_memberships                        SELECT only（SEC-13）
agents · agent_versions · agent_permissions · tools          SELECT only
alembic_version                                              SELECT only
function EXECUTE（public）                                    0（SEC-14）
schema public CREATE                                          false（D-OP101-08）
pg_default_acl                                                0
```

---

# 2. Identity 面操作

| # | 归属 | Object | Operation | Use-case | Security Boundary | Existing Grant | Test（设计） |
|---|---|---|---|---|---|---|---|
| I-1 | Identity | `users` | SELECT | 读取主体（登录/校验） | Runtime execution | ✅ S | 有权限读 · 无跨租户读 |
| I-2 | Identity | `users` | INSERT | 建立首个可登录主体 | Runtime execution | ✅ I | 重复创建被拒（SEC-W2-01） |
| I-3 | Identity | `users` | UPDATE | status 状态机推进 | Runtime execution | ✅ U | 非法转移被拒 |
| I-4 | Identity | `identities` | SELECT | 身份解析 | Runtime execution | ✅ S | — |
| I-5 | Identity | `identities` | INSERT | 建立身份记录 | Runtime execution | ✅ I | 无身份创建权时被拒（ID-W2-01） |
| I-6 | Identity | `identities` | UPDATE | verification / status 推进 | Runtime execution | ✅ U | 非法转移被拒 |
| I-7 | Identity | `credentials` | SELECT | 校验凭据（读 hash） | Runtime execution | ✅ S | hash 不出现在日志/响应 |
| I-8 | Identity | `credentials` | INSERT | 建立凭据（Argon2id） | Runtime execution | ✅ I | 明文不落库 |
| I-9 | Identity | `credentials` | UPDATE | rotate / revoke / expire | Runtime execution | ✅ U | 撤销后不可用（SEC-W2-05） |
| I-10 | Identity | `credentials` | **DELETE** | 物理删除凭据 | — | ❌ **NOT REQUIRED（SEC-08）** | 必须 **DENIED**（负向） |
| I-11 | Identity | `audit_logs` | INSERT | 记录身份事件（若 AUTH-W2-03=A） | Runtime execution | ✅ I | payload 无 secret |

```text
⇒ Identity 面**无需任何新授权**（全部命中既有 51 授权面）
```

---

# 3. Device 面操作

| # | 归属 | Object | Operation | Use-case | Security Boundary | Existing Grant | Test（设计） |
|---|---|---|---|---|---|---|---|
| D-1 | Device | `devices` | SELECT | 读取设备绑定 | Runtime execution | ✅ S | — |
| D-2 | Device | `devices` | INSERT | enrollment（challenge 通过后） | Runtime execution | ✅ I | 错误用户/复用设备被拒（SEC-W2-02） |
| D-3 | Device | `devices` | UPDATE | revoke（置 status/revoked_at） | Runtime execution | ✅ U | revoke 后不可认证 |
| D-4 | Device | `devices` | **DELETE** | 物理删除设备 | — | ❌ **NOT REQUIRED** | 必须 **DENIED**（负向） |
| D-5 | Device | `sessions` | UPDATE / DELETE | device revoke 连带撤销 active sessions（DV-W2-04 若选 A/B） | Runtime execution | ✅ U / D | 原子性：同事务内完成 |
| D-6 | Device（challenge） | `credentials` | INSERT/UPDATE/SELECT | challenge 载体（DV-W2-03 若选 A） | Runtime execution | ✅ I/U/S | 过期/重放被拒 |
| D-7 | Device（challenge） | —（无持久化） | — | DV-W2-03 若选 B（签名令牌） | Runtime execution | — | 不落库 · 无残留 |

```text
⇒ Device 面**无需任何新授权**（含 challenge 两种候选均落在既有面内）
```

---

# 4. Session 面操作

| # | 归属 | Object | Operation | Use-case | Security Boundary | Existing Grant | Test（设计） |
|---|---|---|---|---|---|---|---|
| S-1 | Session | `sessions` | INSERT | 建立会话（activation） | Runtime execution | ✅ I | 未验证身份/设备时被拒（SS-W2-01） |
| S-2 | Session | `sessions` | SELECT | 会话校验（每次请求） | Runtime execution | ✅ S | 过期/撤销会话被拒 |
| S-3 | Session | `sessions` | UPDATE | 状态推进 / 失效 / 替换 | Runtime execution | ✅ U | 并发策略符合 SS-W2-04 |
| S-4 | Session | `sessions` | DELETE | 物理清理失效会话 | Runtime execution | ✅ **D**（唯一含 D 的身份类对象） | 清理不影响其他会话 |
| S-5 | Session | `users` / `identities` | SELECT | 绑定校验 | Runtime execution | ✅ S | 错绑被拒（SEC-W2-03） |
| S-6 | Session | `audit_logs` | INSERT | 会话事件（若 AUTH-W2-03=A） | Runtime execution | ✅ I | 无 secret |

```text
⇒ Session 面**无需任何新授权**
```

---

# 5. Context / Authorization 面只读操作

| # | 归属 | Object | Operation | Use-case | Existing Grant | Test（设计） |
|---|---|---|---|---|---|---|
| C-1 | Context | `tenants` | SELECT | tenant 上下文解析 | ✅ S | 跨租户 DENY（SEC-W2-03） |
| C-2 | Context | `spaces` | SELECT | space 上下文解析 | ✅ S | 跨空间 DENY |
| C-3 | Context | `memberships` | SELECT | 成员关系判定 | ✅ S | inactive membership DENY |
| C-4 | Context | `tenant_memberships` | SELECT | tenant 级成员判定 | ✅ S | 同上 |
| C-5 | Authorization | `roles` | SELECT | RBAC 判定输入 | ✅ S | default deny |
| C-6 | Authorization | `permissions` | SELECT | 权限词表读取 | ✅ S | deny precedence |
| C-7 | Authorization | `role_permissions` | SELECT | 绑定读取 | ✅ S | — |
| C-8 | Authorization | `acl_subject_types` | SELECT | subject_type 解析 | ✅ S | 不得写（C2/CC-7） |
| C-9 | Authorization | `resource_permissions` | SELECT | ACL 判定 | ✅ S | 写必须 DENIED（SEC-09） |
| C-10 | Authorization | `platform_state` | SELECT | 状态读取 | ✅ S | 写必须 DENIED（SEC-13） |
| C-11 | Authorization | `platform_memberships` | SELECT | 平台成员读取 | ✅ S | 写必须 DENIED（SEC-13） |
| C-12 | Authorization | `agents` / `agent_versions` / `agent_permissions` / `tools` | SELECT | agent/tool subject 解析 | ✅ S | — |
| C-13 | Health | `alembic_version` | SELECT | readiness 探针 | ✅ S | 不得写 |

```text
⇒ 全部为既有只读授权；**无需新授权**
```

---

# 6. Outbox / 资源面（仅当 Human 裁定的 use-case 需要）

| # | 归属 | Object | Operation | Use-case | Existing Grant | Test（设计） |
|---|---|---|---|---|---|---|
| E-1 | Identity/Session | `events` | INSERT / UPDATE | outbox 写入与推进 | ✅ I / U | 无 DELETE（SEC-07） |
| E-2 | use-case | `resources` | INSERT / UPDATE | 资源建立/更新 | ✅ I / U | 无 DELETE（SEC-07） |
| E-3 | use-case | `memberships` / `tenant_memberships` | I / U / D | 受控成员关系用例 | ✅ I/U/D | 跨租户 DENY |

```text
⚠ E-1…E-3 仅在 Human 明确 Wave 2 含对应 use-case 时启用；本 Matrix 不预设启用。
```

---

# 7. Gap 判定与 Escalation

```text
结论（本轮分析）：Wave 2 的 Identity / Device / Session 主链操作
                  **全部命中已冻结的 51 授权面**，未发现 SECURITY GRANT GAP。

但不构成对未来的承诺：
  · 若 Human 选择的选项要求**新 verb**（如 devices DELETE、identities DELETE）
    ⇒ `SECURITY GRANT GAP` → STOP → 独立 Security Decision
  · 若 Human 选择的选项要求**新对象**（如 challenge 表）
    ⇒ `SCHEMA DEPENDENCY` → STOP → 独立 Schema Decision
  · 若某操作在实现中被 PostgreSQL 以 42501 拒绝
    ⇒ 不得自动 GRANT；先判定"实现错误 vs Matrix 缺口"（§二十六 语义沿用）

live 复核已完成（2026-09-28 · 只读 catalog · 见 Schema Register §3）：
  · devices：`uq_devices_fingerprint = UNIQUE(user_id, fingerprint)` · 5 态 CHECK
    ⇒ 影响 DV-W2-02（跨用户复用 fingerprint **未被** DB 禁止）
  · memberships / tenant_memberships：status = (invited, active, suspended, removed)
    ⇒ 与 Domain 一致 · 影响 CTX-W2-02（无分歧）
  · sessions：`device_id` **可空** 且无唯一约束
    ⇒ 影响 SS-W2-01（应用层强制设备绑定）与 SS-W2-04（应用层保证并发策略）
  · users：UNIQUE(lower(email)) / UNIQUE(lower(username)) WHERE deleted_at IS NULL
    ⇒ 影响 ID-W2-03（全局 + 大小写不敏感 + 软删除释放）
  · role_permissions.effect ∈ (allow, deny) ⇒ 既有分歧 D-9（见 AUTH-W2-01）

⇒ 复核**未发现**需要新增 verb 或对象的情形：本 Matrix 的
  "未发现 SECURITY GRANT GAP" 结论保持成立
```

---

# 8. 本轮工程变更

```text
新增文档 = 本文件（+ 同轮 8 份）
GRANT / REVOKE / ALTER ROLE / CREATE ROLE = 0 · DDL / DML = 0 · migration = 0
commit / tag / push = 0
```

**END OF P14 RUNTIME WAVE 2 DB OPERATION MATRIX（2026-09-28 · IMPLEMENTATION INPUT · 未发现 GRANT GAP · 未扩权 · HARD STOP ACTIVE）**
