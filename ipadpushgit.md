iPad 使用 lg2 同步 GitHub 工作流

1. 环境信息

* 本地目录：~/Documents
* GitHub 仓库：https://github.com/LishuAndySun/STLsCollect
* 远程名称：origin
* 本地分支：master
* 远程分支：master
* Git 工具：lg2

2. 首次配置

以下配置只需执行一次。

配置远程仓库

如果尚未配置 origin：

lg2 remote add origin https://github.com/LishuAndySun/STLsCollect

如果已经配置，可以检查：

lg2 remote show -v

配置提交者信息

lg2 config user.name "LishuAndySun"
lg2 config user.email "你的GitHub邮箱"

将邮箱替换成自己的邮箱。以上命令配置的是当前仓库的提交者信息。

3. 日常编辑与同步流程

第一步：拉取最新文件

lg2 pull https://github.com/LishuAndySun/STLsCollect

第二步：编辑文件

在 Code App 中打开 ~/Documents，修改 Python、STL 或其他文件，并保存。

例如，运行 Python 脚本重新生成 STL：

python3 generate_cylinder.py

第三步：检查修改

lg2 status
lg2 diff

* status：查看文件状态。
* diff：查看已跟踪文件的未暂存修改。
* 新建文件可能显示为 Untracked files。

第四步：添加文件

添加指定文件：

lg2 add generate_cylinder.py tilted_cylinder.stl

或者添加当前目录下的所有修改：

lg2 add .

第五步：检查暂存状态

lg2 status
lg2 diff --cached

确认需要提交的文件已经暂存。

第六步：创建提交

lg2 commit -m "Update cylinder model"

提交信息可以根据实际修改内容更换，例如：

lg2 commit -m "Fix cylinder generation"

如果提示 No staged changes，说明没有可提交的暂存修改。检查文件是否保存、是否真的发生变化，以及是否执行了 lg2 add。

第七步：推送到 GitHub

lg2 push origin HEAD:refs/heads/master

此命令已在本环境中验证成功，用于将当前提交推送到远程 master 分支。

第八步：检查结果

lg2 status
lg2 log -1

然后打开 GitHub 仓库：

https://github.com/LishuAndySun/STLsCollect

刷新页面，切换到 master 分支，检查文件内容和提交记录。

4. 常见问题

4.1 remote 'origin' does not exist

添加远程仓库：

lg2 remote add origin https://github.com/LishuAndySun/STLsCollect

4.2 Error creating signature

配置提交者信息：

lg2 config user.name "LishuAndySun"
lg2 config user.email "你的GitHub邮箱"

4.3 No staged changes

重新检查：

lg2 status
lg2 diff
lg2 diff --cached

如果文件没有实际变化，就不需要创建新提交。

4.4 not a valid reference 'master'

使用已经验证成功的推送命令：

lg2 push origin HEAD:refs/heads/master

4.5 403

检查 GitHub Token 是否有效、是否具有目标仓库的写入权限，以及 Code App 是否使用了正确的认证信息。

不要将 Token 写入 README 或提交到 GitHub。

5. 日常快速操作

文件编辑完成后，通常只需要执行：

lg2 status
lg2 add .
lg2 commit -m "Update files"
lg2 push origin HEAD:refs/heads/master

如果没有实际修改，或者没有暂存任何文件，就不要强行创建提交。

注意： 应先保存文件，再添加、提交和推送。只有推送成功后，GitHub 上的内容才会更新。