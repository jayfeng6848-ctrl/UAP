# P20 COMPANY DOMAIN GAP RECORD（只读勘验登记 · 未修复）

```text
性质 = 缺口登记（不修复、不实现）；每条含证据、影响、分类
分类 = BLOCKING（阻断实现轮）· DECISION-REQUIRED（需 Human 裁定）· NON-BLOCKING（不阻断）
基线 = 0019_p20_company ACCEPTED · 共享库 uap_b1_test = 0017_p13_seed
```

## 1. 阻断实现轮的缺口

```text
GAP-1 [BLOCKING] 角色授予为 0 ⇒ 无任何主体能通过 Company 授权
  证据：验收报告 company_role_grants = 0；P18 冻结的 TENANT_ADMIN_PERMISSIONS =
        (member.read, member.admin, tenant.admin)、SPACE_ADMIN_PERMISSIONS =
        (space.admin, member.read, member.admin)；platform_admin 仅有 12 条平台权限。
  影响：即使写出全部用例，任何调用都会得到 DENY（默认拒绝 + 无 grant）。
  需要：授权主体与角色授予模型（DECISION_INPUT D-5）。

GAP-2 [BLOCKING] 资源投影策略未定 ⇒ 授权目标不可确定
  证据：canonical 授权要求被治理对象在 resources 有行（F1/F2）；0019 未创建任何 resources 行；
        全仓无 company_* 投影代码。
  影响：instance 级授权、ACL、list 目标均无法确定；缺失投影将导致 DENY 而非报错。
  需要：D-2（集合资源 / 实例资源 / pre-resource）。
```

## 2. 需要 Human 裁定的语义缺口

```text
GAP-3 [DECISION-REQUIRED] company_employee.delete / company_assignment.delete 的语义
  证据：0019 冻结了这两条权限行（action=delete），但 D-P20S-09 规定无物理删除；
        runtime 亦无 DELETE 权限（验收实测 DENIED）。
  选项：① 永久保留为 reserved（永不映射用例）② 映射到"终止/结束"（语义重叠但可解释）
        ③ 未来由新决策移除（需要迁移，且本次 11 条冻结）
  影响：3 条权限行中的 2 条当前无用例（用例矩阵覆盖率 8/11）。

GAP-4 [DECISION-REQUIRED] company_employee.admin 的语义
  证据：AD 冻结了该权限键，但无对应决策说明 admin 覆盖哪些操作。
  选项：① 覆盖生命周期转换（suspend/terminate）② 覆盖 user 链接/解绑 ③ 保留为 reserved
  影响：若 admin 覆盖生命周期，则 C4–C6 的动作应从 update 改为 admin（需一次性裁定）。

GAP-5 [DECISION-REQUIRED] Employee ↔ User 绑定语义（user_id 可空）
  证据：0019 中 user_id 可空 + 部分唯一 (tenant_id, user_id)；AD 未定义绑定/解绑规则。
  需定：写入前是否要求目标 user 存在且 active；是否允许改绑（换人）；是否允许解绑；
        绑定是否产生任何授权（本提案：不产生，F4）。
  影响：C3 的前置条件与错误码（EMPLOYEE_USER_CONFLICT）未定。

GAP-6 [DECISION-REQUIRED] 空间生命周期与分配的交互
  证据：P18 冻结 spaces 生命周期（active → archived → deleted）；0019 未约束 space 状态；
        既有分配不随空间归档自动改写。
  需定：能否向 archived/deleted space 新建分配；空间归档时既有 active 分配是否自动 end；
        是否禁止给 archived space 的员工继续写入。
  影响：C7 前置条件与"归档空间"边界测试。

GAP-7 [DECISION-REQUIRED] 员工自助访问（self-service）
  证据：SELF / RESOURCE 是上下文谓词（core.permission.vocabulary），但服务层 Grant 无谓词字段、
        PolicyRule 也无谓词字段 ⇒ 当前引擎无法表达"员工读自己的记录"（F11）。
  选项：① 本轮不支持自助（推荐，零新机制）② 通过 ACL（resource_permissions）逐资源授予
        ③ 扩展策略/授予模型（需要新的授权语义决策，风险最高）
```

## 3. 不阻断、但需在实现轮明确记录的缺口

```text
GAP-8  [NON-BLOCKING] list 语义未定：分页形状（cursor/limit）、排序键、过滤字段、最大页大小
GAP-9  [NON-BLOCKING] 审计细节未定：action 命名族（company_employee.*）、risk_level 取值、
       拒绝/失败是否落审计行
GAP-10 [NON-BLOCKING] 架构守卫冲突：test_domain_manifests_are_placeholders 断言所有域
       status=placeholder 且 tables=[]；Company 落地实体轮必须显式授权修改该守卫（DEPENDENCY_MAP §4 W1）
GAP-11 [NON-BLOCKING] domains/company/manifest.py 声明 tables=[]、permissions 为占位字符串，
       与 0019 已建 2 表的事实不同步（属实现轮范围）
GAP-12 [NON-BLOCKING] 共享测试库 uap_b1_test 仍为 0017_p13_seed（未迁移 0019）；
       Company 表仅在一次性验证库与未来迁移库中存在
GAP-13 [NON-BLOCKING] 无仓库内 P20 测试；0019 的验证脚本位于仓库外
       （.p20verify/verify_0019_retry.py）——是否提升为仓库内测试待裁定
GAP-14 [NON-BLOCKING] API / Worker / 事件全部未授权（本阶段与实现轮均不含）
       —— 事件侧维持 A7 / D-P20S-15 / P19-D01 OPTION D（Allowlist EMPTY）
GAP-15 [NON-BLOCKING] 员工/分配是否进入 resources 后使用何种 classification
       （默认 INTERNAL）与 owner_id（是否取 user_id）未定 —— 与 D-2 同批裁定
```

## 4. 当前无冲突项（已核对）

```text
* 0019 结构满足 AD/AE（验收 10/10 PASS），域契约无需 schema 变更
* Core → Domain = 0 可保持（DEPENDENCY_MAP §6 D1）
* 无新增 canonical action / ACL subject type / 角色（本阶段零授权变更）
* 现有 uap_runtime 权限面已覆盖契约所需表（F7），无需新 GRANT
```

**END OF P20 COMPANY DOMAIN GAP RECORD（2 项 BLOCKING + 5 项 DECISION-REQUIRED + 8 项 NON-BLOCKING · 未修复、未实现；2026-10-02）**
