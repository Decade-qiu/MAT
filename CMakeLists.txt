cmake_minimum_required(VERSION 3.10) 
project(MAT)        

add_definitions("-Wall -g")
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_BUILD_TYPE Debug)   

set(SRC_LIST utils/murmurhash.cpp src/MAT.cpp main.cpp)           
                 
add_executable(MAT ${SRC_LIST})                      
