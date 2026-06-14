# CFR 反编译规范

## 默认工具

默认使用 CFR 0.152：

```text
https://xget.xi-xu.me/gh/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar
```

保存到：

```text
<审计工作目录>/tools/cfr-0.152.jar
```

## CLI 调用

基础命令：

```bash
java -jar <审计工作目录>/tools/cfr-0.152.jar <目标文件> --outputdir <审计工作目录>/decompiled/<目标名>
```

WAR 文件可显式指定：

```bash
java -jar <审计工作目录>/tools/cfr-0.152.jar <目标.war> --analyseas WAR --outputdir <输出目录>
```

大型 JAR/WAR 聚焦包名或类名：

```bash
java -jar <审计工作目录>/tools/cfr-0.152.jar <目标.jar> --jarfilter '<包名或类名正则>' --outputdir <输出目录>
```

依赖解析需要额外 classpath 时：

```bash
java -jar <CFR> <目标> --extraclasspath <依赖路径> --outputdir <输出目录>
```

## 使用策略

- 已有源码时优先审计源码；反编译只补缺失证据。
- 没有源码且输入为 JAR/WAR/class 时，必须实际调用 CLI 反编译，不要只描述“可以反编译”。
- 反编译产物必须进入工作目录的 `decompiled/`，不要覆盖源码目录。
- 反编译失败时记录命令、返回码、日志路径和未覆盖范围。

## 推荐脚本

```bash
python3 skills/java-audit/scripts/fetch_cfr.py --workspace <审计工作目录>
python3 skills/java-audit/scripts/decompile_with_cfr.py <目标文件> --workspace <审计工作目录>
```
