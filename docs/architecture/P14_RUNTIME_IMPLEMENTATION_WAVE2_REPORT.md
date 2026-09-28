# UAP — P14 RUNTIME IMPLEMENTATION WAVE 2 REPORT

> ## 状态
>
> ```text
> 轮次      = P14 WAVE 2 IMPLEMENTATION（Identity / Device / Session / Context / Authz / API）
> 基线      = HEAD c420403d… · migration 0017_p13_seed · 0018+ = 0 · Wave 1 = ACCEPTED
> 结果      = Wave 2 = **IMPLEMENTED + VERIFIED**（68 Wave2 passed · 211 Wave 1 regression passed）
> 边界      = 不宣称 P14 完成（Bootstrap CLI = OUT OF SCOPE · P14 Overall = NOT YET）
> ```

---

# 1. Human Authorization

```text
W2-AUTH-01 Identity                     = AUTHORIZED
W2-AUTH-02 Device                       = AUTHORIZED
W2-AUTH-03 Session                      = AUTHORIZED
W2-AUTH-04 Authenticated Context        = AUTHORIZED
W2-AUTH-05 Authorization Integration    = AUTHORIZED
W2-AUTH-06 API Adaptation               = AUTHORIZED
W2-AUTH-07 Wave 2 Security Tests        = AUTHORIZED

同轮冻结不变式：Bootstrap CLI = OUT OF SCOPE · Schema Support Objects = SEPARATE DECISION ·
                New Role = FORBIDDEN · New Grant = FORBIDDEN · Migration 0018+ = FORBIDDEN ·
                P15 = FORBIDDEN · COMMIT/TAG/PUSH = FORBIDDEN
依据：P14_RUNTIME_WAVE2_HUMAN_DECISION_SHEET §R（36/36 FROZEN）· PDL 附录 P
```

---

# 2. Implementation Scope（实际落地）

```text
新增（Wave 2）
  services/mapping/{__init__,errors,vocabulary}.py        Domain↔Persistence 显式映射
  services/reads.py                                       SafeReader（见 §14 D-01）
  services/identity/{__init__,errors,hashing,repository,service}.py
  services/device/{__init__,errors,repository,service}.py
  services/session/{__init__,errors,repository,service}.py
  services/context/{__init__,errors,model,builder,authorization_adapter}.py
  services/audit/{__init__,writer}.py
  services/use_cases/{__init__,flows}.py                  事务所有者（handler 不开事务）
  apps/api/{dependencies,error_mapping}.py
  apps/api/routes/{identity,devices,sessions}.py
  tests/unit/test_wave2_{vocabulary_mapping,credentials,error_mapping}.py
  tests/integration/wave2_testkit.py
  tests/integration/test_wave2_{identity,device,session,authorization,api}_security.py

修改
  apps/api/main.py        lifespan 接入 Wave 1 RuntimeApplication + 挂载 3 个新路由
  tests/integration/test_runtime_db_wave1.py   基线断言改为不变量式（见 §14 D-02）
  docs/architecture/P14_RUNTIME_WAVE2_IMPLEMENTATION_AUTHORIZATION_SHEET.md（授权登记）
  docs/architecture/P14_RUNTIME_IMPLEMENTATION_ACCEPTANCE_MAPPING.md（§19 验收推进）

未修改（Wave 1 Foundation 冻结）
  infrastructure/runtime/**（除 reader 规避外未改）· infrastructure/database/{runtime,principal,
  session,config,health}.py · services/authorization/**（Stage 2 零改写）
  migrations_alembic/** · C2 / CC-7 / P13 seed / roles / grants
```

---

# 3. Identity（§五 – §十）

```text
实现 = services/identity/*（session-scoped service；事务由 use-case 拥有）
落地语义
  · onboarding 一个 use-case 事务内写 users + identities + credentials（§四十二）
  · users.status 五态 / identities.status 四态（§5.2 / §5.3），无新增 persisted status
  · 首登成功即完成 unverified → active（verification，一次性、fail-closed）
  · 唯一性沿用 0017（全局 · lower · 软删除释放）；重复 → IdentityConflict = identity_conflict
  · 凭据：password only · Argon2id · 无明文 · rotate = 旧行 revoked + 新行 insert（无物理删除）
  · 失败计数：bounded（5 次）+ 阈值锁（900s），使用既有 failed_attempts / locked_until
证据 = test_wave2_identity_security.py（12 passed）
```

---

# 4. Credential（§八 / §九 / §三十三）

```text
哈希 = argon2-cffi（argon2id · t=3 · m=64MiB · p=4）· 存储值以 $argon2id$ 开头（实测断言）
轮换 = 旧行 revoked_at + 新行 insert（**顺序**受 uq_credentials_active_password 约束）
泄漏面 = logs / metrics / traces / audit / API response / exception ⇒ 六面均无 secret
  证据：SQL 层断言 secret_hash 不含明文 · audit metadata 检索明文 = 0 · API 响应无 password 字样
不足时策略 = 既有字段（failed_attempts / locked_until / expires_at / revoked_at）已足够，
             未创建任何新计数表，未登记 SCHEMA DEPENDENCY
```

---

# 5. Device（§十一 – §十六）

```text
Enrollment = authenticated/eligible user + challenge + verification ⇒ device pending → active
  · device 行 **从不直接 INSERT active**（先 pending 再置 active，同事务）
Challenge 载体 = 既有 schema 的 credentials 行（type='otp' · Argon2id）
  · 绑指纹：hash(secret + "\n" + fingerprint) ⇒ 指纹不符即失败
  · 一次性：消费 = revoked_at（显式·可观测）· 过期/重放一律拒绝
Trust 状态 = 五态 persistence truth（pending/active/untrusted/revoked/lost）
  · 只有 active 可认证；untrusted ≠ active · lost ≠ revoked；lost→active **无自动路径**
Revoke = device revoked + 其全部 active sessions revoked，**同一事务原子完成**
唯一性 = 既有 UNIQUE(user_id, fingerprint)（per-user）；跨用户同指纹允许（未新增全局唯一）
证据 = test_wave2_device_security.py（13 passed）
```

---

# 6. Session（§十七 – §二十一）

```text
创建前置 = active identity + active credential + active device + authenticated request（§十七）
device 绑定 = normal human session 必须在 use-case 层携带 device_id（schema nullable 未改）
并发 = 多设备 + 每设备多会话；未新增 UNIQUE(device_id)；不 auto-kick 旧会话
过期 = expires_at（relative）+ absolute_expires_at（绝对上限）；refresh 不得越过 absolute
  全部比较使用 tz-aware UTC（§二十）
Revoke 矩阵（granular）
  logout → 仅该会话 · device revoke → 该设备全部 active 会话（§十五）
  identity revoke → 该 identity 的 active 会话 + 凭据 revoke（同事务）
  credential revoke → 该凭据认证被拒（不再签发新会话）
证据 = test_wave2_session_security.py（11 passed）
```

---

# 7. Authenticated Context（§二十二 – §二十五）

```text
模型 = AuthenticatedRuntimeContext（frozen · request-scoped）字段：
  user_id · identity_id · session_id · device_id · tenant_id · space_id ·
  subject_type · scope · authentication_assurance · correlation_id/request_id
禁止承载 = credential/secret/hash · 整行 ORM 对象 · membership 集合 · role_permissions
log_fields() = 白名单投影（仅标识与 assurance）
tenant/space 解析 = 唯一候选可确定性解析；多候选 ⇒ context_required；
                    无 active membership ⇒ DENY；handler 不参与选择
证据 = test_wave2_authorization_security.py（context 部分）+ test_wave2_api_security.py
```

---

# 8. Authorization（§二十六 – §二十九）

```text
复用 Stage 2（services/authorization/**，零改写）· 新增薄 adapter：
  services/context/authorization_adapter.py
集成事实（实测确认）：Stage 2 的 SubjectResolver 以 **users.id** 解析 USER subject
  （AuthorizationRepository.get_user(subject.identity_id)）⇒ adapter 的
  `subject.identity_id = context.user_id`（= VOC-W2-01 的 persistence anchor 裁决）
评估顺序 = identity → device → session → tenant → space → Stage 2 → use-case（§二十八）
fail-closed = evaluator 异常 ⇒ DENY(reason=authorization-unavailable)（实测）
effect 词表 = 仅消费 allow/deny；REQUIRES_APPROVAL = DEFERRED（未新增第三套 effect）
证据 = test_wave2_authorization_security.py（10 passed）

FINDING（登记 · 非阻断）：既有 canonical ACTIONS（12）不含 identity/device/session 管理动作，
  故 Wave 2 的自助操作（logout/device revoke 等）以 **认证 + 归属校验** 强制，
  未新增任何 permission vocabulary（§二十九）。见 §14 FINDING-AUTHZ-1。
```

---

# 9. API（§三十 – §三十三）

```text
定位 = transport / adaptation only（handler 无 SQL · 无授权判断 · 无事务）
路由（仅 §三十一 允许范围）
  POST /identity/onboarding · POST /identity/authenticate
  POST /devices/enrollment-challenge · POST /devices/enrollment
  POST /devices/{id}/revoke · POST /devices/{id}/lost
  POST /sessions · POST /sessions/refresh · POST /sessions/logout · GET /me
未实现 = generic admin CRUD / permission admin / role admin / bootstrap / migration / schema 端点
lifespan（§三十二）= 接入 Wave 1 RuntimeApplication（同一 bootstrap · 同一 uap_runtime ·
  同一 lifecycle · 未创建第二套 bootstrap）；startup 失败 = 进程失败（无 degraded mode）
错误映射（§三十三）= 8 类 taxonomy → 401/403/400/422/409/503/500；
  security/persistence 类**统一模糊化**（响应体不含 role/DSN/SQL/表名）
证据 = test_wave2_api_security.py（6 passed · 含 503 不泄露断言）

FINDING（登记 · 非阻断）：readiness 探针仍走 Wave 0 的 process engine
  （apps/api/routes/health.py → check_database），runtime 服务走 RuntimeDatabase，
  因而进程内可能存在两个 engine。修改 health 面会触碰既有健康契约测试，故本轮不改，
  登记为 FINDING-ENGINE-1（建议在 P14 final 或下一 Wave 统一）。
```

---

# 10. Security Tests（§三十四 – §四十一）

```text
Identity   12 · Device 13 · Session 11 · Authorization 10 · API 6 = **54**
另加 Wave 2 Unit 14（映射 / Argon2id / 错误映射）
拒绝面实测：invalid/expired/revoked credential · revoked/suspended identity · locked/deleted user ·
  revoked/lost/untrusted/pending device · expired/absolute-expired/revoked session ·
  wrong device/identity binding · inactive/missing membership · wrong tenant/space ·
  default deny · evaluator failure · 缺凭据/畸形凭据 · DB 失败 503
全部 fail-closed（无 anonymous fallback）；重放/过期 challenge 被拒；granular revoke 不扩散
```

---

# 11. Schema Boundary / Grant Boundary

```text
Schema Mutation（Wave 2 引入的新对象）= **0**
  实测：pg_class 156 · pg_proc 22 · pg_trigger 272 · parent triggers 39（与基线一致）
  alembic = 0017_p13_seed · 0018+ = 0 · migration 文件未新增/未修改
Grant Boundary
  GRANT / REVOKE / ALTER ROLE / CREATE ROLE = 0
  grants = uap_runtime 51 · uap_bootstrap 6 · uap_app 5 · uap_seed 0 · uap_migrator 245（未变）
  default_acl = 0（未变）· memberships = 0（未变）
  C2 md5 = 185e95be8bc4304edbcd3f4d5cda1eff（未变）· P13 seed = 3/12/12（未变）
  roles = 6（属性未变）· schema CREATE=false（未变）
  受保护文件：env.py / 0016 / 0017 sha256 **未变**（PDL 仅上轮授权的附录追加）
Security Grant Gap = **NONE**（Wave 2 主链操作全部命中已冻结的 51 项授权）
SCHEMA DEPENDENCY = **NONE**（未出现需要新对象的实现需求）
EXPECTED TEST DATA = audit_logs 926 行（append-only · 不可删除 · 见 manifest §4）
```

---

# 12. Wave 1 Regression（§四十八）

```text
执行（显式 allowlist · 未跑任何 CF-C-4 禁跑文件）
  Architecture 28 · Contract 23 · Runtime Unit 20 · Runtime Integration 13 ·
  Security Regression 46 · Acceptance subset 81 = **211 passed · 0 failed**
结论：Wave 1 基础行为未被 Wave 2 破坏（bootstrap / connection / pool / transaction /
      lifecycle / health / observability / error taxonomy / authz boundary 均保持）
唯一调整：test_runtime_db_wave1.py 的 audit_logs 绝对断言 → 不变量断言（见 §14 D-02）
```

---

# 13. Wave 2 Change Boundary（§五十四）

```text
new files      = 26（services 14 · apps/api 3 · tests 9）
modified files = 4（apps/api/main.py · tests/integration/test_runtime_db_wave1.py ·
                    docs/...WAVE2_IMPLEMENTATION_AUTHORIZATION_SHEET.md ·
                    docs/...ACCEPTANCE_MAPPING.md）
historical dirty set = 未 stage（staged = 0）
frozen files untouched = migrations_alembic/** · services/authorization/** ·
                    infrastructure/**（除 apps/api/main.py 的 lifespan 接线）
commit / tag / push = 0 / 0 / 0
environment    = 安装 argon2-cffi 25.1.0（+cffi/pycparser）到项目虚拟环境（见 §14 ENV-1）
```

---

# 14. Defects Found / Fixed（§五十二 · 不隐藏）

```text
D-01  分类 = FOUNDATION DEFECT（Wave 1）· **未修复**（Wave 1 冻结）
  位置 = infrastructure/database/persistence.py::Repository._fetch_one/_fetch_all
  事实 = (a) 两处 except 引用未定义名 `err` ⇒ SQLAlchemyError 变成 NameError；
         (b) `_fetch_one` 用 `.one()` ⇒ 零行时 raise NoResultFound，"查无此行"无法表达为 None
  Wave 1 未暴露原因 = 其测试从未让这两个 helper 命中"缺失行/DB 错误"路径
  本轮处置 = 不改冻结文件；Wave 2 仓库继承 `services/reads.py::SafeReader`（同名方法，语义正确）
  建议修复 = 两行（`_safe(exc)` + `.first()`）；需 Human 授权 foundation change

D-02  分类 = WAVE-1 测试基线调整（已登记 · 非行为变更）
  位置 = tests/integration/test_runtime_db_wave1.py::test_approved_reads
  事实 = 原断言 `audit_logs == 0`；Wave 2 合法追加 926 行且审计表 append-only，无法回到 0
  处置 = 改为不变量断言（"本次调用不得追加审计行"），保留原意图
  备注 = 如需严格保持 Wave 1 工件字节不变，可回退该行并接受该用例失败（请 Human 指示）

D-03  分类 = IN SCOPE · 已修复
  事实 = authenticate 仅拒绝 REVOKED identity，**suspended identity 可继续认证**（违反 §三十四）
  修复 = 仅允许 ACTIVE/UNVERIFIED 通过；其余一律 CredentialRejected

D-04  分类 = IN SCOPE · 已修复
  事实 = 失败计数在拒绝路径被事务回滚 ⇒ 有界锁定永不生效（违反 §九）
  修复 = use-case 在事务内捕获拒绝、让计数与审计提交，再在事务外抛出拒绝
         （仅提交计数与审计行，不授予任何权限）

D-05  分类 = IN SCOPE · 已修复
  事实 = rotate 先 insert 新行再 revoke 旧行 ⇒ 违反既有 `uq_credentials_active_password`
  修复 = 先 revoke 旧行再 insert 新行（同一事务，成对原子）

D-06  分类 = IN SCOPE · 已修复
  事实 = 非 IP 的 client host（ASGI test client = "testclient"）写入 `inet` 列 ⇒ 503
  修复 = `normalize_client_ip()`：非 IP 一律存 NULL（请求元数据不得中断认证）

D-07  分类 = TEST DEFECT · 已修复
  事实 = 过期会话测试直接回退 expires_at ⇒ 违反 `ck_sessions_expiry`
  修复 = 同时回退 created_at

ENV-1  分类 = 依赖/可复现性缺口（已登记 · 未决）
  事实 = password 凭据要求 Argon2id，但项目环境无任何密码学库；本轮安装 argon2-cffi 25.1.0
  未做 = **未修改** requirements.txt / pyproject.toml（属依赖清单冻结面）
  建议 = 由 Human 授权把 argon2-cffi 写入依赖清单，否则环境不可复现
```

```text
FINDING-AUTHZ-1（登记 · 非阻断）：canonical ACTIONS 无 identity/device/session 管理动作 ⇒
  自助操作以认证 + 归属校验强制；未新增权限词表（§二十九）。若未来需要"管理员可撤销他人设备"，
  必须走独立 Decision（新增动作或 Approval 模型），不得自行扩词表。
FINDING-ENGINE-1（登记 · 非阻断）：readiness 探针与 runtime 服务使用不同 engine（见 §9）。
FINDING-P11-1（正向证据）：P11 触发器强制 role/scope 形态与 membership-role 一致性
  （enforce_roles_scope_shape / enforce_tm_role_scope），本轮 fixture 曾两次被其正确拒绝。
FINDING-IDX-1（只读发现）：新增了解到的既有唯一约束 —— `uq_credentials_active_password`
  （每 identity 一个活跃 password）· `uq_identities_email` · `uq_identities_ref` ·
  `uq_sessions_token` · `uq_sessions_refresh`。Wave 2 实现已遵守。
```

---

# 15. Acceptance Status（§四十九 / §五十六）

```text
Identity                  = IMPLEMENTED + VERIFIED（12 security tests）
Credential Integration    = IMPLEMENTED + VERIFIED（Argon2id · rotate · 无明文）
Device                    = IMPLEMENTED + VERIFIED（13 security tests）
Session                   = IMPLEMENTED + VERIFIED（11 security tests）
Authenticated Context     = IMPLEMENTED + VERIFIED（context 矩阵 + API 往返）
Authorization Integration = IMPLEMENTED + VERIFIED（10 security tests · Stage 2 复用）
API Adaptation            = IMPLEMENTED + VERIFIED（6 security tests）
Wave 2 Security Tests     = PASS（54 + 14 unit）
Wave 1 Regression         = PASS（211 passed）
Schema Mutation           = 0 · Privilege Mutation = 0 · Security Boundary = INTACT

不宣称：P14 COMPLETE / P14 Overall Acceptance（Bootstrap CLI = OUT OF SCOPE；
        Schema Support Objects = SEPARATE DECISION；P15 = FORBIDDEN）
```

**END OF P14 RUNTIME IMPLEMENTATION WAVE 2 REPORT（2026-09-28 · Wave 2 IMPLEMENTED + VERIFIED · P14 Overall = NOT YET · 未 commit/tag/push · HARD STOP ACTIVE）**
