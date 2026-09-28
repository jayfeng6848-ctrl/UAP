# UAP — P15 PREP ARCHITECTURE SNAPSHOT

> 轮次 = STEP 3 · P15 PREP（只读结构快照 · 未改任何代码 · 发现违规只登记不修复）

## 1. 分层现状（实测目录）

```text
Core            core/{audit,auth,device,event,identity,membership,permission,policy,resource,
                     session,space,tenant}/interfaces.py（12 域契约）
Domain          domains/{business,company,entertainment,family}/manifest.py（业务域 · 非平台核心）
Infrastructure  infrastructure/{database,runtime,logging,monitoring,cache,queue,storage}
Services        services/{authorization,identity,device,session,context,mapping,audit,use_cases} · reads.py
API             apps/api/{main,dependencies,error_mapping}.py · routes/{health,meta,identity,devices,sessions}.py
Worker          apps/worker/main.py（generic scheduler · P14 OUT OF SCOPE）
Frontend        apps/frontend/**（Vite/React · 非 Python runtime 面）
Intelligence    intelligence/**（AI 能力层 · P10 AI gateway schema 已存在）
Agent           agent/**（agent runtime / memory / workflow / tools 接口）
Migration       migrations_alembic/**（0001–0017）
Persistence     PostgreSQL 0017（uap_b1_test 为 schema truth；正式 uap 为空库）
Authorization   services/authorization/**（Stage 2 唯一权威 · 只读不写 · 不缓存）
Security        角色/授权面（uap_runtime 51 · uap_bootstrap 6 · C2 · CC-7）
Observability   infrastructure/logging/{structured,redaction}.py · monitoring/metrics.py
```

## 2. 依赖方向（实测）

```text
Core → Domain              = 0     （tests/architecture 守卫通过）
Domain → Infrastructure     = 0     （domains/** 仅 manifest）
Domain → Runtime            = 0
API → Service               = 有    （routes → services.use_cases → 各层 service）
Service → Repository        = 有    （services.<layer>.repository : SafeReader）
Authorization → Repository  = 有    （AuthorizationRepository 自带 _fetch/_fetch_one · 不继承 Wave 1 Repository）
Runtime → DB                = 有    （RuntimeDatabase → uap_runtime · 唯一 application-level DB 边界）
Handler → SQL               = 0
Repository self-commit      = 0
```

```text
架构违规 = 0（未修改任何代码）
```

## 3. P14 之后对 P15 有效的不变量

```text
· Core 不依赖上层；Domain 契约不引用 concrete service / SQLAlchemy session / PG principal
· 唯一 runtime DB principal = uap_runtime；migration = uap_migrator；bootstrap = uap_bootstrap（独立）
· Authorization 唯一权威 = services/authorization（禁第二套 engine / 第二套词表）
· Domain ↔ Persistence 词表差异由显式 mapping 承担；禁隐式 cast / magic string
· handler 无 SQL / 无授权决策 / 不拥有事务；use-case 拥有事务边界
· 0017 = persistence truth；新增 schema 一律 SEPARATE DECISION（RTA-10 = OPTION B）
```

**END OF P15 PREP ARCHITECTURE SNAPSHOT（2026-09-28 · 违规 0 · HARD STOP ACTIVE）**
