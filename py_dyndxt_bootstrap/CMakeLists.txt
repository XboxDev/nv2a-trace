cmake_minimum_required(VERSION 3.18)
project(py_dnydxt_bootstrap)

set(CMAKE_VERBOSE_MAKEFILE TRUE)

set(CMAKE_CXX_STANDARD 17)

set(TARGET py_dnydxt_bootstrap)

add_library(
    ${TARGET}
    SHARED
    py_dll_loader.c
    ${DYNDXT_SOURCE_DIR}/dll_loader/dll_loader.c
    ${DYNDXT_SOURCE_DIR}/dll_loader/dll_loader.h
    ${DYNDXT_SOURCE_DIR}/test/third_party/nxdk/winapi/winnt.h
    ${DYNDXT_SOURCE_DIR}/test/third_party/nxdk/xboxkrnl/xboxdef.h
)
target_include_directories(
        ${TARGET}
        PRIVATE
        ${DYNDXT_SOURCE_DIR}/dll_loader
        ${DYNDXT_SOURCE_DIR}/test/third_party/nxdk
)

install(
        TARGETS
        ${TARGET}
        DESTINATION
        lib
)
install(
        FILES
        ${DYNDXT_SOURCE_DIR}/dll_loader/dll_loader.h
        DESTINATION
        include
)
