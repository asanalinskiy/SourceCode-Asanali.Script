// sysinfo.c
#include <stdio.h>
#include <stdlib.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif

// Функция для получения имени текущего пользователя компьютера
const char* get_computer_user() {
    const char* user = getenv("USERNAME"); // Для Windows
    if (!user) {
        user = getenv("USER"); // Для Linux/Mac
    }
    return user ? user : "Unknown";
}