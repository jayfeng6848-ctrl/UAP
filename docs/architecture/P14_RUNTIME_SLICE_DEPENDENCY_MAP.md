# UAP — P14_RUNTIME_SLICE DEPENDENCY MAP

> ## 阶段与边界
>
> ```text
> 阶段      = `P14_RUNTIME_SLICE`（FROZEN 编号 · PDL 附录 M.1）
> 本文档性质 = PREP 设计产物（DRAFT · NOT FROZEN）
> 依据      = RUNTIME_DOCUMENT_SET_DECISION.md §2（本文件为其中 DEPENDENCY_MAP）
>              + P14_RUNTIME_SLICE_FORMALIZATION_GATE_REPORT §4.2（C-9 三层关系 · 已冻结）
> 本轮未做   = 未创建 migration / schema / runtime code / services 实现 / API / worker / scheduler
> ```

---

# 1. 三层模型（C-9 冻结关系）

```text
┌──────────────────────────────────────────────────────────────┐
│ Schema Layer                                                 │
│   0001 … 0017 迁移链：结构 · 约束（PK/FK/UQ/CK）· 触发器 ·   │
│   索引 · trust boundary（0016 CC-7）                          │
│   owner = uap_migrator（178 对象）                            │
└──────────────────────────────────────────────────────────────┘
                            │  提供结构
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Authorization / Data Baseline                                │
│   P13 seed：acl_subject_types 3 · permissions 12 ·           │
│             role_permissions 12                              │
│   身份分离：migration = uap_migrator · runtime = uap_app      │
│   缺口（有意）：users 0 · 凭据 0 · membership 0 · PM 0         │
└──────────────────────────────────────────────────────────────┘
                            │  提供基线与身份边界
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Runtime Layer（本阶段 P14_RUNTIME_SLICE）                     │
│   进程/服务宿主 · API-service 边界 · onboarding ·             │
│   授权执行 · 运维接口 · bootstrap CLI                         │
└──────────────────────────────────────────────────────────────┘

方向律：**只能由下向上依赖**。反向依赖（Schema/Data 依赖 Runtime）= 0。
```

---

# 2. Runtime depends on（四项 · 逐项）

## 2.1 identity

```text
Runtime 依赖什么
  · users 表的既有结构（id/email/username/status/…；ck_users_login 要求 email 或 username 非空）
  · identities / primary_identity_id 语义（既有表，未使用）
  · 授权主体词汇（D-AUTH-18：USER / ROLE / AGENT；不得混用 identity provider 词汇）

Runtime 必须补齐什么（P13 有意留空）
  · 首个可登录主体的建立（users 行）
  · 凭据建立与生命周期（onboarding 设密）
  · 设备/主体关联策略（具体形态 = OPEN）

既有约束（不得违反）
  · D-P13-06：identity row allowed · credential secret 不得出现在 seed
  · D-P13-13：credentials = 0 / plaintext = 0 / fabricated = 0（P13 侧）
  · D-PLAT-11①：首个正式可登录主体只经 P13 建立 ⇒ 「可登录」完成机制属 Runtime
```

## 2.2 authorization

```text
Runtime 依赖什么
  · roles（platform_admin 归 0005；tenant/space 四角色按 onboarding 补种）
  · permissions（12 项 canonical · is_system=true · 无 deny）
  · role_permissions（platform_admin × 12 × allow）
  · resource_permissions（ACL 执行面，P13 时 0 行）
  · platform_memberships / tenant_memberships / memberships（P13 时均 0 行）

Runtime 必须实现什么
  · 授权判定执行（default deny · deny 优先 · FAIL CLOSED）
  · 首个平台管理员与后续 grant/revoke/transfer 的受控路径

既有约束
  · 不新增授权模型 · 不新增 subject type · 不改 action 词表（D-AUTH-05）
  · 判定位置（API / service / policy）为 OPEN
```

## 2.3 audit boundary

```text
Runtime 依赖什么
  · audit_logs（0013，分区表，PK(id, occurred_at)）
    actor_type NOT NULL · actor_id nullable（**无 users FK**）· action NOT NULL
    result ∈ {success,denied,error} · risk_level ∈ {LOW,MEDIUM,HIGH,CRITICAL} · metadata NOT NULL
  · tg_audit_immutable（BEFORE DELETE/UPDATE 阻断 ⇒ 写入后不可修正）
  · events（transactional outbox，0013）

Runtime 必须决定什么（OPEN）
  · 哪些 runtime 事件写 audit_logs · actor 语义（system vs user）· action 命名规范
  · events outbox 的发布路径（若本阶段涉及）

既有先例
  · bootstrap 路径写 audit(action='platform.admin.bootstrap', actor='system')（R4/R5）
  · 既有迁移不写 audit（P13 = IMPL-03 A）
```

## 2.4 database access model

```text
Runtime 依赖什么
  · runtime DSN：DATABASE_URL → config/settings.py → uap_app
  · uap_app 的**恰 5 项**显式授权（SCHEMA public USAGE · alembic_version SELECT ·
    audit_logs(+当期分区) INSERT/SELECT）
  · uap_app CREATE = false（无 DDL）

Runtime 必须面对的事实（约束，不是待办）
  · 按 OI-G-1，runtime 的**逐表 DML 矩阵**尚未核定（登记于 BATCH-D）
    ⇒ Runtime PREP 必须把「哪些表需要哪些 DML 授权」作为**显式 OPEN 项**报 Human 裁定，
      因为扩张 uap_app 授权属独立授权（不得自行扩权）
  · uap_app 当前对 users / roles / tenants / spaces / memberships 等表**无任何授权**
    ⇒ onboarding 与 bootstrap 的写入路径必须由 Human 决定（扩权 or 受信专用路径）
```

---

# 3. Runtime does not own（三项）

```text
· schema migration        —— 任何 migration / DDL 需求都必须另立独立授权；
                             Runtime 路线内不得创建 0018+
· permission definition   —— Runtime 只**消费**既有 permission 词汇与绑定，
                             **不定义**新权限、不改 12 项、不改 action 词表
· database governance     —— 角色拓扑 · ownership 拓扑（178 全 uap_migrator）·
                             grants 面 · default ACL 均属治理面，Runtime 不得变更
```

---

# 4. 边界检查结果

```text
Core → Domain                = 0
  证据：tests/architecture 全量执行 = 28 passed（含 test_dependency_rules.py 的 AST 守卫）

Runtime → Schema ownership   = 0
  证据：0018+ migration = 0 · P14_IMPLEMENTATION* 文件 = 0 ·
        migrations_alembic/versions 仍为 17 个文件（0001…0017）

Runtime → Future phase leakage = 0
  证据：无 P15+ 文档 · 无未来阶段编号引入 · 无 services 实现文件新增

其他
  · 本次未触碰 0016 · 0017 · env.py · PDL（冻结正文）
  · 未新增 GRANT / ROLE / OWNER / default ACL 变更
```

---

# 5. 与既有守卫（G-1…G-8 · D-PLAT-17）的关系

```text
硬门（未通过即不得验收）
  G-1 core ↛ SQLAlchemy/psycopg      · G-2 core ↛ services · G-3 agent ↛ services
  G-4 domains ↛ {services, infrastructure}
  G-6 readiness 的 migration 组件 critical=True
  G-7 启动不调用 legacy runner（且 Settings 不含该开关）
advisory
  G-5 apps ↛ SQLAlchemy/psycopg（代理判据，不等价于 D-PLAT-04.a 语义）
deferred / cancelled
  G-8 bootstrap 唯一性（Deferred）· G-9 compose↔alembic heads 漂移（Cancelled）

Runtime Slice 的义务：
  · 实施前后所有硬门必须保持通过（由人工执行并留证 · D-PLAT-17 ⑦）
  · 不得为通过守卫而削弱断言（Rule 10：绝不为 PASS 作弊）
```

---

# 6. 依赖缺口登记（交 PREP_REPORT 的 OPEN 清单）

```text
GAP-1  uap_app 的逐表 DML 矩阵未核定（OI-G-1 · BATCH-D）
       ⇒ onboarding / bootstrap 需要的写路径必须先由 Human 裁定
GAP-2  Runtime 凭据存储与密钥管理方案未定义
GAP-3  events（outbox）在本阶段是否启用未定义
GAP-4  services/ 内部结构（C-5）与 domains 公开契约载体（C-6）未定义
GAP-5  部署模型与运维手册缺失（C-10）
（以上均为 OPEN，不得由 Bot 自行裁定）
```

---

# 7. 状态与边界

```text
本文档 = DRAFT · NOT FROZEN
未产生实施授权。P14 IMPLEMENTATION = NOT AUTHORIZED。
本轮工程变更：DDL = 0 · DML = 0 · migration = 0 · runtime = 0 · commit/tag/push = 0
```

---

## 8. Decision Sync（append-only · 2026-09-27 · 依 PDL 附录 N）

> 本节为**追加**：不改写 §1–§7；把已冻结决策映射到既有章节；不写实现结果。

```text
§2.1 identity        ← OQ-P14-01（staged onboarding · 客户端不得直接访问 DB）
                        OQ-P14-02（credential 独立生命周期 · Argon2id hash）
                        OQ-P14-03（1 User : N Device · 1 Device : 1 User · 显式 enrollment/challenge ·
                                  device revoke 同事务撤销 active sessions）
§2.2 authorization   ← OQ-P14-04（centralized precheck + service/use-case enforcement）
                        OQ-P14-05（application/service boundary · default deny · deny precedence · ABAC ·
                                  **不使用 DB RLS 作为主授权机制**）
§2.3 audit boundary  ← OQ-P14-11（operational logs 与 audit logs 分离）
§2.4 database access model ← OQ-P14-13（**OPTION B — Trusted Internal Service Boundary**）：
                        · uap_app 保持当前最小权限（5 项 + schema USAGE · CREATE = false）
                        · 不授予宽泛 DB 写权限
                        · Runtime 不使用 uap_migrator
                        · Runtime 使用独立 runtime / trusted service principal
                        · 新 DB role / GRANT / privilege **不并入本轮**
                        · 新 privilege 另开 Privilege / Security Gate
                      → 完整登记见 Contract §13「P14 PRIVILEGE PRECONDITION」
§3   Runtime does not own ← 不变（schema migration / permission definition / database governance）
§5   与既有守卫的关系      ← 不变（G-1…G-8 职责持续）
§6   依赖缺口 GAP-1…GAP-5 ← GAP-1（uap_app 逐表 DML 矩阵）现已有**机制性答复**：
                        OPTION B ⇒ 写路径不经 uap_app 宽泛扩权，改经受信内部边界；
                        但受信主体的形态/授权仍属**独立 Gate**（PRECONDITION，未关闭）
```

```text
边界检查（本轮复核，未变）：
  Core → Domain = 0 · Runtime → Schema ownership = 0 · Future phase leakage = 0
新增禁止（依冻结决策）：Runtime 不使用 uap_migrator · Runtime 不继承 migration privilege ·
                      本轮不新增 role / GRANT
P14 IMPLEMENTATION = NOT AUTHORIZED（未变）。
```

---

**END OF P14_RUNTIME_SLICE DEPENDENCY MAP（2026-09-27 · PREP · §8 Decision Sync 追加 · 三层关系冻结对齐 · `P14 IMPLEMENTATION = NOT AUTHORIZED`）**
