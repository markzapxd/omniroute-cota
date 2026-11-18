cmake_minimum_required(VERSION 3.21)
project(OmniQuotaBridge VERSION 0.1 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
find_package(Qt6 6.5 REQUIRED COMPONENTS Core Qml DBus)
qt_standard_project_setup()
qt_add_qml_module(omniquotabridge
    URI OmniQuota
    VERSION 1.0
    OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/OmniQuota"
    SOURCES bridge.h bridge.cpp
)
target_link_libraries(omniquotabridge PRIVATE Qt6::Core Qt6::Qml Qt6::DBus)
set_target_properties(omniquotabridge omniquotabridgeplugin PROPERTIES INSTALL_RPATH "$ORIGIN" INSTALL_RPATH_USE_LINK_PATH TRUE)
install(TARGETS omniquotabridge omniquotabridgeplugin LIBRARY DESTINATION OmniQuota)
install(FILES "${CMAKE_BINARY_DIR}/OmniQuota/qmldir" "${CMAKE_BINARY_DIR}/OmniQuota/omniquotabridge.qmltypes" DESTINATION OmniQuota)
