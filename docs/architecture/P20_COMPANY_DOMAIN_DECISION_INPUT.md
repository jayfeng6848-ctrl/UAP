# P20 COMPANY DOMAIN DECISION INPUT（Human Decision 输入 · 未冻结）

```text
性质 = 决策输入整理（提出问题、选项与后果），**不是决策本身**
用途 = 由 Human 裁定后写入 PDL（append-only 新附录），实现轮方可开始
关联 = 每个决策标注其解除的 GAP（见 P20_COMPANY_DOMAIN_GAP_RECORD.md）
```

## 摘要表

| ID | 议题 | 建议 | 解除 |
| --- | --- | --- | --- |
| D-1 | Company 授权主体与角色授予来源 | A（platform_admin 先承担） | GAP-1 |
| D-2 | 资源投影策略（授权目标） | A（集合资源 · 与 P17 member 同型） | GAP-2 |
| D-3 | `company_*​.delete` 权限键语义 | A（永久保留 · 不映射用例） | GAP-3 |
| D-4 | `company_employee.admin` 语义 | C（保留为 reserved） | GAP-4 |
| D-5 | Employee ↔ User 绑定规则 | A（可绑可解绑 · 强校验） | GAP-5 |
| D-6 | 空间生命周期与其他分配交互 | A（仅 active 可新建 · 归档不改写既有） | GAP-6 |
| D-7 | 员工自助访问 | A（本轮不支持） | GAP-7 |
| D-8 | 审计契约细节 | A（沿用 P18 风格 · 仅成功行） | GAP-9 |
| D-9 | 列表分页与过滤契约 | A（keyset 游标 · 默认 50 / 上限 200） | GAP-8 |
| D-10 | 架构守卫与 manifest 更新授权 | A（实现轮显式修改 placeholder 守卫） | GAP-10 / GAP-11 |
| D-11 | 测试与共享库策略 | A（共享库保持冻结 · 验证脚本提升为仓库内测试） | GAP-12 / GAP-13 |

## D-1 授权主体与角色授予来源

```text
A（建议）platform_admin 承担：为 platform_admin 绑定 11 条 Company 权限（PLATFORM scope）
    · 优点：零新角色、零 P18 改动、可逆（role_permissions 追加 allow 行）
    · 代价：Company 操作在首轮只有平台管理员可执行；租户自服务需后续决策
    · 需同时定：绑定方式是"新迁移 0020 追加 role_permissions 行"（推荐，可审计、可回滚）
B 新建 tenant-scoped `company_admin` 角色：需改 P18 provisioning 语义 + 对既有 tenant 回填角色
    · 代价：触碰 P18 冻结语义（TENANT/SPACE admin 角色集合），需新决策 + 全量回归
C 扩展既有 tenant_admin / space_admin 的权限集：直接修改 P18 冻结的权限常量
    · 代价：改变既有租户管理员的权限面（安全语义变更），且既有角色需回填
D 不授予：所有 Company 用例恒 DENY（仅契约骨架可交付）

不可选项：为 Company 新建 ACL subject type / 第二授权主体（A6 禁令，禁止）
```

## D-2 资源投影策略（决定授权目标）

```text
A（建议）集合资源：每 tenant 一行 resources（resource_type = company_employee /
    company_assignment，natural_key 保留键如 `employees` / `assignments`）
    · 与 P17 `member` 集合先例同型；TENANT-scope grant 即可覆盖全 tenant
    · 代价：无实例级 ACL 粒度（"只允许某员工读某条"不可表达）
B 集合 + 实例资源：额外为每个对象建 resources 行（resource id = 对象 id，P16 agent 先例）
    · 优点：实例级 ACL 可用；代价：每条写路径都要维护投影行 + 失败即回滚
C 仅 pre-resource（resource=None）：仅 PLATFORM scope 可用
    · 代价：所有 Company 操作都必须是平台级授权；无法表达租户级授权

说明：三选项都不改变 11 条权限行与 resource_type 名（已冻结），因此本项可后续升级（A → B），
      升级代价限于投影行回填，不影响权限词表。
投放路径（若选 A/B）：投影必须在与业务写入同一事务内完成（P3），沿用既有
      `uap_runtime` resources INSERT/UPDATE 权限，不需要新 GRANT。
```

## D-3 / D-4 保留权限键的语义

```text
D-3 company_employee.delete · company_assignment.delete
  A（建议）永久保留为 reserved：不映射任何用例；在契约中显式标注"不使用"
      · 代价：11 条权限行中 2 条长期闲置（诚实登记，不静默映射）
  B 映射到"终止 / 结束"：语义重叠（delete 与 update 混用），易被误读为可物理删除
  C 删除这些权限行：需要新迁移改写 0019 冻结产物 + 新决策

D-4 company_employee.admin
  A 覆盖生命周期转换（C4–C6 改用 admin 动作）
  B 覆盖 user 链接/解绑（C3 改用 admin 动作）
  C（建议）保留为 reserved，生命周期统一走 `update`
      · 理由：与 D-P20S-04 生命周期由状态变更驱动的语义一致，且不需要区分两套管理动作
```

## D-5 Employee ↔ User 绑定规则

```text
A（建议）可绑定、可解绑，且强校验：
    · 绑定前校验 users 行存在且 status = active（否则 EMPLOYEE_USER_CONFLICT）
    · 解绑 = user_id 置 NULL（历史事实保留在审计中）
    · 绑定**不产生任何授权**（Employee ≠ User 在授权层同样成立，F4）
B 只允许绑定（不允许解绑）：历史更简单，但操作不可逆
C 本轮完全不做绑定用例（C3 推迟到后续轮次）
```

## D-6 空间生命周期与分配的交互

```text
A（建议）仅 active 空间可新建分配；空间归档/删除不自动改写既有分配（保留历史事实）
    · 与 P18 生命周期由控制面驱动的冻结语义一致
B 空间归档时自动 end 既有 active 分配
    · 代价：控制面操作产生跨域副作用（P18 需感知 Company 域数据）
C 不做空间状态校验
    · 代价：可向 archived/deleted 空间建立新分配，弱化结构隔离语义
```

## D-7 员工自助访问（self-service）

```text
A（建议）本轮不支持：员工不是授权主体，自助读取需后续决策
    · 理由：当前引擎无法表达 SELF 谓词（F11）；强行实现将引入第二授权语义
B 通过 ACL（resource_permissions）逐资源授予：需要实例资源投影（D-2=B）与授权管理面
C 扩展授权引擎（策略/授予加入谓词）：影响面最大，需评估对既有 P13–P18 决策的冲击
```

## D-8 审计契约细节

```text
A（建议）沿用 P18 风格：
    · action 族 = company_employee.* / company_assignment.*
    · 仅记录成功变更（result=success）；risk_level = LOW（生命周期/终止 = MEDIUM）
    · 拒绝/失败不落 audit_logs（由运行时日志承担，避免把审计表变成请求日志）
B 额外记录被拒绝的授权尝试（result=denied）
    · 代价：审计表写入量显著上升；需要明确"授权拒绝审计"的保留策略
```

## D-9 列表分页与过滤契约

```text
A（建议）keyset 游标（(created_at, id) 降序）· 默认 limit = 50 · 上限 200
    · 过滤：employees（status / employee_no 前缀）· assignments（employee_id / space_id / status）
    · 非法 limit/游标 ⇒ PAGINATION_INVALID（不返回部分结果）
B offset 分页：实现更简单，但在并发写入下会跳行/重复
```

## D-10 架构守卫与 manifest 更新授权

```text
A（建议）实现轮显式修改 `test_domain_manifests_are_placeholders`：
    · 由"所有域必须 placeholder"改为"白名单已实现域 + 其余仍为 placeholder"
    · 并在同一轮更新 domains/company/manifest.py（tables 列 2 张表 · permissions 使用 canonical key）
B 不修改域 manifest、仅走 services/company：守卫不变，但 `domains/company/` 将长期与事实不同步
注意：该守卫是既有冻结测试，修改它需 Human 明确授权（不得静默放宽）
```

## D-11 测试与共享库策略

```text
A（建议）共享测试库 uap_b1_test 保持 0017_p13_seed 冻结；Company 测试使用一次性隔离库；
    并将 `.p20verify/verify_0019_retry.py` 提升为仓库内 migration 测试（§14 允许）
B 将共享测试库迁移到 0019：使 Company 表在共享库可用，但改变既有冻结基线
C 两者都做：需先 A 后 B，并单独记录基线变更
```

## 决策后仍不可自动进行的事项

```text
* 实现 Domain / 用例 / 仓储（需新的实现授权指令）
* API / UI / Worker / 事件（A7 / P19-D01 未变）
* commit / tag / push（仍受 HARD STOP 约束）
```

**END OF P20 COMPANY DOMAIN DECISION INPUT（11 项决策输入 D-1…D-11 · 每项含选项、代价与建议 · 未作任何裁定；2026-10-02）**
