cmake_minimum_required(VERSION 3.21)
project(LegacyWheelHubDInputProxy LANGUAGES CXX)

if(NOT WIN32 OR NOT MSVC)
    message(FATAL_ERROR "The LWH dinput8 proxy must be built with MSVC on Windows.")
endif()

add_library(dinput8 SHARED
    src/dllmain.cpp
    src/dinput8.def
)

target_compile_features(dinput8 PRIVATE cxx_std_17)
target_compile_definitions(dinput8 PRIVATE
    WIN32_LEAN_AND_MEAN
    NOMINMAX
    DIRECTINPUT_VERSION=0x0800
)
target_include_directories(dinput8 PRIVATE src)
target_link_libraries(dinput8 PRIVATE dxguid user32 advapi32)
set_target_properties(dinput8 PROPERTIES
    OUTPUT_NAME "dinput8"
    PREFIX ""
    CXX_EXTENSIONS OFF
)
