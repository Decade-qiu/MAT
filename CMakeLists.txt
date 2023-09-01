cmake_minimum_required(VERSION 3.10) 
project(MAT)        

set(mode "release" CACHE INTERNAL "")

if(mode STREQUAL "debug")
    set(CMAKE_BUILD_TYPE Debug)
    add_definitions(--std=c++11 -g -mavx2 -O0 -fno-omit-frame-pointer -fno-optimize-sibling-calls)
else()
    set(CMAKE_BUILD_TYPE Release)   
    add_definitions(--std=c++11 -mavx2 -O3 -march=native -funroll-all-loops -flto)
endif()

message(STATUS "Build type: ${mode}!")

set(SRC_LIST src/MAT.cpp main.cpp)           
                 
add_executable(MAT ${SRC_LIST})                      
