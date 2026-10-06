# P20 COMPANY API PREP（只读勘察 + 契约设计输入）

```text
阶段     = P20 COMPANY API AUTHORIZATION PREP（设计阶段产出 · 不实现）
状态     = FROZEN · PDL 附录 AG（D-P20A-01 = B / 02 = A / 03 = A / 04 = A / 05 = A / 06 = C / 07 = A / 08 = A）
基线     = UAP-V0.1.17-P18-CONTROL-PLANE（08a0485b）+ PDL 附录 AF + 0019 + 0020 + P20 DOMAIN ACCEPTANCE = PASS
本轮禁止 = FastAPI router / endpoint / DTO / request model / response model / API 测试 /
           app startup / authentication middleware / authorization engine / migration / schema /
           permission / role grant / resources 数据 / commit / tag / push
产物     = 本文件 + 4 份配套（CONTRACT · MATRIX · GAP_RECORD · DECISION_INPUT）
```

## 1. Phase 0 — 基线（只读实测）

```text
P20 DOMAIN ACCEPTANCE = PASS（acceptance report 存在 · Company 测试 26 passed · 架构守卫 63 passed）
0019_p20_company            sha256 3F4767B9CBA7550C4676F783222C69AEB23DCDCFA6CB678231C2332C756828F0（未变）
0020_p20_company_authorization sha256 22B6EE611CDD4281CD1BE892F6D8716FE7EA8E26BA41E21DE41EC9BC20588CA4
API code（Company）= 0（`rg -i company apps/` 无任何命中）
Company router      = 0（routes/ 下无 company 模块；main.py 未注册）
events = 0 · handlers = 0 · producers = 0（allowlist EMPTY）
workers = 0（Company 无 worker；apps/worker 仅 P15 consumer kernel，与本轮无关）
git = HEAD 08a0485b · staged = 0 · 未 commit / tag / push
⇒ 系统当前没有任何 Company API（确认）
```

## 2. API 层既有约定（契约必须遵循的实测事实）

```text
F1  Transport-only handler：认证 actor → 调用**一个** use case → 映射结果；handler 内无 SQL、
    无角色比较、无 is_admin 捷径（P18 control-plane / P17 identity-runtime 同型）
F2  **目标作用域来自 path，绝不来自 session / header / 首行猜测**（P17 §44 明文）
F3  错误统一走 apps/api/error_mapping.py：classify() → 八类 taxonomy → translate() 出 HTTP；
    安全类（persistence / security_boundary / connection / transaction）= 503 模糊化，
    绝不泄露数据库名 / 角色名 / SQL / 连接串
F4  请求体 = pydantic BaseModel + Field 约束；响应 = 普通 dict（UUID/datetime 经 _clean 序列化）
F5  列表响应封装 = {"items": [...], "count": n}（**当前无 cursor / offset 分页先例**）
F6  router 在 apps/api/main.py 显式注册；已有路由清单守卫先例
    （tests/integration/test_p17_acceptance.py::test_api_route_inventory_matches_the_frozen_scope）
F7  API 层不参与授权判定：授权在 use case 内经 canonical AuthorizationService 完成
F8  P17 的 DELETE 端点仅用于成员移除（状态变更），并非物理删除；Company V1 无删除语义
F9  Company use case 需要 **runtime identity**（`get_database` → uap_runtime），
    而非 P18 的 control identity（`get_control_database` → uap_control）
F10 既有 router = 8 个（health · meta · identity · identity_runtime · devices · sessions ·
    agent_runs · control_plane）；命名空间先例：P18 用专用 `/control/...` 前缀
F11 认证入口 = services.use_cases.authenticate_actor(bearer session)；返回 actor（user_id / subject_type）
F12 Employee ≠ User：员工**不是**认证主体，不得用员工身份登录（本阶段亦禁止新增登录体系）
```

## 3. 本轮设计范围

```text
覆盖 = 11 个已实现 use case 的 HTTP 暴露设计（employee 6 + assignment 5）
不含 = API 实现 · OpenAPI 生成 · UI · Worker · Event · 新的认证或令牌体系
重点 = ① 端点与作用域形状 ② 授权映射 ③ 响应暴露面 ④ 错误契约 ⑤ 分页/过滤最小面
      ⑥ 认证边界 ⑦ 事件边界
```

## 4. 交付物索引

```text
docs/architecture/P20_COMPANY_API_PREP.md            ← 本文件（基线 + 既有约定）
docs/architecture/P20_COMPANY_API_CONTRACT.md        ← API 契约设计（端点 / 请求响应 / 错误 / 边界）
docs/architecture/P20_COMPANY_API_MATRIX.md          ← endpoint × use case × permission × audit 矩阵
docs/architecture/P20_COMPANY_API_GAP_RECORD.md      ← 缺口登记（含需 Human Decision 项）
docs/architecture/P20_COMPANY_API_DECISION_INPUT.md  ← 决策输入（选项 / 代价 / 建议）
```

## 5. 本轮未做（边界声明）

```text
未创建/修改任何 Python 代码（apps/** · services/** · domains/** 零改动）·
未创建 router / endpoint / DTO / request·response model / API 测试 ·
未修改 app startup / authentication middleware / authorization engine ·
未修改 migration / schema / permission / role grant / resources 数据 ·
未 commit / tag / push
```

**END OF P20 COMPANY API PREP（基线：Company API 代码 = 0 · 12 项 API 层既有约定 F1–F12 · 5 份设计交付物 · 未实现；2026-10-02）**
