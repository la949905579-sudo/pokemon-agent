/* arm64 ELF 包装：x86_64 cmake 经 qemu 转译 */
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#define REAL "/opt/aapt2-x86_64/cmake.real"
int main(int argc, char** argv) {
    setenv("CMAKE_ROOT", "/root/android-sdk/cmake/3.22.1/share/cmake-3.22", 1);
    char* qargv[argc + 5];
    int n = 0;
    qargv[n++] = "qemu-x86_64-static";
    qargv[n++] = "-L";
    qargv[n++] = "/opt/amd64-root";
    qargv[n++] = REAL;
    for (int i = 1; i < argc; i++) qargv[n++] = argv[i];
    qargv[n] = 0;
    execv("/usr/bin/qemu-x86_64-static", qargv);
    perror("execv qemu");
    return 127;
}
