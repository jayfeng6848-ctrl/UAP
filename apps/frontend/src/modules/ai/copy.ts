/**
 * Customer-facing AI copy — Simplified Chinese default (HD-P21-18 · HD-P21-AI-04).
 *
 * Deliberately a plain constant module, not an i18n framework: this round only
 * freezes zh-CN for the customer AI UI. Brand and necessary technical names
 * (UAP · AI · API Key) stay as they are. The customer sees 服务/模型/连接 — never
 * adapter, protocol, endpoint or secret terms.
 */

export const AI_COPY = {
  // entry / page chrome
  entryResolving: '正在打开 AI 助手…',
  entryNoWorkspace: '暂时无法确定工作空间。请先在 UAP 中打开一个工作空间，然后再进入 AI。',
  entryFailed: '暂时无法确定工作空间。请稍后重试。',
  pendingTenant: '正在准备工作空间…',
  pageTitleAssistant: 'UAP AI 助手',
  pageTitleConnect: '连接 AI',

  // home / first use
  homeTitle: 'AI 助手',
  homeDescription: '连接你的 AI 服务，然后直接用自然语言提问。',
  checking: '正在检查 AI 连接…',
  welcomeTitle: '连接 AI',
  welcomeBody: '连接您的 AI 服务后，UAP 就可以开始帮助您处理工作。',
  startConnect: '开始连接',
  statusConnected: 'AI 已连接',
  statusDisconnected: 'AI 未连接',

  // stepper (HD-P21-AI-04 §18)
  stepProviderTitle: '选择 AI 服务',
  stepProviderDescription: '选择您要使用的 AI 服务。云端服务需要 API Key，本机服务直接使用。',
  stepModelTitle: '选择模型',
  stepModelDescription: '以下模型来自该 AI 服务当前可用的列表。',
  stepCredentialTitle: '输入必要信息',
  stepCredentialDescription: '完成最后一步，就可以开始使用 AI。',
  groupCloud: '云端 AI',
  groupLocal: '本地 AI',
  selectedLabel: '已选择：',
  back: '返回',
  next: '下一步',

  // models
  modelLoading: '正在获取模型列表…',
  modelEmpty: '该服务当前没有可用模型。',
  modelChoose: '选择模型',
  localDetecting: '正在检测本机 AI 服务……',
  localNone: '未检测到本地 AI',
  localUnavailable: '未检测到本地 AI。请先在这台电脑上启动该服务，然后再试。',
  localAvailableCount: '本机可用模型',

  // credential step
  keyLabel: 'API Key',
  keyHint: '请输入您的 API Key。它只用于本次连接，不会保存到浏览器。',
  keyRequired: '请输入您的 API Key。',
  tokenLabel: '本地访问令牌',
  tokenHint: '该本地服务需要访问令牌。它只用于本次连接，不会保存到浏览器。',
  keyShow: '显示',
  keyHide: '隐藏',
  keyHelp: '在哪里获取 API Key？请在你的 AI 服务账号页面创建。',
  enable: '一键启用 AI',
  enableLocal: '使用本地 AI',
  cancel: '取消',
  connecting: '正在连接 AI…',

  // success
  successTitle: 'AI 已准备好',
  successBody: '现在你可以直接和 UAP 说话。',
  successExampleLabel: '例如：',
  successExample: '“告诉我研发团队现在有多少人在职。”',
  startUsing: '开始使用 AI',

  // errors (customer language only; technical codes stay internal)
  errorInvalidKey: 'API Key 无法使用。请检查 API Key 是否正确，然后重新尝试。',
  errorKeyRequired: '请输入您的 API Key。',
  errorModelUnavailable: '这个模型当前不可用，请重新选择模型。',
  errorLocalAuthRequired: '本机 AI 服务需要访问令牌，请输入后再试。',
  errorLocalModelMissing: '这个模型在本机已经不可用，请重新选择模型。',
  errorLocalUnavailable: '暂时无法连接本机 AI 服务。请确认本机服务已启动。',
  errorLocalProtocol: '本机 AI 服务返回了不兼容的响应，已停止本次连接。',
  errorNoCredentialTitle: 'AI 还没有连接',
  errorNoCredentialBody: '请先连接 AI 服务。',
  errorNoCredentialAction: '连接 AI',
  errorNetwork: '暂时无法连接 AI 服务。请检查网络后重试。',
  errorReconnect: '重新连接',
  errorConfig: 'AI 暂时无法启用。请稍后重试。',
  errorRetry: '重试',

  // assistant
  assistantTitle: 'AI 助手',
  assistantDescription: '你可以直接告诉我你想做什么。',
  assistantGreeting: '你好，我已经准备好了。你可以直接告诉我你想做什么。',
  questionLabel: '你的问题',
  questionPlaceholder: '请输入你想让我帮你做的事情…',
  send: '发送',
  sending: '正在处理…',
  answerFallback: '我已经完成这次查询。',
  assistantUnavailable: 'AI 暂时无法回答。请稍后重试。',
  authorizationDenied: '你没有查看这部分数据的权限。',
  expired: 'AI 连接已过期。请重新连接 AI 服务。',
  emptyTitle: '还没有对话',
  emptyBody: '你可以直接告诉我你想完成什么。',
  emptyExample: '例如：“帮我看看研发团队有哪些员工。”',

  // advanced details (collapsed by default)
  advancedSummary: '高级详情',
  advancedProviderLabel: 'AI 服务',
  advancedModelLabel: '模型',
  advancedStatusLabel: '连接状态',
  advancedSecurityLabel: '安全状态',
  advancedConnected: '已连接',
  advancedDisconnected: '未连接',
  advancedSecurityOk: '正常',
  providerPrimary: 'OpenAI',
  clearButton: '清除 AI 连接',
  clearDialogTitle: '确定要断开 AI 连接吗？',
  clearDialogBody: '清除后，需要重新输入 API Key。',
  clearDialogConfirm: '确定',
  cleared: 'AI 已断开',
  reconnect: '重新连接 AI',
} as const;

export type AiCopy = typeof AI_COPY;
