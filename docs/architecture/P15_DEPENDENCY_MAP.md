# UAP — P15 DEPENDENCY MAP

> 轮次 = STEP 3 · P15 PREP（依赖映射 · 标注 hard / soft / future / blocked）

```text
上游依赖（P15 建立在其上 · 不得修改）
  P14 release（commit 15feebad · tag UAP-V0.1.10-P14-RUNTIME-SLICE）  = **hard**
  Schema 0017（current schema truth · alembic head 0017_p13_seed）     = **hard**
  Authorization Stage 2（services/authorization · 12 canonical actions）= **hard**
  P14 Runtime（Wave 1：bootstrap/connection/pool/transaction/persistence/lifecycle/
                 health/observability/error taxonomy/authz boundary）    = **hard**
  Security boundary（uap_runtime 51 · uap_bootstrap 6 · C2 · CC-7）      = **hard**
  Domain 契约（core/* 12 域 · 冻结语义）                                = **hard**
  Infrastructure（database/runtime/logging/monitoring）                 = **hard**
  API adaptation（apps/api · 5 路由组）                                 = **soft**（仅当 P15 需 API）

候选相关依赖
  C-1 D-01 修复           → Wave 1 artifact（需 foundation 授权）        = **blocked**（未授权）
  C-2 管理类能力           → Stage 2 词表 / Approval model               = **blocked**（需 Decision）
  C-3 engine 统一          → health 契约 + database 层                  = **soft**
  C-4 Bootstrap CLI        → uap_bootstrap 一次性边界                    = **blocked**（RTA-09 = OPTION B）
  C-5 outbox consumer      → events 表 + worker 边界                     = **blocked**（需 Decision）
  C-6 AI 启用              → P10 AI gateway schema + provider 凭据        = **blocked**（需 Decision + 凭据策略）
  C-7 Frontend             → API surface（P14 已提供）                   = **soft**
  C-8 审计深化             → audit_logs（append-only） + observability    = **soft**

外部集成
  External AI/API providers = **future**（P10 决策已冻结 provider/route/policy 语义，未启用）
  GitHub remote（origin）   = hard（release/发布链路 · P15 不得修改）

未决
  · P15 scope 未冻结 ⇒ 上表候选依赖的激活顺序 = UNKNOWN（须 Human Decision）
```

**END OF P15 DEPENDENCY MAP（2026-09-28 · hard/soft/future/blocked 已标注 · HARD STOP ACTIVE）**
