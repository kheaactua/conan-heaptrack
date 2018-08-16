#!/usr/bin/env python
# -*- coding: future_fstrings -*-
# -*- coding: utf-8 -*-

import os
from conans import ConanFile, CMake, tools
from conans.tools import os_info, SystemPackageTool
from conans.errors import ConanException


class HeaptrackConan(ConanFile):
    name        = 'heaptrack'
    version     = '1.1.0'
    license     = ''
    url         = 'https://github.com/kheaactua/conan-heaptrack'
    description = 'A heap memory profiler for Linux'
    settings    = 'os', 'compiler', 'build_type', 'arch'
    generators  = 'cmake'
    requires    = (
        'kdiagram/2.6.1@ntc/stable',
        'boost/[>=1.58]@ntc/stable',
        'zlib/[>=1.2]@conan/stable',
        'bzip2/1.0.6@ntc/stable',
        'OpenSSL/1.0.2n@conan/stable', # overwrite Qt's OpenSSL. some sort of ABI and API incompatibility
        'qt/[>5.6]@ntc/stable',
    )

    def system_requirements(self):
        pack_names = None
        if tools.os_info.linux_distro == "ubuntu":
            pack_names = [
                'libdwarf-dev', 'libkf5coreaddons-dev', 'libkf5i18n-dev',
                'libkf5itemmodels-dev', 'libkf5threadweaver-dev',
                'libkf5configwidgets-dev', 'libkf5kiocore5',
                'libkf5kiowidgets5', 'kio-dev', 'libsparsehash-dev',
                'libqt5svg5-dev', 'extra-cmake-modules'
            ]

            if self.settings.arch == "x86":
                full_pack_names = []
                for pack_name in pack_names:
                    full_pack_names += [pack_name + ":i386"]
                pack_names = full_pack_names

        if pack_names:
            installer = tools.SystemPackageTool()
            try:
                installer.update() # Update the package database
                installer.install(" ".join(pack_names)) # Install the package
            except ConanException:
                self.output.warn('Could not run system updates to fetch system requirements.')

    def configure(self):
        self.options['qt'].openssl = 'yes'

    def source(self):
        self.run(f'git clone https://github.com/KDE/heaptrack.git {self.name}')
        self.run(f'cd {self.name} && git checkout v{self.version}')

    def build(self):
        cmake = CMake(self)

        # zlib (won't work on windows right now)
        cmake.definitions['ZLIB_INCLUDE_DIR:PATH'] = os.path.join(self.deps_cpp_info['zlib'].rootpath, self.deps_cpp_info['zlib'].includedirs[0])
        cmake.definitions['ZLIB_LIBRARY_RELEASE:FILEPATH'] = os.path.join(self.deps_cpp_info['zlib'].rootpath, 'lib', 'libz.so')

        # Boost
        cmake.definitions['BOOST_ROOT:PATH'] = self.deps_cpp_info['boost'].rootpath

        # Qt
        qt_deps = ['Core', 'Gui', 'Widgets']
        for p in qt_deps:
            cmake.definitions[f'Qt5{p}_DIR:PATH'] = os.path.join(self.deps_cpp_info['qt'].rootpath, 'lib', 'cmake', f'Qt5{p}')
        # cmake.definitions['QT_QMAKE_EXECUTABLE:PATH'] = os.path.join(self.deps_cpp_info['qt'].rootpath, 'bin', 'qmake')

        # KDiagram
        for p in self.deps_cpp_info['kdiagram'].resdirs:
            mod = os.path.basename(p)
            cmake.definitions[f'{mod}_DIR'] = os.path.join(self.deps_cpp_info['kdiagram'].rootpath, p)

        # Debug
        s = '\nCMake Definitions:\n'
        for k,v in cmake.definitions.items():
            s += ' - %s=%s\n'%(k, v)
        self.output.info(s)

        cmake.configure(source_folder=self.name)
        cmake.build()
        cmake.install()

    def deploy(self):
        if 'Linux' == self.settings.os:
            self.copy(
                pattern='*',
                dst=os.path.join(os.environ.get('HOME', os.path.join('/usr', 'local')), 'bin'),
                src=os.path.join(self.package_folder, 'bin')
            )

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
