# UAP — P14 RUNTIME IMPLEMENTATION FILE INVENTORY

> ## 状态
>
> ```text
> 轮次      = P14 SECURITY CLOSURE + RUNTIME IMPLEMENTATION AUTHORIZATION PREPARATION（§十一 / §十二）
> 性质      = 只读扫描 + 归类（**未修改任何文件**）
> 归类口径   = IN SCOPE / OUT OF SCOPE / SEPARATE AUTHORIZATION（三态，无模糊区）
> 铁律      = **unknown file = 不自动进入 scope**（未明确归入 IN SCOPE 者一律视为 OUT OF SCOPE）
> 基线      = HEAD c420403d… · 现有代码为 Stage 2 Authorization 基线（034ee97）之延续
> ```

---

# 1. Runtime 分层分解（§十一）

```text
Application / API
      ↓
Authorization
      ↓
Service / Use-case
      ↓
Repository / Persistence
      ↓
uap_runtime          ← 已实施的 Security DB Boundary（本层已冻结）
      ↓
PostgreSQL

（Bootstrap 独立路径）
Bootstrap CLI
      ↓
Bootstrap boundary
      ↓
uap_bootstrap        ← 已实施（本轮不实现 CLI）

证明：`uap_migrator` **不出现在** Runtime execution path（pg_has_role 双向 False；
      Runtime 无法 SET ROLE 到 migrator；凭据不共享）
```

---

# 2. 现有文件规模（只读扫描 · 用于判定实现程度）

```text
apps/api/main.py                 77 行
apps/api/routes/health.py       109 行
apps/api/routes/meta.py          35 行
apps/worker/main.py              43 行
infrastructure/database/session.py   115 行
infrastructure/database/health.py    187 行
infrastructure/database/config.py     98 行
infrastructure/database/migration.py 190 行
infrastructure/logging/structured.py 146 行
infrastructure/logging/redaction.py   96 行
infrastructure/monitoring/metrics.py  53 行
services/authorization/（12 文件 · 合计约 1,300+ 行）
  __init__ 61 · actions 49 · audit 84 · errors 36 · permissions 232 · policy 199 ·
  repository 179 · resources 56 · scopes 48 · service 224 · subjects 148 · tools 118
config/settings.py（BATCH-B 已修改）· config/build_info.py · config/__init__.py
core/*/interfaces.py（12 域契约 · 28 文件）· agent/*（接口 11 文件）· domains/*（manifest 9 文件）
```

```text
判定依据：以上均为**既有基线代码**（非本轮创建）；P14 Runtime Slice 是在其上的**扩展**，
          而非从零创建。因此「范围」= 允许修改/扩展哪些文件，以及哪些必须冻结。
```

---

# 3. IN SCOPE（P14 Runtime Slice 允许实现/扩展）

```text
A. runtime bootstrap of application process
   · apps/api/main.py（应用装配 / 生命周期 / 优雅关闭）
   · apps/api/__init__.py

B. API / service boundary
   · apps/api/routes/__init__.py
   · apps/api/routes/health.py（liveness/readiness 面，复用 D-PLAT-14/16）
   · apps/api/routes/meta.py
   · 新增路由（identity / device / session / authorization-facing 端点）——**须在授权后新增**

C. identity onboarding workflow（database-backed）
   · services/identity/**（若不存在则新增）· 复用 core/identity 契约

D. device enrollment / session lifecycle
   · services/device/** · services/session/**（若不存在则新增）

E. centralized authorization（SEC-10 = HYBRID）
   · services/authorization/（12 文件 · 已有基线，允许扩展实现）

F. service / use-case orchestration
   · services/**（业务编排；新增包须遵循 D-PLAT-03 与 D-AUTH-16）

G. persistence adapters
   · infrastructure/database/session.py（连接边界 · 使用 uap_runtime）
   · infrastructure/database/config.py（连接配置）
   · 新增 repository 适配（经 services 调用）

H. observability
   · infrastructure/logging/structured.py · redaction.py
   · infrastructure/monitoring/metrics.py

I. runtime health interface
   · infrastructure/database/health.py（readiness 探针）

J. 测试
   · tests/ 下与上述对应之新增/扩展测试（**排除**会 reset DB 的 19 个文件 · CF-C-4）
```

---

# 4. OUT OF SCOPE（明确排除 · 不得修改）

```text
· schema redesign / 任何 DDL                          （Contract Excluded）
· migrations_alembic/** 下的 0001–0017                （历史迁移不可改写）
· 0018+ 任何 migration                                （本轮与 P14 路线内均禁止）
· core/*/interfaces.py 的**契约语义变更**              （冻结契约；仅可作为被消费对象）
· domains/**（business / company / entertainment / family manifest）  （业务域不属 P14）
· agent/**（agent runtime / memory / workflow / tools 接口）           （不属 P14）
· apps/worker/main.py                                 （generic background scheduler；
                                                        Contract 未要求 ⇒ 不自动纳入）
· infrastructure/database/migration.py                （migration engine 变更禁止）
· config/build_info.py                                （D-PLAT-15 v2 构建期只读工件）
· scripts/**（含 generate_build_info）                  （OI-G-4 范围 · BATCH-D / maintenance）
· infra/cache · queue · storage 的实际实现             （仅接口存在；无 Contract 授权）
· P15+ 任何内容
· 任何新授权模型 / 权限词表变更 / P13 seed 变更
· unrestricted admin interface
```

---

# 5. SEPARATE AUTHORIZATION（需独立授权 · 不得由 Runtime 授权隐式覆盖）

```text
S-1  config/settings.py 的运行时 DSN 切换（指向 uap_runtime）
     ⇒ 属"Runtime DB 连接配置"实施动作，须随 Runtime Authorization 明确（见 RTA-02）
S-2  新增非 migration 的 Runtime support object（若涉及 schema）
     ⇒ **必须单独进入 Schema Decision**（RTA-10）；不得由 Runtime Authorization 隐式授权
S-3  Bootstrap CLI（本轮 FORBIDDEN；其是否与 Runtime 同轮见 RTA-09）
S-4  tests/integration/** 中会 reset 数据库的 19 个文件（CF-C-4=C · BATCH-D 决定）
S-5  `uap_runtime` / `uap_bootstrap` 的**权限扩张**（任何新增 grant）
     ⇒ 必须重开 Security Decision（OI-G-1 关闭不构成自动扩权许可）
S-6  新增数据库角色
S-7  observability 引入的任何新基础设施组件（队列 / 追踪后端等）
```

---

# 6. 归类完整性声明（§二十五 "Unknown implementation boundary = 0"）

```text
本清单已覆盖仓库全部 Python 顶层目录：apps · agent · services · intelligence · core ·
infrastructure · config · domains · scripts · tests
⇒ 每一类均已被归入 IN SCOPE / OUT OF SCOPE / SEPARATE AUTHORIZATION 之一
⇒ **无模糊区域**；未列明者依铁律视为 OUT OF SCOPE（不自动纳入）

注：intelligence/** 属 AI 能力层（AI Provider/Route/Policy）；
    其 runtime 启用不属 P14 Contract 范围 ⇒ OUT OF SCOPE（未在 §4 展开，此处补记）。
```

---

# 7. 本轮工程变更

```text
未修改任何文件（纯只读扫描）· DDL/DML/migration/runtime code = 0
新增文档 = 本文件（+ 同轮 6 份）· commit = 0 · tag = 0 · push = 0
P14 RUNTIME IMPLEMENTATION = NOT AUTHORIZED
```

---

**END OF P14 RUNTIME IMPLEMENTATION FILE INVENTORY（2026-09-27 · IN SCOPE 10 组 · OUT OF SCOPE 明列 · SEPARATE AUTHORIZATION 7 项 · unknown boundary = 0）**
