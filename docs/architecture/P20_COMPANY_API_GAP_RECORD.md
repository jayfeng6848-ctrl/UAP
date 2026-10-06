# P20 COMPANY API GAP RECORD（设计缺口登记 · 不现场解决）

```text
性质 = 缺口/未决登记（本文件不设计定案、不实现、不修改任何代码）
依据 = P20 COMPANY API PREP 的 F1–F12 + API CONTRACT 提案 + 已实现 service 的事实
分类 = BLOCKING（阻断 API 实现设计定案）· DECISION-REQUIRED（需 Human 裁定）· OBSERVATION
```

## 1. 阻断性缺口

```text
G-API-01 [BLOCKING] tenant 作用域在端点形状中的位置
  事实：本门指令提案为 `/company/employees`（无 tenant）；P17 §44 明文规定"目标作用域来自 path，
       绝不来自 session/header"；P18 先例为 `/control/tenants/{tenant_id}/spaces/{space_id}`。
  影响：若不把 tenant 放入 path，则必须由 session/header 推断 tenant → 与 F2 冲突；
       若放入 path，则端点形状与本门指令示例不同（语义等价、路径不同）。
  需：D-API-01 裁定（形态 A + 显式上下文规则 / 形态 B 路径化）。

G-API-02 [DECISION-REQUIRED] not-found 的 HTTP 状态
  事实：既有 taxonomy 无 404 —— P18 把 TENANT_NOT_FOUND/SPACE_NOT_FOUND 映射为 validation(422)。
       本门指令示例把 EMPLOYEE_NOT_FOUND 定为 404。
  影响：是否在 Company 命名空间引入 404（局部新语义）或沿用 422（全局一致）。
  需：D-API-02。
```

## 2. 需裁定或确认的设计项

```text
G-API-03 [DECISION-REQUIRED] 分页
  事实：已实现 service 仅支持 `limit`（1..200），无 cursor/offset；F5 先例为 {items,count}。
  选项：V1 仅暴露 limit（最小面） / 需要 cursor（须先改 service = 新授权）
  需：D-API-03（并说明是否接受"无游标"的列表语义）。

G-API-04 [DECISION-REQUIRED] 错误映射注册
  事实：apps/api/error_mapping.py 尚未注册 services.company.CompanyError；
       不加映射会被归入 "internal"(500)。
  影响：实现轮必须新增映射（属代码改动，本轮禁止）。
  需：D-API-05 确认映射归属（Company 命名空间内新增 vs 扩展全局 taxonomy）。

G-API-05 [DECISION-REQUIRED] 跨租户与未投影的对外语义
  事实：P17 把"未授权/未投影/不可见"统一为 403（不区分），避免存在性泄露；
       Company service 在跨租户时返回 *_NOT_FOUND（不泄露存在性），未投影返回 RESOURCE_NOT_PROVISIONED。
  选项：统一 403（P17 口径） / 区分 404 与 403（信息更细但暴露面更大）
  需：D-API-04。

G-API-06 [DECISION-REQUIRED] 响应暴露面（Phase 4 A/B/C）
  事实：V1 授权为租户集合级（无实例资源、无 ACL），因此**不存在**按行过滤的授权机制；
       可使用的是显式 DTO 白名单。
  选项：A 返回完整行（含全部字段） / B "授权过滤视图"（当前引擎无法表达逐行过滤） /
       C 显式 DTO projection（冻结字段白名单）
  需：D-API-04 相关裁定（本文件与 DECISION_INPUT 的 D-API-06）。

G-API-07 [OBSERVATION] 审计 action 命名口径
  事实：本门指令矩阵示例写 `employee.created`；已实现并已验收的审计口径为
       `company_employee.create` / `.update` / `.suspend` / `.terminate` 与
       `company_assignment.create` / `.update` / `.end`。
  处置：API 层不自行命名审计 action（审计由 use case 写），MATRIX 采用已实现口径。
       若需改口径 → 需新决策 + service 改动（不在本轮）。

G-API-08 [OBSERVATION] 幂等重放的 HTTP 表达
  事实：service 的 create 在完全一致重放时返回同一实体（内部幂等），但**未**返回 replayed 标志；
       初判与唯一契约键不同则抛 409。
  影响：API 无法区分"首次创建(201)"与"重放(200)"，当前一律 201。
  处置：登记为观察项；若需 200/201 区分则要 service 暴露重放标志（新授权）。

G-API-09 [OBSERVATION] 路由清单守卫
  事实：P17 有 frozen route inventory 断言；Company 新增路由必须同步该断言（实现轮）。
  处置：实现轮清单项（属代码改动）。

G-API-10 [OBSERVATION] assignment 列表过滤面
  事实：service 支持 employee_id / space_id / status 过滤；本门指令未明确是否全部暴露。
  处置：建议按"最小必要"暴露（DECISION_INPUT D-API-03）。
```

## 3. 已核对无冲突项

```text
* 11 个 use case 与 11 个端点一一对应（无遗漏、无多余；delete/admin 无端点）✓
* Company use case 需要 runtime identity（get_database）而非 control identity ✓
* API 不参与授权判定；无 is_admin 捷径 ✓（设计与既有先例一致）
* Employee ≠ User：员工不是认证主体；无员工登录/自助端点 ✓
* 事件边界：API 不发布事件；events/handlers/producers = 0 保持 ✓
* 本轮零代码改动：api code（company）= 0 仍成立 ✓
```

**END OF P20 COMPANY API GAP RECORD（2 BLOCKING/需裁 · 4 需确认 · 4 观察 · 3 项已核对无冲突 · 未实现；2026-10-02）**
