#!/usr/bin/env python3

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Mapping, Sequence, Tuple

from deps import COPY_FIXES, DEPENDENCIES


class Triplet(object):
    def __init__(self, arch: str, system: str, linkage: str):
        self.arch = arch
        self.system = system
        self.linkage = linkage

    @classmethod
    def from_string(cls, triplet_string: str) -> 'Triplet':
        triplet_list = triplet_string.split('-')
        if len(triplet_list) == 2:
            triplet_list.append('dynamic')
        return cls(arch=triplet_list[0], system=triplet_list[1], linkage=triplet_list[2])

    def __hash__(self) -> int:
        return hash(self.arch) ^ hash(self.system) ^ hash(self.linkage)

    def __eq__(self, other: object) -> bool:
        if type(self) != type(other):
            return False
        return self.arch == other.arch and self.system == other.arch and self.linkage == other.linkage

    def __str__(self) -> str:
        format_str = '{arch}-{system}-{linkage}' if self.linkage == 'static' else '{arch}-{system}'
        return format_str.format(arch=self.arch, system=self.system, linkage=self.linkage)


X86_WINDOWS_DYNAMIC = Triplet(arch='x86', system='windows', linkage='dynamic')
X86_WINDOWS_STATIC = Triplet(arch='x86', system='windows', linkage='static')

X64_WINDOWS_DYNAMIC = Triplet(arch='x64', system='windows', linkage='dynamic')
X64_WINDOWS_STATIC = Triplet(arch='x64', system='windows', linkage='static')

TRIPLETS = (
    X86_WINDOWS_DYNAMIC,
    X64_WINDOWS_DYNAMIC,
)


class VcPkg(object):
    def __init__(self, output_path: Path, vcpkg_path: Path):
        self._output = output_path
        self._vcpkg = vcpkg_path

    @property
    def output_path(self) -> Path:
        return self._output

    @property
    def vcpkg_path(self) -> Path:
        return self._vcpkg

    def get_install_path(self, triplet: Triplet) -> Path:
        return self.vcpkg_path / 'installed' / str(triplet)

    @property
    def exe_path(self) -> Path:
        return self.vcpkg_path / 'vcpkg.exe'

    def build_vcpkg(self) -> None:
        if not self.vcpkg_path.exists():
            print('vcpkg: cloning...')
            subprocess.run([
                'git', 'clone', '--depth', '1', '--', 'https://github.com/Microsoft/vcpkg', str(self.vcpkg_path)
            ], cwd=self.output_path, check=True)
        else:
            print('vcpkg: directory exists, skipping git clone.')
        if not self.exe_path.exists():
            print('vcpkg: running bootstrap script')
            subprocess.run([str(self.vcpkg_path / 'bootstrap-vcpkg.bat')],
                           cwd=self.vcpkg_path, check=True)
        else:
            print('vcpkg: vcpkg executable exists, skipping bootstrap')
            print('vcpkg: try update?')

    def update_vcpkg(self) -> None:
        self.build_vcpkg()
        print('vcpkg: updating to master...')
        cmds = [
            ['git', 'fetch', 'origin'],
            ['git', 'reset', '--hard', 'HEAD'],
            ['git', 'checkout', 'master'],
            ['git', 'merge', 'origin/master'],
            [str(self.vcpkg_path / 'bootstrap-vcpkg.bat')],
        ]
        for cmd in cmds:
            subprocess.run(cmd, cwd=self.vcpkg_path, check=True)

    def list_installed(self) -> Mapping[str, Sequence[Tuple[Triplet, str]]]:
        output = subprocess.run([str(self.exe_path), 'list'],
                                cwd=self.vcpkg_path, check=True, stdout=subprocess.PIPE).stdout
        output = output.decode()
        name_variations = dict()
        for line in output.split('\r\n'):
            try:
                [name_triplet, version, _] = line.split(maxsplit=2)
                [name, triplet_string] = name_triplet.split(':')
                triplet = Triplet.from_string(triplet_string)
                name_variations.setdefault(name, set()).add((triplet, version, ))
            except ValueError:
                pass
        return name_variations

    def install_library(self, lib: str, triplet: Triplet) -> None:
        print('vcpkg: installing', lib)
        subprocess.run([str(self.exe_path), 'install', lib, '--triplet', str(triplet)],
                       cwd=self.vcpkg_path, check=True)

    def remove_library(self, lib: str, triplet: Triplet) -> None:
        print('vcpkg: removing', lib)
        subprocess.run([str(self.exe_path), 'remove', lib, '--triplet', str(triplet)],
                       cwd=self.vcpkg_path, check=True)


class CommaSplitter(argparse.Action):
    def __init__(self, *args, **kwargs):
        self._choices = []
        if 'choices' in kwargs:
            self._choices = kwargs['choices']
            del kwargs['choices']
        argparse.Action.__init__(self, *args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if self._choices:
            values = values.split(',')
            for value in values:
                if value not in self._choices:
                    parser.error('{} is not in {}.'.format(value, ','.join(self._choices)))
        setattr(namespace, self.dest, values)


def main() -> None:
    default_output_path = Path('.').absolute()
    try:
        default_vcpkg_path = Path(shutil.which('vcpkg')).parent
    except TypeError:
        default_vcpkg_path = Path('.').absolute() / 'vcpkg'
    default_arch = ['x86', 'x64']
    default_system = ['windows']
    default_linkage = ['dynamic', 'static']

    parser = argparse.ArgumentParser()
    folder_group = parser.add_argument_group(title='Folders')
    folder_group.add_argument('-t', dest='vcpkg_path', default=default_vcpkg_path, type=Path,
                              help='VcPkg directory. Default is "{}"'.format(default_vcpkg_path))
    folder_group.add_argument('-o', dest='output_path', default=default_output_path, type=Path,
                              help='Output directory. Default is "{}"'.format(default_output_path))
    folder_group.add_argument('-w', dest='what', nargs=1, default=[], action=CommaSplitter,
                              help='Dependencies. Default is to build all dependencies.')

    triplet_group = parser.add_argument_group(title='Triplet')
    triplet_group.add_argument('-a', dest='arch', default=default_arch,
                               choices=['arm', 'x64', 'x86'], action=CommaSplitter,
                               help='Architecture. Default is "{}"'.format(','.join(default_arch)))
    triplet_group.add_argument('-s', dest='system', default=default_system,
                               choices=['windows', 'uwp'], action=CommaSplitter,
                               help='System name. Default is "{}"'.format(','.join(default_system)))
    triplet_group.add_argument('-l', dest='linkage',default=default_linkage,
                               choices=['dynamic', 'static'], action=CommaSplitter,
                               help='Linkage. Default is "{}"'.format(','.join(default_linkage)))

    subparser = parser.add_subparsers(help='sub-commandos')
    vcpkg_parser = subparser.add_parser('vcpkg', help='Administrate vcpkg')
    vcpkg_parser.add_argument('vcpkg_action', metavar='ACTION', default=None,
                              choices=['install', 'update', 'list_installed'], help='Action to perform.')

    dep_parser = subparser.add_parser('deps', help='Dependency commands')
    dep_parser.add_argument('deps_action', metavar='ACTION', default=None,
                            choices=['build', 'rmbuild', 'copy', 'rmcopy'], help='Action to perform')

    options = parser.parse_args()

    vcpkg = VcPkg(output_path=options.output_path, vcpkg_path=options.vcpkg_path)

    if not options.what:
        options.what = DEPENDENCIES

    triplets = []
    for arch in options.arch:
        for system in options.system:
            for linkage in options.linkage:
                triplets.append(Triplet(arch=arch, system=system, linkage=linkage))
    print('triplets: {}'.format([str(t) for t in triplets]))

    if 'vcpkg_action' in options:
        if options.vcpkg_action == 'install':
            vcpkg.build_vcpkg()
        elif options.vcpkg_action == 'update':
            vcpkg.update_vcpkg()
        elif options.vcpkg_action == 'list_installed':
            installed = vcpkg.list_installed()
            for lib in installed:
                print('- {}'.format(lib))
        else:
            parser.error('Illegal VcPkg action.')
    elif 'deps_action' in options:
        if options.deps_action == 'build':
            for triplet in triplets:
                for dep in options.what:
                    print('build: {}'.format(dep))
                    vcpkg.install_library(dep, triplet)
        elif options.deps_action == 'rmbuild':
            for triplet in triplets:
                for dep in options.what:
                    vcpkg.remove_library(dep, triplet)
        elif options.deps_action == 'copy':
            for triplet in triplets:
                packages_path = vcpkg.vcpkg_path / 'packages'
                dst = options.output_path / str(triplet)
                dst.mkdir(exist_ok=True)
                print('copy: src={src} dst={dst}'.format(src=packages_path, dst=dst))
                for dep in options.what:
                    import distutils.dir_util
                    dep_pack_path = packages_path / '{}_{}'.format(dep, str(triplet))
                    distutils.dir_util.copy_tree(str(dep_pack_path), str(dst))
                    try:
                        COPY_FIXES[dep](dst)
                        print('fix for "{}" applied'.format(dep))
                    except KeyError:
                        pass
                (dst / 'CONTROL').unlink()
                (dst / 'BUILD_INFO').unlink()
        elif options.deps_action == 'rmcopy':
            for triplet in triplets:
                dst = options.output_path / str(triplet)
                print('remove: {}'.format(dst))
                shutil.rmtree(str(dst), ignore_errors=True)
        else:
            parser.error('Illegal dependency action.')
    else:
        parser.error('Need action to perform')


if __name__ == '__main__':
    main()
