cmake_minimum_required(VERSION 3.22)
project(saude_llm LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Official upstream at an immutable commit, fetched in GitHub Actions only.
# The GGUF weights themselves are never packaged into the APK.
set(LLAMA_CPP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/llama.cpp")
if(NOT EXISTS "${LLAMA_CPP_ROOT}/CMakeLists.txt")
    message(FATAL_ERROR "Pinned llama.cpp source missing; do not publish placeholder AI.")
endif()

add_subdirectory("${LLAMA_CPP_ROOT}" "${CMAKE_CURRENT_BINARY_DIR}/llama.cpp")
add_library(saude_llm SHARED saude_llm.cpp)
target_include_directories(saude_llm PRIVATE "${LLAMA_CPP_ROOT}/include")
target_link_libraries(saude_llm PRIVATE llama android log)
