# Monkey 配置

> https://github.com/tsbxmw/monkey_tcloud

## Jenkins 配置

### Jobs 配置

#### 1, 新建 job ： ```monkey_autotest```

> 类型选择 Pipeline

> 然后选择参数化构建过程

| id | type | remark |
|----|----|----|
|PackageName | String type |运行的 android 包名 |
|DefaultAppActivity| String type | app 默认启动的 Activity |
|DeviceName| String type | 运行的设备的 device id (序列号)|
|RunTime| String type | 运行时间 单位分钟|
|AppDownloadUrl| String type | app 下载路径|
|PATH| String type | PATH|
|RunMod | String type | Monkey运行模式。 mix: 类monkey模式。70%控件解析随机点击，其余30%按原Monkey事件概率分布。支持android版本>=5  dfs: DFS深度遍历算法。支持android版本>=6 |
|MonkeyId| String type | tcloud 相关参数，定位 build id|
|TaskId| String type | tcloud 相关参数，定位 当前设备测试的 id |
|TcloudUrl| String type | tcloud 相关参数，api根 url |
|SystemDevice| Bool type | 是否是 系统设备，未使用 |
|InstallAppRequired| Bool type | 是否需要安装 App |
|LoginRequired| Bool type | 是否需要登录，未使用 |
|LoginUsername| String type | 登录用的用户名, 未使用|
|LoginPassword| String type | 登录用的密码，未使用|

> 
#### 2,  

### Nodes 配置


## 运行环境设置

### adb

### python 3.7

### git

## 运行