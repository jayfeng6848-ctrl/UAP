# UAP — P15 THEME ANALYSIS

> 轮次 = STEP 3 · P15 HUMAN DECISION COMPLETION（候选结构分析 · 2026-09-28）
> 声明 = **不输出"哪个最值得做"**；本表为事实/结构判断（规模、负担、依赖、杠杆），
>        供 Human 决定主题组合之用。分类 = primary theme / secondary workstream /
>        maintenance / future phase，均为结构判断而非主观排序。

## 1. 候选结构对比

```text
候选  范围规模  依赖                                             安全负担  架构负担  运行时负担  API负担  测试负担  架构杠杆  平台相关性  发布复杂度
C-1   XS      无                                                 无        Wave1冻结 无         无        低        低        中          低
      = D-01（persistence.py 两行修复）· 唯一特殊之处：触碰 Wave 1 Evidence Freeze
C-2   L       Stage 2 词表 / Approval model / Authorization Decision  高     高（词表） 中         高        高        高        高          高
      = 管理他人 device/session/credential（唯一可能触发 schema 的候选）
C-3   S       apps/api/routes/health.py + database 层              无       中（健康契约）低      低        中        低        中          低
      = /ready 与 RuntimeDatabase engine 双轨统一（P14 accepted compatibility）
C-4   M       uap_bootstrap 边界（6 项已就位）· 独立授权            高（特权） 中         独立路径   无（CLI）  高        中        高          中
      = Bootstrap CLI（一次性 · 不得成为 runtime dependency）
C-5   M–L     events 表（已存在）+ worker 边界 + 幂等契约            中–高    中         高（后台）  无        高        高        高          中
      = outbox consumer（幂等/重放/并发/审计语义须先冻结）
C-6   L       P10 AI gateway 决策 + provider 凭据注入策略            高（外部） 中         中         可能      高        高        高          高
      = AI / intelligence 启用（schema 已存在；外部调用与凭据是主要风险面）
C-7   M       API surface（P14 已提供 5 路由组）                    低       低         无         高（前端） 中        中        中          中
      = Frontend 交付（非 Python runtime 面）
C-8   S–M     audit_logs（append-only）+ logging/monitoring           中（审计） 低         低         可能      中        中        高          低
      = 审计导出 / 上报语义深化（AUD-1 / AUD-3 仍 PLANNED）
```

## 2. 结构分类（非排序）

```text
适合作为 **primary P15 theme**（具备独立平台价值 + 依赖已就位）
  C-5（事件驱动闭环）· C-6（AI 能力启用）· C-8（审计深化）
  注：三者均可作为主题，但都需要先完成对应 Security/Authorization Decision

适合作为 **secondary P15 workstream**（可与主题并行、规模较小）
  C-3（engine 统一 · maintenance 级）· C-8（若主题为 C-5 则 C-8 天然并行）

适合作为 **maintenance**（不构成 P15 主题，独立于主题裁决）
  C-1（D-01 · 需 foundation 授权）· C-3（compatibility maintenance）

适合作为 **future phase**（规模/风险/依赖超出单轮，或需先有前置能力）
  C-2（管理类能力：需词表或独立 Approval 模型 ⇒ 建议在 C-5/C-6 之后）
  C-4（Bootstrap CLI：独立一次性路径 ⇒ 可独立成小轮）
  C-7（Frontend：需先明确 API 契约与产品形态）
```

## 3. 依赖与相互影响（结构事实）

```text
· C-1 与 C-3 与其他候选**无依赖**（可独立裁决）· 二者都不引入新安全边界
· C-2 是唯一可能要求 schema/词表变更的候选 ⇒ 是"schema 决策"的唯一来源
· C-4 / C-5 / C-6 都新增"执行面"（特权路径 / 后台 / 外部调用）⇒ 各自需要独立 Security Decision
· C-5 与 C-8 共享 audit_logs 与 observability 面 ⇒ 若同期推进需统一审计语义（避免两套事件语义）
· C-6 与 P10（AI gateway）决策强耦合 ⇒ 启用前须确认 provider/route/policy 冻结语义适用
· C-7 依赖 API 契约稳定（P14 已提供）⇒ 不阻塞其他候选
```

## 4. 本文件不做的判断

```text
· 不给候选排序（不输出 best/worst）
· 不推定 P15 主题（= P15-DEC-01 的 UNKNOWN，须 Human 裁定）
· 不把任何候选写成 implementation scope
```

**END OF P15 THEME ANALYSIS（2026-09-28 · 8 候选结构对比 · 未排序 · 未选主题 · HARD STOP ACTIVE）**
