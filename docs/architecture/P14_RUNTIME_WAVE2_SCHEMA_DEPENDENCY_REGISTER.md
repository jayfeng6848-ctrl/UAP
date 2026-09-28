# UAP — P14 RUNTIME WAVE 2 SCHEMA DEPENDENCY REGISTER

> ## 状态
>
> ```text
> 状态      = **EMPTY / OPEN**
> 含义      = 目前 **NO NEW SCHEMA OBJECT REQUIRED**（尚未发现必须新增的 schema 对象）
>             · OPEN = 随 Wave 2 决策推进可追加登记（本文件为活体登记册）
> 依据      = RTA-10 = OPTION B（不得隐式创建任何 schema support object）·
>             Wave 1 FINAL ACCEPTANCE §18（Schema Boundary）
> 铁律      = 不得以 0018 / ad-hoc DDL / startup DDL / test-only hidden schema 绕过
> ```

---

# 1. 登记册（当前为空）

```text
┌──────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ 序号  │ required obj │ why required │ consumer     │ affected acc │ 状态          │
├──────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ —    │ （无）        │ —            │ —            │ —            │ —            │
└──────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘

⇒ NO NEW SCHEMA OBJECT REQUIRED（本条为**结论**而非省略）
⇒ 不得为此创建空 migration
```

---

# 2. 判定依据（为何当前判定为空）

```text
Identity / Device / Session 所需的存储面**已全部存在于 migration 0017**：

  users(id,email,username,display_name,status,primary_identity_id,last_login_at,
        locked_until,failed_attempts,created_at,updated_at,deleted_at)
        ck_users_login(email OR username) · ck_users_status(pending|active|suspended|locked|deleted)
  identities(id,user_id,provider,issuer,subject,email,display_name,status,verified_at,
             last_used_at,revoked_at,created_at,updated_at)
        ck_identities_provider(local|oidc|saml|device|service)
        ck_identities_status(active|unverified|suspended|revoked)
  credentials(id,identity_id,user_id,type,secret_hash,algorithm,secret_hint,expires_at,
              last_used_at,rotated_at,revoked_at,failed_attempts,locked_until,created_at,updated_at)
        ck_credentials_type(password|api_key|recovery_code|device_cert|otp)
        ck_credentials_algorithm(argon2id|scrypt|sha256_hmac) · ck_credentials_secret(secret_hash <> '')
  devices(id,user_id,fingerprint,label,platform,app_version,public_key,status,
          first_seen_at,last_seen_at,ip_last,revoked_at,revoked_reason,created_at,updated_at)
        ck_devices_status(pending|active|untrusted|revoked|lost)
  sessions(id,user_id,identity_id,device_id,token_hash,refresh_token_hash,status,ip_created,
           ip_last,user_agent,expires_at,absolute_expires_at,last_used_at,revoked_at,
           revoked_reason,replaced_by,created_at,updated_at)
        ck_sessions_status(active|expired|revoked) · ck_sessions_expiry(expires_at > created_at)

⇒ 三个候选核心节点的字段、枚举、外键、唯一性载体**均已具备**。
```

---

# 3. VERIFICATION 结果（原 5 项 PENDING → **已 live 复核完成**）

```text
说明：本轮开工时 PostgreSQL（127.0.0.1:5432）一度不可达（connection refused），
      复核延后；服务恢复后已按**只读 catalog 查询**完成全部 5 项，结果如下。
      复核未产生任何 DDL / DML / grant。
```

| # | 复核项 | 实测结果（只读 catalog） | 对应 Decision |
|---|---|---|---|
| VP-1 | `devices` 唯一性与状态约束 | `uq_devices_fingerprint` = **UNIQUE (user_id, fingerprint)**；`ck_devices_status` = (pending, active, untrusted, revoked, lost)；`fk_devices_user ON DELETE CASCADE`；`ix_devices_user_status` | DV-W2-02 / VOC-W2-03 |
| VP-2 | `memberships` / `tenant_memberships` 状态枚举 | 两者均为 `(invited, active, suspended, removed)` —— **与 core `MEMBERSHIP_STATUS` 完全一致** | CTX-W2-02 |
| VP-3 | `sessions` 可空性与唯一性 | `user_id NOT NULL` · `identity_id NOT NULL` · **`device_id` 可空**；FK：device CASCADE / identity RESTRICT / user CASCADE；`ck_sessions_status(active,expired,revoked)` · `ck_sessions_expiry(expires_at > created_at)`；**无 (device_id) 唯一约束** | SS-W2-01 / SS-W2-02 / SS-W2-04 |
| VP-4 | `users` 的 email / username 唯一性 | `uq_users_email` = **UNIQUE (lower(email)) WHERE deleted_at IS NULL**；`uq_users_username` = **UNIQUE (lower(username)) WHERE deleted_at IS NULL**；`ck_users_login(email OR username)`；`ck_users_status(pending,active,suspended,locked,deleted)` | ID-W2-03 / VOC-W2-04 |
| VP-5 | `resources` / `role_permissions` 约束 | `resources`：classification/status/type CHECK + FK(owner SET NULL · space RESTRICT · tenant RESTRICT)；`role_permissions`：**`ck_role_permissions_effect` = (allow, deny)** · PK (role_id, permission_id, effect) | 既有授权判定输入 · **新增分歧 D-9** |

```text
关键结论（影响 Human Decision 的事实，非建议）
  · VP-1：DB 的 fingerprint 唯一性是 **per-user**（同一用户内唯一），
          **未禁止跨用户复用同一 fingerprint**；device 归属列为 `user_id`（非 identity_id）
  · VP-3：`device_id` 在 DB 层**可空** ⇒ "session 必须绑定已验证设备"是**应用层约束**，
          无法由既有 schema 表达；且无唯一约束 ⇒ 并发策略只能由应用层保证
  · VP-4：email / username 唯一性**已存在**且为 (i) 全局（无 tenant 维度）
          (ii) 大小写不敏感（lower）(iii) 软删除后释放（partial index）
          ⇒ 任何 tenant-scoped 唯一性方案都会与既有 DB 行为**冲突**（需 Human 裁决）
  · VP-5：`role_permissions.effect` 仅 (allow, deny)，无法表达
          `core.permission.EFFECTS` 中的 `REQUIRES_APPROVAL` ⇒ **新增分歧 D-9**

⇒ 5 项复核**均未发现**需要新增 schema 对象的情形，§1 的
  `NO NEW SCHEMA OBJECT REQUIRED` 结论**保持成立**。
⇒ 但复核**新增**了 1 项词表分歧（D-9），已并入 WAVE2_SCOPE §5。
```

---

# 4. 触发规则（Wave 2 全程有效）

```text
若在实现期发现现有 schema 不足以表达某功能：
  1. 立即停止该方向实现（STOP AT SCHEMA BOUNDARY）
  2. 在本文件 §1 追加一行：required object / why required / consumer /
     affected acceptance / why existing object insufficient
  3. 建立独立 Schema Decision 请求 Human 裁决

明令禁止（RTA-10）
  0018 migration · ad-hoc DDL · startup DDL · test fixture 内隐藏对象 ·
  CREATE TABLE / FUNCTION / VIEW / TRIGGER / INDEX / SEQUENCE / TYPE / SCHEMA
```

---

# 5. 本轮工程变更

```text
新增文档 = 本文件（+ 同轮 8 份）
DDL = 0 · migration = 0 · 未创建任何 schema 对象 · commit / tag / push = 0
```

**END OF P14 RUNTIME WAVE 2 SCHEMA DEPENDENCY REGISTER（2026-09-28 · EMPTY / OPEN · NO NEW SCHEMA OBJECT REQUIRED · 5 项 VERIFICATION PENDING · HARD STOP ACTIVE）**

---

# 6. Decision Freeze 后的状态确认（2026-09-28）

```text
PDL 附录 P 已裁决：`New schema object required for Wave 2 = **NO**`（§三十五）。

登记册状态
  §1 登记项 = **EMPTY**（无 required object）
  §1 结论   = **NO NEW SCHEMA OBJECT REQUIRED**（保持成立）
  §3 复核   = 5 项 VERIFICATION PENDING **已全部完成**（live 只读 catalog；未产生 DDL）
  §4 触发规则 = 继续有效（实现期若发现不足 ⇒ SCHEMA DEPENDENCY → STOP AT SCHEMA BOUNDARY）

保留的条件式路径（非未决项）
  DV-W2-03（challenge）与 ID-W2-03（唯一性）在仲裁中均采用"既有 schema 优先"；
  若实现期证明必须新增对象，则按 §4 走独立 Schema Decision（RTA-10 = OPTION B）。
  该路径为**条件式**，不构成 Wave 2 的未决 schema dependency。

⇒ Schema dependency unresolved = **0**
```

**END OF SCHEMA DEPENDENCY REGISTER §6（2026-09-28 · EMPTY / CONFIRMED · NO NEW SCHEMA OBJECT REQUIRED · HARD STOP ACTIVE）**
