# Struts2 路由参考

只在项目存在 Struts2 filter、`struts.xml`、`struts-*.xml`、Action 类或 `struts2-core` 依赖时读取本文件。

## 必查配置

- `WEB-INF/web.xml` 中的 `StrutsPrepareAndExecuteFilter` 或旧版 FilterDispatcher。
- `struts.xml` 和所有被 `<include file="...">` 引入的配置。
- `struts-*.xml`、插件配置、package 继承。
- `struts.action.extension`，默认常见为 `action`，也可能为空或多个扩展。

## URL 组成

```text
context-path + package namespace + action name + extension
```

`namespace="/"` 表示根 namespace。扩展为空时不要强行加 `.action`。

## 普通 action

对每个 `<action>` 输出：

- URL。
- class。
- method，未配置时通常是 `execute`，但需结合 DMI/通配符确认。
- result 不作为路由，但可帮助识别返回类型。
- 参数来自 Action 字段、setter、ModelDriven 对象和父类字段。

## 通配符 action

遇到以下模式必须展开：

- `name="*_*"`
- `name="user_*"`
- `name="*"`
- class 或 method 中出现 `{1}`、`{2}`。

处理步骤：

1. 根据 namespace 和 class 模板定位候选 Action 类。
2. 反编译或读取 Action 类 public 业务方法。
3. 排除 getter/setter、`validate`、`input`、继承自框架的通用方法。
4. 输出一个“模式族”头部，再逐行列出全部实际 URL 到方法映射。
5. 模式族中的实例数量计入总接口数。

## 动态方法调用

如果启用 DMI 或 URL 支持 `action!method.action`：

- 检查 `struts.enable.DynamicMethodInvocation`。
- 识别可被调用的 public 业务方法。
- 将每个可达 method 作为独立入口或实例列出。

## 参数来源

| 模式 | 参数来源 |
|------|----------|
| 普通 Action 字段 | setter 或字段名 |
| `ModelDriven<T>` | model 类型字段 |
| 嵌套对象 | OGNL 对象图，如 `user.name` |
| 文件上传 | `File`, `fileName`, `contentType` 三元字段 |
| 父类字段 | 读取公共基类和抽象 Action |

## 不要误列

- getter/setter 本身不是 action method。
- `ActionSupport` 继承方法不是业务入口。
- result JSP 不是新的 HTTP route。

## Gotchas

- 只列 `<action name="*_*">` 模板是失败输出，必须列实例。
- 多个 package 继承同一 namespace 时要合并配置，不要覆盖。
- 同名 action 在不同 namespace 是不同入口。
- 参数可能只存在父类或 ModelDriven 类型中。
