cmake_minimum_required(VERSION 3.10) 
project(MAT)        

set(CMAKE_CXX_STANDARD 11)
set(mode "release" CACHE INTERNAL "")

if(mode STREQUAL "debug")
    set(CMAKE_BUILD_TYPE Debug)
    add_definitions(--std=c++11 -Wall -g -mavx2)
else()
    set(CMAKE_BUILD_TYPE Release)   
    add_definitions(--std=c++11 -mavx2 -O3)
endif()

message(STATUS "Build type: ${CMAKE_BUILD_TYPE}!")

set(SRC_LIST utils/murmurhash.cpp src/MAT.cpp main.cpp)           
                 
add_executable(MAT ${SRC_LIST})                      
