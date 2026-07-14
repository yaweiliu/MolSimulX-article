---
wp_post_id: 1338
id: T08
title: SSH密钥与config配置简明教程
wp_slug: ssh密钥与config配置简明教程
series: 在线资源
tier: 技术文档
status: reviewed
topic: SSH
paywall: free
---
> **系列标签：** `技术文档` · `SSH` · `集群` · `密钥`

连 Git、登集群、VSCode Remote SSH、传轨迹——都离不开 **SSH**。配好一次 **密钥** 和 **`~/.ssh/config` 别名**，以后就不用一遍遍敲 `user@很长一串域名.edu.cn`，`ssh`、`scp`、`rsync`、`git push` 都能用短名字。

本文专讲 SSH：**怎么生成密钥、公钥装到哪、`config` 怎么写、连不上怎么查**。Git 仓库换 SSH 地址见 [Git简明使用教程](T04-Git简明使用教程.md) 第五节；传文件见 [本地与集群文件传输](T09-本地与集群文件传输.md)；编辑器远程见 [VSCode与Cursor远程连接集群](T07-VSCode与Cursor远程连接集群.md)。

![ssh_key](../../images/articles/技术文档/T08-SSH密钥与config配置简明教程/web/T08-hero-ssh_key.webp)

---

## 一、SSH 与密钥认证是什么？

可以这么理解：**公钥是锁在门上的那把「挂锁」，私钥是你口袋里的钥匙**——本机留着私钥，服务器或 GitHub 上登记公钥，对上了就放行，不必每次输登录密码。

| 概念 | 含义 |
|------|------|
| **SSH** | 加密的远程登录协议；`ssh`、`scp`、`rsync` 都基于它 |
| **密钥对** | **私钥**在本机（`id_ed25519`）；**公钥**（`.pub`）装到服务器或 Git 平台 |
| **密码登录** | 每次敲账号密码；很多集群会限流或关掉，不适合当日常方式 |
| **密钥登录** | 私钥和服务器上的公钥配对即通过；可配合 `ssh-agent` 记住密钥口令 |

科研里，**同一套密钥**往往同时用于：课题组集群、GitHub / Gitee、跳板机。下文用 **ed25519**（短、快、够安全）；只有特别老的环境才考虑 rsa。

---

## 二、生成密钥对

在 Mac 终端、Ubuntu 或 **WSL** 里执行（Windows 建议走 WSL，见第八节）：

```bash
ssh-keygen -t ed25519 -C "你的邮箱或备注"
```

一路怎么选：

| 提示 | 建议 |
|------|------|
| 保存路径 | 直接回车 → 默认 `~/.ssh/id_ed25519` |
| passphrase（密钥口令） | 可设（更安全）或留空（省事）；设了口令可交给 `ssh-agent` 记一次 |

**集群和 Git 想分开两把钥匙**（可选）：

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_cluster -C "cluster"
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_github -C "github"
```

要复制公钥到网页或发给管理员时：

```bash
cat ~/.ssh/id_ed25519.pub
```

整行复制，从 `ssh-ed25519` 开头到备注结尾。

---

## 三、`~/.ssh` 目录与权限

密钥和配置都放在家目录下的 `~/.ssh/`：

```
~/.ssh/
├── id_ed25519          # 私钥（绝不上传、不进 Git）
├── id_ed25519.pub      # 公钥
├── authorized_keys     # 服务器上：谁可以登录我
├── config              # 本机：主机别名、用哪把钥匙
└── known_hosts         # 本机：信过的服务器指纹
```

权限太松时，SSH 会直接拒绝用密钥——这是安全机制，不是 bug：

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 600 ~/.ssh/config
chmod 644 ~/.ssh/id_ed25519.pub
```

> **Tips：** 私钥相当于银行卡密码。别丢网盘、别发群；换电脑应**重新生成**并在服务器上换公钥，别把旧私钥拷来拷去。

---

## 四、把公钥装到服务器（集群）

### 1. 自己能传（集群支持 `ssh-copy-id` 时）

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub your_username@cluster.university.edu.cn
```

或手动：先密码登录集群，把本机 `cat id_ed25519.pub` 的**整行**追加到远程 `~/.ssh/authorized_keys`（一行一把钥匙，别断行）。

### 2. 网页提交 / 找管理员

不少学校超算要在用户门户里粘贴公钥，或由管理员导入。按集群手册做完再测：

```bash
ssh your_username@cluster.university.edu.cn
```

能上去、且不用反复输登录密码（或只输密钥口令），就算成功。

### 3. Git 平台（GitHub / Gitee）

在网站 **Settings → SSH keys** 里添加公钥，然后：

```bash
ssh -T git@github.com
ssh -T git@gitee.com
```

看到欢迎信息即 OK。仓库远程地址和日常 `git push` 见 [Git简明使用教程](T04-Git简明使用教程.md) 第五节。

---

## 五、配置 `~/.ssh/config` 别名

`config` 就像 SSH 的**通讯录**：给集群起短名 `molcluster`，顺便写好用户名、用哪把私钥、怎么保活。

用编辑器打开或新建 `~/.ssh/config`：

```
Host molcluster
    HostName cluster.university.edu.cn
    User your_username
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

之后这些都用别名，不用记长域名：

```bash
ssh molcluster
scp local.dat molcluster:~/project/
rsync -avh ./ molcluster:~/project/
```

### 常用字段

| 字段 | 含义 |
|------|------|
| `Host` | 你起的短名；`ssh molcluster` 里的 `molcluster` |
| `HostName` | 真实地址 |
| `User` | 登录用户名（可省略，默认用本机用户名） |
| `IdentityFile` | 用哪把私钥 |
| `Port` | 非 22 端口时写，如 `Port 2222` |
| `ServerAliveInterval` | 每隔 N 秒发心跳，防空闲断线 |
| `ServerAliveCountMax` | 心跳失败几次后断开 |

### 多集群示例

```
Host molcluster
    HostName cluster.university.edu.cn
    User zhangsan
    IdentityFile ~/.ssh/id_ed25519_cluster

Host backup
    HostName backup.cluster.edu.cn
    User zhangsan
    IdentityFile ~/.ssh/id_ed25519_cluster
```

### 经跳板机（堡垒机）登录

校内集群常要先登跳板，再进计算网：

```
Host bastion
    HostName bastion.university.edu.cn
    User zhangsan
    IdentityFile ~/.ssh/id_ed25519

Host molcluster
    HostName compute.login.cluster.edu.cn
    User zhangsan
    IdentityFile ~/.ssh/id_ed25519_cluster
    ProxyJump bastion
```

以后只敲 `ssh molcluster`，SSH 会自动经 `bastion` 跳过去。

### GitHub 专用密钥（多把钥匙时）

```
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes
```

`IdentitiesOnly yes` 很重要——否则 SSH 可能把集群那把钥匙也拿去试 GitHub，认证会乱。

---

## 六、`ssh-agent` 与密钥口令

生成密钥时若设了 passphrase，每次 `ssh` / `git push` 都要输一遍。用 **ssh-agent** 可以在当前会话里记一次：

```bash
# macOS / Linux：多数环境已自动起 agent
ssh-add ~/.ssh/id_ed25519

# 看已加载了哪些钥匙
ssh-add -l
```

macOS 可写入钥匙串，重启后少输几次：

```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

WSL 里若提示 agent 没起来：`eval "$(ssh-agent -s)"`，再 `ssh-add`。

---

## 七、和 MolSimulX 工作流怎么串起来

配好 SSH 后，后面这些教程都直接受益：

| 场景 | 怎么用 |
|------|--------|
| **终端登集群** | `ssh molcluster`（别名来自第五节 `config`） |
| **传脚本、轨迹** | `scp` / `rsync` 同样写别名，见 [本地与集群文件传输](T09-本地与集群文件传输.md) |
| **VSCode / Cursor 远程** | Remote - SSH 会读 `config` 里的 `Host` 列表，见 [VSCode与Cursor远程连接集群](T07-VSCode与Cursor远程连接集群.md) |
| **Git 推代码** | `git@github.com:...` + 平台公钥，见 [Git简明使用教程](T04-Git简明使用教程.md) |
| **交 SLURM 作业** | SSH 只管登录和 `sbatch`；算力在计算节点，见 [集群与SLURM简明教程](T10-集群与SLURM简明教程.md) |

---

## 八、Windows 与 WSL

| 环境 | `config` 和密钥放哪 |
|------|---------------------|
| **WSL（推荐）** | `~/.ssh/`，和 Linux 一模一样 |
| **Windows 自带 OpenSSH** | `C:\Users\你的用户名\.ssh\config` |
| **Git Bash** | 一般在用户主目录的 `~/.ssh/` |

分子模拟用户建议在 **WSL 里统一配 SSH**（[WSL2安装与配置](T02-WSL2安装与配置.md)），和集群环境一致。若 Windows 版 VSCode 用本机 `config`、WSL 里又有一套，容易改 A 用 B——**选一条路坚持**即可。

---

## 九、常见问题

### 1. `Permission denied (publickey)`

- 集群 / GitHub 上是不是贴了**这把**公钥？`cat ~/.ssh/id_ed25519.pub` 核对  
- `config` 里 `IdentityFile` 是否指向实际私钥  
- 私钥权限：`chmod 600 ~/.ssh/id_ed25519`  
- 仍不行：`ssh -v molcluster` 看日志里试了哪几把钥匙

### 2. `WARNING: UNPROTECTED PRIVATE KEY FILE`

私钥或 `config` 权限太宽，按第三节跑一遍 `chmod`。

### 3. 连上一会儿就断

在对应 `Host` 段加上 `ServerAliveInterval 60` 和 `ServerAliveCountMax 3`。

### 4. 改了 `config` 没反应

确认改的是**当前终端 / 编辑器正在用的**那份——WSL 的 `~/.ssh` 和 Windows 的 `C:\Users\...\.ssh` 不是同一个。

### 5. `Host key verification failed`

服务器重装或换 IP 后指纹变了。执行 `ssh-keygen -R cluster.university.edu.cn`（或按提示删 `known_hosts` 里对应行）再连。

### 6. 多把密钥时总认证错主机

每个 `Host` 写清 `IdentityFile`；连 GitHub 时加 `IdentitiesOnly yes`。

---

## 十、小结

1. 用 **ed25519** 生成密钥对；**私钥留本机**，公钥装到集群或 Git 平台。  
2. **`~/.ssh` 权限**（目录 `700`、私钥和 config `600`）不过关，SSH 会直接拒你。  
3. **`~/.ssh/config`** 起别名、指定 `IdentityFile`、保活、`ProxyJump`——写一次，后面 `ssh` / `scp` / Remote SSH 都省事。  
4. Windows 用户优先在 **WSL** 配，和 [本地与集群文件传输](T09-本地与集群文件传输.md)、[VSCode与Cursor远程连接集群](T07-VSCode与Cursor远程连接集群.md) 同一套环境。

`Permission denied` 或连不上时，把 `ssh -v molcluster` 的**完整输出**复制去搜，往往能快速对上原因。

---

## 学习路径

**前置阅读：**

- [Linux终端与Shell简明教程](T03-Linux终端与Shell简明教程.md)
- Windows：[WSL2安装与配置](T02-WSL2安装与配置.md)

**下一步：**

- [Git简明使用教程](T04-Git简明使用教程.md) —— 用 SSH 地址关联远程仓库
- [本地与集群文件传输](T09-本地与集群文件传输.md) —— `scp` / `rsync` 使用别名传文件
- [VSCode与Cursor远程连接集群](T07-VSCode与Cursor远程连接集群.md) —— Remote - SSH 连集群
- [集群与SLURM简明教程](T10-集群与SLURM简明教程.md) —— 登录后提交作业
