# P20 COMPANY API DECISION INPUT（Human Decision 输入 · 已裁定）

```text
性质 = 决策输入整理（问题 / 选项 / 代价 / 建议）
状态 = 已裁定 · 冻结于 PDL 附录 AG（D-P20A-01…08）
```

## 裁定结果（附录 AG）

| ID | 裁定 | 冻结表述 |
| --- | --- | --- |
| D-API-01 | **B** | tenant_id 显式进入 path（tenant boundary = API path boundary） |
| D-API-02 | **A** | 沿用既有错误 taxonomy（validation → 422） |
| D-API-03 | **A** | 仅 limit + 已冻结过滤能力（禁 cursor / DSL / 动态排序） |
| D-API-04 | **A** | 跨租户 / 未投影 / 未授权统一 403 |
| D-API-05 | **A** | Company namespace 独立错误映射（不污染 Core taxonomy） |
| D-API-06 | **C** | 显式 DTO whitelist（Database Schema ≠ API Contract） |
| D-API-07 | **A** | V1 create 统一 201 |
| D-API-08 | **A** | 同步 route manifest guard |

## 摘要

| ID | 议题 | 建议 | 关联 |
| --- | --- | --- | --- |
| D-API-01 | tenant 作用域位置（端点形状） | B：tenant 入 path | G-API-01 |
| D-API-02 | not-found HTTP 状态 | A：沿用既有 taxonomy（422） | G-API-02 |
| D-API-03 | 分页与过滤面 | A：仅 limit + 既有过滤 | G-API-03 / G-API-10 |
| D-API-04 | 跨租户/未投影的对外语义 | A：统一 403（P17 口径） | G-API-05 |
| D-API-05 | 错误映射注册方式 | A：Company 命名空间内新增映射项 | G-API-04 |
| D-API-06 | 响应暴露面 | C：显式 DTO 白名单 | G-API-06 |
| D-API-07 | 幂等重放的 HTTP 表达 | A：V1 一律 201（不新增 service 标志） | G-API-08 |
| D-API-08 | 路由清单守卫同步 | A：实现轮同步更新断言 | G-API-09 |

## D-API-01 tenant 作用域位置

```text
A 形態：`/company/employees`（指令原提案）+ 另定上下文规则
   代价：tenant 必须来自 session/header/查询参数之一；与 P17 §44「目标作用域来自 path」冲突，
        且引入"上下文来源"的新语义（需额外决策与守卫）
B（建议）形态：`/company/tenants/{tenant_id}/employees`（tenant 入 path）
   优点：与 F2 及 P18 `/control/tenants/{tid}/spaces/{sid}` 完全一致；无新语义；
        跨租户访问天然变成"tenant 不可见"而由 use case 拒绝
   代价：路径更长；与指令示例字面不同（语义等价）
```

## D-API-02 not-found 的 HTTP 状态

```text
A（建议）沿用既有 taxonomy：EMPLOYEE_NOT_FOUND / ASSIGNMENT_NOT_FOUND → validation → 422
   优点：零全局改动；与 P18 的 TENANT_NOT_FOUND/SPACE_NOT_FOUND 行为一致
   代价：语义上 422（不可处理实体）用作"未找到"，不如 404 直观
B 在 Company 命名空间引入 404
   代价：需扩展全局 HTTP_STATUS/taxonomy（或为 Company 单开映射分支），
        与 P17/P18 的既有行为不一致 → 需说明为何 Company 例外
C 全局统一改为 404（所有 not-found 类）
   代价：影响 P17/P18 既有 API 行为与既有测试 → 属平台级变更，超出 Company 范围
```

## D-API-03 分页与过滤面

```text
A（建议）V1 仅暴露已实现能力：`limit`（1..200 · 默认 50）+ 既有过滤
   employees：status；assignments：employee_id / space_id / status
   优点：**最小必要 API 面**；无需改动 service（本轮与实现轮都不新增查询能力）
   代价：无游标 → 大集合只能取前 N 条（V1 可接受；真实分页需新授权 + service 改动）
B 暴露 cursor：需先给 service 增加游标语义（keyset on (created_at,id)）→ 属新授权与代码改动
C 暴露 offset：实现简单但并发下跳行/重复，与"最小必要"冲突
```

## D-API-04 跨租户 / 未投影的对外语义

```text
A（建议）统一 403：未授权、未投影、跨租户不可见一律 403（P17 §40/§46 口径）
   优点：不泄露存在性；与既有平台行为一致
   代价：调用方无法区分"无权限"与"不存在"（这是刻意的）
B 区分：不可见 → 404；未投影 → 403
   代价：需要 D-API-02 选 B/C 才成立；且泄露"存在但不能访问"的信息
```

## D-API-05 错误映射注册方式

```text
A（建议）在 apps/api/error_mapping.py 内为 CompanyError 新增一个 _P20_STATUS 映射表 +
   classify() 分支（与 P18 的 _P18_STATUS 同型）
   优点：最小改动、模式一致、可审计
B 扩展全局 taxonomy 类（新增 not_found / provision 等）
   代价：影响面大，需评估 P17/P18 回归
```

## D-API-06 响应暴露面

```text
A 返回完整数据库行
   代价：把存储细节暴露为 API 契约；未来加列即隐式扩面，且 user_id/title 等字段无差别暴露
B "authorization-filtered view"（按授权逐行/逐字段过滤）
   事实：V1 授权为租户集合级（无实例资源、无 ACL）→ **当前引擎无法表达逐行过滤**；
        若要实现需新的授权语义决策（高成本）
C（建议）显式 DTO projection：冻结字段白名单（§CONTRACT §4），tenant_id 与 user_id 均显式声明
   优点：契约稳定、隐私可控、与"最小必要"一致；不需要新授权机制
   代价：新增字段需新决策（这正是期望的约束）
```

## D-API-07 幂等重放的 HTTP 表达

```text
A（建议）V1 一律 201；重放返回同一实体但状态码不变（不区分）
   优点：不需要 service 暴露重放标志（零改动）
   代价：客户端无法区分"新建"与"重放"
B 区分 200/201：需 service 返回 replayed 标志（新授权 + 代码改动）
```

## D-API-08 路由清单守卫

```text
A（建议）实现轮同步更新 P17 的 frozen route inventory 断言，把 /company/* 11 条纳入清单
   优点：与既有守卫风格一致，防止意外新增端点
B 不更新守卫 → Company 路由不在断言范围内（容易出现未审计端点扩散）
```

## 决策后仍不可自动进行的事项

```text
* API 实现（router / DTO / error mapping 注册 / API 测试）
* UI / Worker / Event
* commit / tag / push
* 任何 service / domain / schema / permission 变更（如需分页游标或重放标志 → 另立授权）
```

**END OF P20 COMPANY API DECISION INPUT（8 项决策输入 D-API-01…08 · 每项含选项、代价与建议 · 未作任何裁定；2026-10-02）**
