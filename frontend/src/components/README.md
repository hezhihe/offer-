# components 组件边界说明

这个目录只放“展示型组件”和“通用 UI 组件”。

## 当前组件分工

| 组件 | 业务含义 | 边界 |
|---|---|---|
| `ResumeAnalysisResult.vue` | 简历分析结果展示 | 只展示结果，通过事件通知父页面保存、投递、复制、模拟面试。 |
| `ResumeDiagnosisContextCard.vue` | 简历页的求职诊断档案回流提示卡 | 只展示短板、补强线索和下一步动作，通过事件通知父页面清除上下文。 |
| `ApplicationBoard.vue` | 投递进展表 | 只展示投递记录和阶段，通过事件通知父页面更新阶段或开始模拟面试。 |
| `CareerDiagnosisCard.vue` | 求职诊断档案 | 只展示短板、线索和下一步动作，通过事件通知父页面跳转。 |
| `LoadingDots.vue` | 加载动画 | 不含业务。 |
| `ModalDialog.vue` | 弹窗壳 | 不含业务。 |
| `Toast.vue` | 提示组件 | 不含业务。 |
| `BottomNav.vue` | 底部导航 | 只负责导航展示。 |

## 禁止事项

组件里不要直接做这些事：

- 不直接调用后端 API；
- 不直接写 localStorage / sessionStorage；
- 不直接改 Pinia store；
- 不直接 router.push，除非这个组件本身就是导航组件；
- 不塞复杂业务判断。

正确方式：

```text
组件展示 props
组件点击 emit 事件
父页面处理业务动作
store 保存业务状态
api 请求后端
```