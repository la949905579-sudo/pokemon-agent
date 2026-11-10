/* arm64 ELF 包装：x86_64 aapt2 经 qemu 转译
 * 关键点（AGP daemon 协议）：
 *  - 文件名必须是 aapt2（AGP 校验 path.endsWith("aapt2")）
 *  - "version" 子命令：aapt2 输出到 stderr，AGP 从 stdout 读，需合并
 *  - 其他子命令：不能动 stderr（AGP 把 stderr EOF 当 daemon 崩溃）
 */
#include <unistd.h>
#include <string.h>
#include <stdio.h>

#define REAL_AAPT2 "/opt/aapt2-x86_64/aapt2"

int main(int argc, char** argv) {
    if (argc >= 2 && strcmp(argv[1], "version") == 0) {
        dup2(STDOUT_FILENO, STDERR_FILENO);
    }
    char* qargv[argc + 5];
    int n = 0;
    qargv[n++] = "qemu-x86_64-static";
    qargv[n++] = "-L";
    qargv[n++] = "/opt/amd64-root";
    qargv[n++] = REAL_AAPT2;
    for (int i = 1; i < argc; i++) qargv[n++] = argv[i];
    qargv[n] = 0;
    execv("/usr/bin/qemu-x86_64-static", qargv);
    perror("execv qemu-x86_64-static");
    return 127;
}
