# 01_PROJECT_OVERVIEW — UAP 项目定位

## UAP 是什么

**UAP（Universal AI Platform）= 通用平台基座（platform foundation）**，业务无关的多租户 AI Agent 平台底座。

它**不是**：

- ❌ 把所有业务模块硬塞在一起的单体业务系统；
- ❌ Todo system；
- ❌ Chat system；
- ❌ Home AI assistant（那是另一条独立代码线「小智/家庭小窝」，与 UAP **代码完全隔离**）。

## 可插拔板块（未来以 Domain 形式接入）

```text
Company          企业域
Commercial       商业域
Entertainment    娱乐域
Industry custom  行业定制域
AI Gateway       AI 能力层（已建：0010_b1_6_ai_gateway）
```

板块通过 Domain 层插拔；Core 不含任何行业词汇（架构守卫 AST 强制）。

## 核心工程目标

```text
practical        实用
usable           可用
stable           稳定
reliable         可靠
privacy/security 隐私与安全（默认 deny / FAIL CLOSED）
multi-user       多用户
multi-device     多设备
pluggable        可插拔
external AI API  外部 AI API 接入能力（AI Provider = 数据行，非代码分支）
```

## 治理形态（新 Agent 必须理解的工作方式）

- 分阶段交付：PREP/DESIGN（READ-ONLY）→ Human Decision Freeze → Gate → **显式授权** → IMPLEMENTATION → GATE →（另行授权）COMMIT/TAG；
- 所有决策以 `D-<AREA>-NN` 形式冻结于 `docs/architecture/PLATFORM_DECISION_LOG.md`（append-only，禁改结论）；
- 每阶段 HARD STOP 等 Human 显式指令；证据留档于仓库外 `uap-stage3-evidence/`。

## 权威文档地图

| 主题 | 权威 |
|---|---|
| 决策 | `docs/architecture/PLATFORM_DECISION_LOG.md` |
| 架构规则 | `docs/architecture/DEPENDENCY_RULES.md` |
| 领域模型 | `docs/architecture/CORE_DOMAIN_MODEL.md` |
| OPEN-P10-1 契约 | `docs/architecture/OPEN_P10_1_IMPLEMENTATION_CONTRACT.md` |
| P13 冻结 | PDL `D-P13-01…15` + `P13_B1_HUMAN_DECISION_FINAL_DIRECTION.md` |
| 本交接包 | `docs/architecture/handoff/`（00–15 + BUNDLE） |
