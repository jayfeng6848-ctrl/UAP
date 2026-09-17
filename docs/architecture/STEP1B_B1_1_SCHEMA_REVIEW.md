# STEP 1-B / B1-1 — Schema Review（5 张 Identity 表逐字段核对）

Status: **FROZEN-DESIGN CROSS-CHECK — 以冻结设计为准**
来源（优先级顺序）：
1. `CORE_DOMAIN_MODEL.md` §1.1（主）
2. `ER_MODEL.md` §1（关系）
3. `STEP1B_CONSTRAINT_MATRIX.md` §1（B0 已批准：NOT NULL/NULL 判定、CK/UQ 落地）
4. `STEP1B_INDEX_STRATEGY.md` §1/§3（索引与 FK 反查）
5. `STEP1B_TRIGGER_INVENTORY.md` §1（trigger）
6. `STEP1B_UUID_STRATEGY.md`（DEFAULT 兜底）

> 核对结论：冻结设计字段级明确；NULL/NOT NULL 粒度以已批准 B0 CONSTRAINT_MATRIX 为准（CORE_DOMAIN_MODEL 未逐列标注，例：`email_verified_at` 语义必空但未写 NULL → 未标 ≠ NN 的证明）。

---

## 0. 全局约定落实

| 项 | 决定 |
|---|---|
| ID | `uuid PK DEFAULT uap_uuid_v7()`（B1-0 已建函数，**不重建、不修改**） |
| citext | **不用**：`email`/`username` 用 `text` + `lower()` 表达式唯一索引（零依赖，冻结文档明确推荐） |
| created_at / updated_at | `timestamptz NOT NULL DEFAULT now()`；updated_at 由 trigger 维护 |
| 状态/枚举 | `text` + CHECK（非 PG enum） |
| primary_identity_id | **普通 uuid 列，不建 FK**（冻结 FK/ER 未定义该边；避免 users↔identities 循环。语义由应用层维护） |
| 敏感列 | 仅 `secret_hash` / `token_hash` / `refresh_token_hash`（哈希），**无明文列** |

---

## 1. `users`（平台级身份根，tenant-independent）

| column | type | nullable | default | notes |
|---|---|---|---|---|
| id | uuid | NN | `uap_uuid_v7()` | PK |
| email | text | Y | NULL | `lower(email)` 部分唯一（deleted_at IS NULL） |
| email_verified_at | timestamptz | Y | NULL | 语义必空，未标 NULL → 由 B0 Matrix 定为 NULL |
| username | text | Y | NULL | `lower(username)` 部分唯一（同上） |
| display_name | text | Y | NULL | B0 Matrix：NULL |
| status | text | NN | — | CK `('pending','active','suspended','locked','deleted')` |
| primary_identity_id | uuid | Y | NULL | **无 FK**（见 §0） |
| last_login_at | timestamptz | Y | NULL | |
| locked_until | timestamptz | Y | NULL | |
| failed_attempts | int | NN | 0 | 不加额外 CHECK（B0 标注"建议"，本轮不实施 → PROPOSED） |
| created_at / updated_at / deleted_at | timestamptz | NN/NN/Y | now() | deleted_at 软删 |

- CK：`status IN (...)`；`email IS NOT NULL OR username IS NOT NULL`
- UQ（部分）：`uq_users_email ON (lower(email)) WHERE deleted_at IS NULL`；`uq_users_username ON (lower(username)) WHERE deleted_at IS NULL`
- 无 FK（root）

## 2. `identities`

| column | type | nullable | notes |
|---|---|---|---|
| id | uuid | NN | PK |
| user_id | uuid | NN | FK → users.id **ON DELETE CASCADE** |
| provider | text | NN | CK `('local','oidc','saml','device','service')` |
| issuer | text | Y | NULL |
| subject | text | NN | |
| email / display_name | text | Y | NULL |
| status | text | NN | CK `('active','unverified','suspended','revoked')` |
| verified_at / last_used_at / revoked_at | timestamptz | Y | NULL |
| created_at / updated_at | timestamptz | NN | |

- UQ：`uq_identities_ref ON (provider, COALESCE(issuer,''), subject)`；`uq_identities_email ON (provider, lower(email)) WHERE email IS NOT NULL AND revoked_at IS NULL`（部分）
- **同一 provider+issuer+subject 只能被一个 user 占用**（UQ 强制）
- 注意：`device` provider 是身份源类型枚举值，**不是**把 device_id 当 identity owner；本表不出现 device_id/session_id/tenant_id/space_id 列

## 3. `credentials`

| column | type | nullable | notes |
|---|---|---|---|
| id | uuid | NN | PK |
| identity_id | uuid | NN | FK → identities.id **ON DELETE CASCADE** |
| user_id | uuid | NN | FK → users.id **ON DELETE CASCADE**（冗余，便于按用户检索） |
| type | text | NN | CK `('password','api_key','recovery_code','device_cert','otp')` |
| secret_hash | text | NN | **CK `secret_hash <> ''`；永不存明文** |
| algorithm | text | NN | CK `('argon2id','scrypt','sha256_hmac')` |
| secret_hint | text | Y | NULL |
| expires_at / last_used_at / rotated_at / revoked_at / locked_until | timestamptz | Y | NULL |
| failed_attempts | int | NN | 0 |
| created_at / updated_at | timestamptz | NN | |

- UQ（部分）：`uq_credentials_active_password ON (identity_id) WHERE type='password' AND revoked_at IS NULL` —— 每种 type 同时仅 1 份有效
- **禁止列**（B1-1 schema 不出现，security test 断言）：`plaintext_secret` / `plaintext_password` / `api_key` / `token` 等含明文字段名

## 4. `devices`

| column | type | nullable | notes |
|---|---|---|---|
| id | uuid | NN | PK |
| user_id | uuid | NN | FK → users.id **ON DELETE CASCADE** |
| fingerprint | text | NN | |
| label | text | Y | NULL |
| platform / app_version / public_key | text | Y | NULL |
| status | text | NN | CK `('pending','active','untrusted','revoked','lost')` |
| first_seen_at / last_seen_at | timestamptz | Y | NULL |
| ip_last | inet | Y | NULL |
| revoked_at / revoked_reason | timestamptz/text | Y | NULL |
| created_at / updated_at | timestamptz | NN | |

- UQ：`uq_devices_fingerprint ON (user_id, fingerprint)`
- 无 identity FK（device 与 identity 独立；关系语义：device 属于 user，不反向拥有 identity）

## 5. `sessions`

| column | type | nullable | notes |
|---|---|---|---|
| id | uuid | NN | PK |
| user_id | uuid | NN | FK → users.id **ON DELETE CASCADE** |
| identity_id | uuid | NN | FK → identities.id **ON DELETE RESTRICT**（有会话时 identity 不可删） |
| device_id | uuid | Y | NULL；FK → devices.id **ON DELETE CASCADE**（NULL = 非设备会话） |
| token_hash | text | NN | **UQ `uq_sessions_token`**；仅哈希 |
| refresh_token_hash | text | Y | UQ（部分）`WHERE refresh_token_hash IS NOT NULL` |
| status | text | NN | CK `('active','expired','revoked')` |
| ip_created | inet | Y | NULL（B0 Matrix：可空） |
| ip_last | inet | Y | NULL |
| user_agent | text | Y | NULL |
| expires_at | timestamptz | NN | CK `expires_at > created_at` |
| absolute_expires_at | timestamptz | Y | NULL（B0 建议 `>= expires_at` 未冻结 → PROPOSED，不实施） |
| last_used_at | timestamptz | Y | NULL |
| revoked_at / revoked_reason / replaced_by | timestamptz/text | Y | NULL |
| created_at / updated_at | timestamptz | NN | |

- 多 Session 允许（user+device 不设唯一）
- 过期清理为 TTL job（应用层）；DB 只保证状态 CK + `expires_at > created_at`
- 设备撤销级联其会话：**应用层同事务**（冻结设计明确 DB 层不写跨表 trigger）

---

## 6. 索引（非 PK/UQ，来自 B0 INDEX_STRATEGY 已定义清单）

| index | table | type | 服务查询 |
|---|---|---|---|
| `ix_identities_user` | identities | btree (user_id) | FK 反查（users 删除 CASCADE 扫表）+ "某用户全部身份" |
| `ix_credentials_user` | credentials | btree (user_id) | FK 反查 + 按用户列凭据 |
| `ix_devices_user_status` | devices | btree (user_id, status) | 设备列表 / 批量撤销 |
| `ix_sessions_user_status` | sessions | btree (user_id, status) | 会话列表 / 批量撤销 |
| `ix_sessions_identity` | sessions | btree (identity_id) | FK 反查（identity RESTRICT 检查） |
| `ix_sessions_device` | sessions | btree (device_id) | FK 反查（device 删除 CASCADE） |
| `ix_sessions_expires_active` | sessions | btree (expires_at) WHERE status='active' | TTL 清理 job |

> 不建：users.status 单列（无批扫 job，B0 标注 P3 候选）；credentials 无 algorithm/type 单列。

## 7. Trigger（B0 TRIGGER_INVENTORY A 组，Identity 域仅此）

| name | table | timing/event | purpose |
|---|---|---|---|
| `set_updated_at()` 函数 | —（函数，0003 内建） | — | `NEW.updated_at = now()` |
| `tg_users_set_updated_at` | users | BEFORE UPDATE | 维护 updated_at |
| `tg_identities_set_updated_at` | identities | BEFORE UPDATE | 同上 |
| `tg_credentials_set_updated_at` | credentials | BEFORE UPDATE | 同上 |
| `tg_devices_set_updated_at` | devices | BEFORE UPDATE | 同上 |
| `tg_sessions_set_updated_at` | sessions | BEFORE UPDATE | 同上 |

> Identity 域**无**跨表业务 trigger（设备撤销级联、会话过期均在应用层，冻结设计明确）。

## 8. 设计不明确项与处置

| 项 | 冻结状态 | 处置 |
|---|---|---|
| `users.display_name` / `email_verified_at` 等 NULL 粒度 | 主文档未逐列标 NULL | 以已批准 B0 Matrix 判定（文档 `email_verified_at` 语义必空即证"未标 ≠ NN"） |
| `sessions.absolute_expires_at >= expires_at` | B0 标"建议" | **PROPOSED**：不实施，注释保留 |
| `users.failed_attempts <= 20` CHECK | B0 标"建议" | **PROPOSED**：不实施 |
| `users.primary_identity_id` FK | 主文档 FK/ER 无此边 | 不加 FK（避免循环），应用层语义 |
| citext 扩展 | 主文档明确"推荐 text+lower" | 用 text + lower 表达式 |

> 以上处置均已在 B0 文档批准范围内；**未发现需要停下来报告的架构级不明处**。
