# UAP — P15 CANDIDATE SCOPE DISCOVERY

> 轮次 = STEP 3 · P15 PREP（候选发现 · **不构成 implementation scope**）
> 铁律 = 候选 ≠ 已授权；任何候选进入实现前须经 P15 Human Decision

## 候选清单（由 P14 遗留 + 现存资产推导）

```text
C-1  P14 遗留：D-01 foundation maintenance（Wave 1 persistence.py 两处缺陷）
     现状：DEFERRED / NON-BLOCKING · active path 已由 services/reads.SafeReader 规避
     为什么出现：P14 RELEASE GATE 登记为独立 foundation maintenance candidate
     依赖：无 · Security：No impact · Schema：No · Runtime：潜在（读取路径）·
           API：No · Authorization：No · 需 Human Decision：**是**（foundation change 授权）

C-2  P14 遗留：管理类身份/设备/会话能力（FINDING-AUTHZ-1）
     现状：DEFERRED（自助操作以认证 + 归属校验；无 admin-on-behalf-of-user）
     为什么出现：canonical ACTIONS（12）不含 identity/device/session 管理动作
     依赖：Stage 2 词表扩展或独立 Approval/Decision model · Security：**Authorization impact** ·
           Schema：可能（若新增 action/effect）· Runtime：service 层 ·
           API：是（admin 端点）· 需 Human Decision：**是**（词表 + 授权模型）

C-3  P14 遗留：FINDING-ENGINE-1（/ready 探针与 RuntimeDatabase 的 engine 并存）
     现状：ACCEPTED COMPATIBILITY FINDING（P14 内不重构）
     为什么出现：Wave 2 API 接线后的 engine 双轨
     依赖：apps/api/routes/health.py + infrastructure/database/* · Security：No impact
           （不改变授权面）· Schema：No · Runtime：health 面 · API：是 · 需 Human Decision：是

C-4  Bootstrap CLI（RTA-09 = OPTION B · P14 OUT OF SCOPE）
     现状：uap_bootstrap 6 项授权已就位但**未被任何代码使用**
     为什么出现：P14 明确"须另一独立 implementation authorization"
     依赖：uap_bootstrap 边界 · Security：**Privilege boundary impact**（一次性 bootstrap 路径）·
           Schema：platform_state/platform_memberships 已具备 · 需 Human Decision：**是**

C-5  事件 / outbox 消费（events + events_202609 已存在 · runtime 有 S/I/U）
     现状：schema 与授权就位，**无 consumer**；apps/worker 为 generic scheduler（P14 OUT OF SCOPE）
     为什么出现：P10 outbox substrate 已建、consumer 未建
     依赖：events 表 + worker 边界 · Security：Runtime security impact（新增后台写入者）·
           Schema：No · API：No · 需 Human Decision：**是**

C-6  AI / intelligence 能力启用（intelligence/** + P10 AI gateway schema 已存在）
     现状：schema 与接口存在，runtime 未启用（D-PLAT 系列对 AI provider/route/policy 有冻结决策）
     依赖：P10 决策 + provider 凭据注入 · Security：**Runtime/Audit impact**（外部调用）·
           Schema：No（已存在）· API：可能 · 需 Human Decision：**是**

C-7  Frontend 交付（apps/frontend 为 Vite/React 骨架）
     现状：非 Python runtime 面；P14 FILE_INVENTORY 未纳入
     依赖：API surface（P14 已提供 onboarding/auth/device/session/context）· Security：No impact ·
           需 Human Decision：**是**（是否属 P15）

C-8  审计 / 可观测性深化（AUD-1 / AUD-3 / AUDX-2 仍为 PLANNED/BLOCKED）
     现状：Wave 2 已写身份/设备/会话事件；审计导出与上报未实现
     依赖：audit_logs（append-only）+ logging/monitoring · Security：Audit impact ·
           Schema：No · API：可能 · 需 Human Decision：**是**
```

## SCHEMA DELTA DISCOVERY（§9）

```text
当前候选判定 = **SCHEMA CHANGE MAY BE REQUIRED**（仅 C-2 可能在新增 action/effect 时触及）
  ⇒ 未冻结 P15 scope ⇒ 不得判定为 NO SCHEMA CHANGE REQUIRED
登记：SCHEMA DECISION REQUIRED（若 C-2 被选入 P15 且需新词表/新 effect）
未实现任何 schema 变更
```

## 未决

```text
P15 主题选择 = UNKNOWN（须 Human Decision · 见 P15_HUMAN_DECISION_SHEET.md）
```

**END OF P15 CANDIDATE SCOPE DISCOVERY（2026-09-28 · 8 候选 · 未授权 · HARD STOP ACTIVE）**
